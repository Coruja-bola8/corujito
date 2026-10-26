"""
Blueprint de importacao CSV.
Cada rota recebe um arquivo CSV (separador ; ou ,), valida as colunas
esperadas, importa os registros validos e devolve um relatorio de resultado.
Somente administradores podem importar.
"""

import io
import csv
import re
from datetime import datetime, date

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from models import (
    db, Militar, Cargo, VerbaOperacional, VerbaAdm,
    TurmaEstagio, ParticipanteEstagio, Parceiro,
    CATEGORIAS_POSTO, FONTES_VERBA_ADM,
)
from auth import admin_required

importacao_bp = Blueprint("importacao", __name__, url_prefix="/importacao")


# ── utilidades ────────────────────────────────────────────────────────────────

def _detectar_separador(texto):
    """Tenta detectar ; ou , como separador."""
    n_ponto_virgula = texto.count(";")
    n_virgula = texto.count(",")
    return ";" if n_ponto_virgula >= n_virgula else ","


def _ler_csv(file_storage):
    """Lê o FileStorage e devolve lista de dicts (linhas) e lista de erros."""
    raw = file_storage.read()
    # Remove BOM UTF-8 se presente
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    texto = raw.decode("utf-8-sig", errors="replace")
    sep = _detectar_separador(texto)
    reader = csv.DictReader(io.StringIO(texto), delimiter=sep)
    linhas = []
    for row in reader:
        # Ignora linhas completamente vazias
        valores = [v.strip() for v in row.values() if v and v.strip()]
        if valores:
            linhas.append({k.strip(): v.strip() if v else "" for k, v in row.items()})
    return linhas, sep


def _parse_data(valor):
    """Tenta vários formatos de data brasileiros."""
    if not valor:
        return None
    valor = valor.strip().replace("\xa0", "")
    formatos = [
        "%d/%m/%Y", "%d/%m/%y",
        "%d/%b/%y", "%d/%b/%Y",
        "%Y-%m-%d",
        "%d-%m-%Y", "%d-%m-%y",
    ]
    meses_pt = {
        "jan": "01", "fev": "02", "mar": "03", "abr": "04",
        "mai": "05", "jun": "06", "jul": "07", "ago": "08",
        "set": "09", "out": "10", "nov": "11", "dez": "12",
    }
    for abbr, num in meses_pt.items():
        valor = re.sub(rf"/{abbr}/", f"/{num}/", valor, flags=re.IGNORECASE)
    for fmt in formatos:
        try:
            return datetime.strptime(valor, fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def _parse_valor(texto):
    """Converte 'R$ 4.320,00' ou '4320.00' para float."""
    if not texto:
        return 0.0
    limpo = re.sub(r"[R$\s]", "", texto).replace(".", "").replace(",", ".")
    try:
        return float(limpo)
    except ValueError:
        return 0.0


def _col(row, *nomes):
    """Tenta pegar a coluna pelo primeiro nome que existir (case-insensitive)."""
    row_lower = {k.lower(): v for k, v in row.items()}
    for n in nomes:
        v = row_lower.get(n.lower(), "")
        if v:
            return v
    return ""


def _relatorio_flash(importados, erros, nome_modulo):
    if importados:
        flash(f"{importados} registro(s) de {nome_modulo} importados com sucesso.", "sucesso")
    if erros:
        for e in erros[:10]:
            flash(e, "erro")
        if len(erros) > 10:
            flash(f"... e mais {len(erros) - 10} erros omitidos.", "erro")


# ── index ─────────────────────────────────────────────────────────────────────

@importacao_bp.route("/")
@login_required
@admin_required
def index():
    return render_template("importacao/index.html")


# ── pessoal ───────────────────────────────────────────────────────────────────

@importacao_bp.route("/pessoal", methods=["GET", "POST"])
@login_required
@admin_required
def pessoal():
    """
    Colunas esperadas (baseadas no 3db_pessoal.csv):
    ORD;AGENTE;POSTO-GRAD;ARMA;Situacao;Circulo;ANO FORMACAO;NOME;IDT;
    DT_PRACA;CPF;DT_ULT_PROM;DT_OM;DT_SEDE;...
    """
    if request.method == "GET":
        return render_template("importacao/pessoal.html")

    arquivo = request.files.get("arquivo")
    if not arquivo or not arquivo.filename:
        flash("Selecione um arquivo CSV.", "erro")
        return redirect(url_for("importacao.pessoal"))

    linhas, _ = _ler_csv(arquivo)
    importados = 0
    erros = []

    for i, row in enumerate(linhas, start=2):
        # Nome: prefere coluna NOME, aceita AGENTE como fallback
        nome = _col(row, "NOME", "nome") or _col(row, "AGENTE", "agente")
        nome = nome.strip()
        if not nome:
            erros.append(f"Linha {i}: sem nome — ignorada.")
            continue

        posto = _col(row, "POSTO-GRAD", "posto_grad", "POSTO_GRAD", "posto-grad")
        if not posto:
            erros.append(f"Linha {i} ({nome}): sem posto/graduação — ignorada.")
            continue

        # Verifica duplicata por nome + posto
        existente = Militar.query.filter(
            db.func.lower(Militar.nome) == nome.lower()
        ).first()
        if existente:
            erros.append(f"Linha {i}: militar '{nome}' já cadastrado — ignorado.")
            continue

        m = Militar()
        m.nome = nome
        m.posto_grad = posto
        m.cpf = _col(row, "CPF", "cpf")
        m.idt = _col(row, "IDT", "idt")
        m.arma = _col(row, "ARMA", "arma")

        sit = _col(row, "Situação", "situacao", "Situacao", "SITUACAO").lower()
        m.situacao = sit.capitalize() if sit else None

        circulo_raw = _col(row, "Circulo", "CIRCULO", "círculo").lower()
        # Mapeia os valores curtos do CSV para os nomes completos
        mapa_circulo = {
            "oficial sup": "Oficial Superior",
            "oficial superior": "Oficial Superior",
            "intermediario": "Oficial Intermediário",
            "oficial intermediario": "Oficial Intermediário",
            "oficial subalt": "Oficial Subalterno",
            "oficial subalterno": "Oficial Subalterno",
            "subten": "Subtenente",
            "subtenente": "Subtenente",
            "1 sgt": "1º Sargento",
            "1o sgt": "1º Sargento",
            "2 sgt": "2º Sargento",
            "2o sgt": "2º Sargento",
            "3 sgt": "3º Sargento",
            "3o sgt": "3º Sargento",
            "n_aperfeicoado": "Oficial Subalterno",
            "reserva": None,
        }
        m.circulo = mapa_circulo.get(circulo_raw, circulo_raw.title() if circulo_raw else None)

        # categoria_posto (para contagem de claros)
        mapa_cat = {
            "oficial sup": "Oficial Superior",
            "oficial superior": "Oficial Superior",
            "intermediario": "Oficial Intermediário",
            "oficial intermediario": "Oficial Intermediário",
            "oficial subalt": "Oficial Subalterno",
            "oficial subalterno": "Oficial Subalterno",
            "n_aperfeicoado": "Oficial Subalterno",
            "subten": "Subtenente",
            "subtenente": "Subtenente",
            "1 sgt": "1º Sargento",
            "2 sgt": "2º Sargento",
            "3 sgt": "3º Sargento",
        }
        m.categoria_posto = mapa_cat.get(circulo_raw)

        ano_form = _col(row, "ANO FORMACAO", "ano_formacao", "ANO_FORMACAO")
        try:
            m.ano_formacao = int(ano_form) if ano_form else None
        except ValueError:
            m.ano_formacao = None

        m.dt_praca = _parse_data(_col(row, "DT_PRACA", "DT PRACA", "dt_praca"))
        m.dt_ult_promocao = _parse_data(_col(row, "DT_ULT_PROM", "DT ULT PROM", "dt_ult_prom"))
        m.dt_om = _parse_data(_col(row, "DT_OM", "DT OM", "dt_om"))
        m.dt_sede = _parse_data(_col(row, "DT_SEDE", "DT SEDE", "dt_sede"))

        db.session.add(m)
        importados += 1

    db.session.commit()
    _relatorio_flash(importados, erros, "Pessoal")
    return redirect(url_for("pessoal.listar"))


# ── cargos (QCP) ──────────────────────────────────────────────────────────────

@importacao_bp.route("/cargos", methods=["GET", "POST"])
@login_required
@admin_required
def cargos():
    """
    Colunas: cargo;ocupante;posto_ocupante;qc;previsto;Cod_Previsto;Hab;conf_habilitacao
    """
    if request.method == "GET":
        return render_template("importacao/cargos.html")

    arquivo = request.files.get("arquivo")
    if not arquivo or not arquivo.filename:
        flash("Selecione um arquivo CSV.", "erro")
        return redirect(url_for("importacao.cargos"))

    linhas, _ = _ler_csv(arquivo)
    importados = 0
    erros = []

    # Cache de militares para lookup rápido
    militares = {m.nome.lower(): m for m in Militar.query.all()}

    mapa_cat_qcp = {
        "Ten Cel": "Oficial Superior",
        "Cel": "Oficial Superior",
        "Gen": "Oficial Superior",
        "Maj": "Oficial Intermediário",
        "Cap": "Oficial Subalterno",
        "1T": "Oficial Subalterno",
        "2T": "Oficial Subalterno",
        "Sub Ten": "Subtenente",
        "1 Sgt": "1º Sargento",
        "2 Sgt": "2º Sargento",
        "3 Sgt": "3º Sargento",
    }

    for i, row in enumerate(linhas, start=2):
        nome_cargo = _col(row, "cargo", "CARGO")
        if not nome_cargo:
            continue

        previsto_raw = _col(row, "qc", "previsto", "QC", "PREVISTO")
        categoria = None
        for posto_key, cat_val in mapa_cat_qcp.items():
            if posto_key.lower() in previsto_raw.lower():
                categoria = cat_val
                break
        if not categoria:
            categoria = "Oficial Subalterno"

        # Tenta vincular ocupante
        nome_ocup = _col(row, "ocupante", "OCUPANTE").strip()
        ocupante_id = None
        if nome_ocup:
            m = militares.get(nome_ocup.lower())
            if m:
                ocupante_id = m.id
            else:
                erros.append(f"Linha {i}: ocupante '{nome_ocup}' não encontrado em Pessoal — cargo criado sem vínculo.")

        hab = _col(row, "Hab", "hab", "HAB", "habilitacao")
        conf = _col(row, "conf_habilitacao", "CONF_HABILITACAO", "conf habilitacao")
        hab_confirmada = "ok" in conf.lower() or conf.strip() == "1"

        c = Cargo(
            cargo=nome_cargo,
            categoria_posto_previsto=categoria,
            habilitacao_exigida=hab or None,
            habilitacao_confirmada=hab_confirmada,
            ocupante_id=ocupante_id,
        )
        db.session.add(c)
        importados += 1

    db.session.commit()
    _relatorio_flash(importados, erros, "Cargos (QCP)")
    return redirect(url_for("cargos.listar"))


# ── verba operacional ─────────────────────────────────────────────────────────

@importacao_bp.route("/verba-operacional", methods=["GET", "POST"])
@login_required
@admin_required
def verba_operacional():
    """
    Colunas (baseadas no 9db_verba2.csv):
    dt_deposito;VL_RECEBIDO;AG_SUP;operacao;prazo_pc;tipo;nr_ordem;dt_envio;nr_rastreio;recebido
    """
    if request.method == "GET":
        return render_template("importacao/verba_operacional.html")

    arquivo = request.files.get("arquivo")
    if not arquivo or not arquivo.filename:
        flash("Selecione um arquivo CSV.", "erro")
        return redirect(url_for("importacao.verba_operacional"))

    linhas, _ = _ler_csv(arquivo)
    importados = 0
    erros = []

    for i, row in enumerate(linhas, start=2):
        valor_raw = _col(row, "VL_RECEBIDO", "vl_recebido", "valor", "VALOR")
        if not valor_raw:
            continue
        valor = _parse_valor(valor_raw)
        if valor == 0:
            continue

        dt = _parse_data(_col(row, "dt_deposito", "DT_DEPOSITO", "data_recebimento", "DATA"))
        if not dt:
            erros.append(f"Linha {i}: data inválida ('{_col(row, 'dt_deposito', 'data_recebimento')}') — importado sem data.")

        operacao = _col(row, "operacao", "OPERACAO", "origem")
        semestre = ""
        match = re.search(r"(\d+/\d{4})", operacao)
        if match:
            semestre = match.group(1)

        status_raw = _col(row, "recebido", "RECEBIDO", "status").lower()
        if "recebido" in status_raw:
            status = "Recebida"
        elif "enviado" in status_raw:
            status = "A prestar conta"
        elif "processamento" in status_raw:
            status = "A prestar conta"
        else:
            status = "Recebida"

        r = VerbaOperacional(
            data_recebimento=dt or date.today(),
            semestre_referencia=semestre,
            valor=valor,
            origem=operacao,
            quem_recebeu=_col(row, "AG_SUP", "ag_sup", "quem_recebeu"),
            tipo_verba=_col(row, "tipo", "TIPO", "tipo_verba"),
            recibo_remessa=_col(row, "nr_rastreio", "NR_RASTREIO", "recibo_remessa"),
            status=status,
        )
        db.session.add(r)
        importados += 1

    db.session.commit()
    _relatorio_flash(importados, erros, "Verba Operacional")
    return redirect(url_for("verba_operacional.listar"))


# ── verba administrativa ──────────────────────────────────────────────────────

@importacao_bp.route("/verba-adm", methods=["GET", "POST"])
@login_required
@admin_required
def verba_adm():
    """
    Colunas (baseadas no 4verba_adm.csv):
    UG;NC;ND;DATA;prazo_empenho;dias_tela;valor;empenhado_em;liquidado;status
    O CSV não tem coluna 'fonte' — o usuário seleciona a fonte no formulário.
    """
    if request.method == "GET":
        return render_template("importacao/verba_adm.html", fontes=FONTES_VERBA_ADM)

    arquivo = request.files.get("arquivo")
    fonte = request.form.get("fonte", "Verba do CIE")
    if not arquivo or not arquivo.filename:
        flash("Selecione um arquivo CSV.", "erro")
        return redirect(url_for("importacao.verba_adm"))

    linhas, _ = _ler_csv(arquivo)
    importados = 0
    erros = []

    for i, row in enumerate(linhas, start=2):
        nc = _col(row, "NC", "nc")
        if not nc:
            continue

        status_raw = _col(row, "status", "STATUS").lower()
        if "aguardando" in status_raw or "aguard" in status_raw:
            status = "Aguardando"
        elif "empenhado" in status_raw:
            status = "Empenhado"
        elif "liquidado" in status_raw or "liquid" in status_raw:
            status = "Liquidado"
        elif "atrasado" in status_raw:
            status = "Atrasado"
        else:
            status = "Aguardando"

        r = VerbaAdm(
            fonte=fonte,
            ug=_col(row, "UG", "ug"),
            nc=nc,
            nd=_col(row, "ND", "nd"),
            data=_parse_data(_col(row, "DATA", "data")),
            prazo_empenho=_parse_data(_col(row, "prazo_empenho", "PRAZO_EMPENHO")),
            valor=_parse_valor(_col(row, "valor", "VALOR", " valor ")),
            empenhado_em=_parse_data(_col(row, "empenhado_em", "EMPENHADO_EM")),
            liquidado_em=_parse_data(_col(row, "liquidado", "liquidado_em", "LIQUIDADO")),
            status=status,
        )
        db.session.add(r)
        importados += 1

    db.session.commit()
    _relatorio_flash(importados, erros, "Verba Administrativa")
    return redirect(url_for("verba_adm.listar"))


# ── estágios ──────────────────────────────────────────────────────────────────

@importacao_bp.route("/estagios", methods=["GET", "POST"])
@login_required
@admin_required
def estagios():
    """
    Colunas (5estagios_externos.csv):
    doc_ref;dt_doc_ref;estagio_turno;dt_ini_ead;dt_term_ead;
    dt_ini_presencial;dt_term_presencial;prazo_indicacao;encaminhamento
    """
    if request.method == "GET":
        return render_template("importacao/estagios.html")

    arquivo = request.files.get("arquivo")
    if not arquivo or not arquivo.filename:
        flash("Selecione um arquivo CSV.", "erro")
        return redirect(url_for("importacao.estagios"))

    linhas, _ = _ler_csv(arquivo)
    importados = 0
    erros = []

    for i, row in enumerate(linhas, start=2):
        nome_turma = _col(row, "estagio_turno", "ESTAGIO_TURNO", "estagio", "ESTAGIO")
        if not nome_turma:
            continue

        t = TurmaEstagio(
            estagio_turno=nome_turma,
            doc_ref=_col(row, "doc_ref", "DOC_REF"),
            dt_doc_ref=_parse_data(_col(row, "dt_doc_ref", "DT_DOC_REF")),
            dt_inicio_ead=_parse_data(_col(row, "dt_ini_ead", "DT_INI_EAD", "dt_inicio_ead")),
            dt_fim_ead=_parse_data(_col(row, "dt_term_ead", "DT_TERM_EAD", "dt_fim_ead")),
            dt_inicio_presencial=_parse_data(_col(row, "dt_ini_presencial", "DT_INI_PRESENCIAL", "dt_inicio_presencial")),
            dt_fim_presencial=_parse_data(_col(row, "dt_term_presencial", "DT_TERM_PRESENCIAL", "dt_fim_presencial")),
            prazo_indicacao=_parse_data(_col(row, "prazo_indicacao", "PRAZO_INDICACAO")),
            encaminhamento=_col(row, "encaminhamento", "ENCAMINHAMENTO"),
        )
        db.session.add(t)
        importados += 1

    db.session.commit()
    _relatorio_flash(importados, erros, "Estágios")
    return redirect(url_for("estagios.listar_turmas"))


# ── participantes de estágio (EEIOC) ─────────────────────────────────────────

@importacao_bp.route("/participantes", methods=["GET", "POST"])
@login_required
@admin_required
def participantes():
    """
    Colunas (6eeioc.csv):
    estagio;doc_ref;prazo_indicacao;nome_voluntario;empresa_voluntario;
    indicado_por;encaminhamento;doc_remessa_pedido;status_participacao
    """
    if request.method == "GET":
        turmas = TurmaEstagio.query.order_by(TurmaEstagio.estagio_turno).all()
        return render_template("importacao/participantes.html", turmas=turmas)

    arquivo = request.files.get("arquivo")
    if not arquivo or not arquivo.filename:
        flash("Selecione um arquivo CSV.", "erro")
        return redirect(url_for("importacao.participantes"))

    linhas, _ = _ler_csv(arquivo)
    importados = 0
    erros = []

    # Cache de turmas
    turmas_cache = {}
    for t in TurmaEstagio.query.all():
        turmas_cache[t.estagio_turno.lower()] = t
        turmas_cache[t.doc_ref.lower() if t.doc_ref else ""] = t

    for i, row in enumerate(linhas, start=2):
        nome_vol = _col(row, "nome_voluntario", "NOME_VOLUNTARIO", "nome")
        if not nome_vol:
            continue

        # Encontra a turma pelo nome do estágio ou doc_ref
        nome_turma = _col(row, "estagio", "ESTAGIO", "estagio_turno")
        doc_ref = _col(row, "doc_ref", "DOC_REF")
        turma = turmas_cache.get(nome_turma.lower()) or turmas_cache.get(doc_ref.lower(), "")

        if not turma:
            # Cria a turma automaticamente se não existir
            if nome_turma:
                turma = TurmaEstagio(
                    estagio_turno=nome_turma,
                    doc_ref=doc_ref or None,
                    prazo_indicacao=_parse_data(_col(row, "prazo_indicacao", "PRAZO_INDICACAO")),
                )
                db.session.add(turma)
                db.session.flush()
                turmas_cache[nome_turma.lower()] = turma
            else:
                erros.append(f"Linha {i}: turma '{nome_turma}' não encontrada — participante ignorado.")
                continue

        status_raw = _col(row, "status_participacao", "STATUS_PARTICIPACAO").strip()
        mapa_status = {
            "efetivamente fez": "Efetivamente fez",
            "fez": "Efetivamente fez",
            "faltou": "Faltou",
            "nao fez": "Não fez",
            "não fez": "Não fez",
            "indicado": "Indicado",
        }
        status = mapa_status.get(status_raw.lower(), status_raw or "Indicado")

        p = ParticipanteEstagio(
            turma_id=turma.id,
            nome_voluntario=nome_vol,
            empresa=_col(row, "empresa_voluntario", "EMPRESA_VOLUNTARIO", "empresa"),
            indicado_por=_col(row, "indicado_por", "INDICADO_POR"),
            encaminhamento=_col(row, "encaminhamento", "ENCAMINHAMENTO"),
            doc_remessa_pedido=_col(row, "doc_remessa_pedido", "DOC_REMESSA_PEDIDO"),
            status_participacao=status,
        )
        db.session.add(p)
        importados += 1

    db.session.commit()
    _relatorio_flash(importados, erros, "Participantes de Estágio")
    return redirect(url_for("estagios.listar_turmas"))


# ── parceiros ─────────────────────────────────────────────────────────────────

@importacao_bp.route("/parceiros", methods=["GET", "POST"])
@login_required
@admin_required
def parceiros():
    """
    Colunas (7listas.csv):
    emp_colab;unid_pm;unid_pc;departamento_empresa;indicado_por;
    status_prest_conta;tipo_op;estagio_cie;status_participacao;status_verba_adm
    """
    if request.method == "GET":
        return render_template("importacao/parceiros.html")

    arquivo = request.files.get("arquivo")
    if not arquivo or not arquivo.filename:
        flash("Selecione um arquivo CSV.", "erro")
        return redirect(url_for("importacao.parceiros"))

    linhas, _ = _ler_csv(arquivo)
    importados = 0
    erros = []

    for i, row in enumerate(linhas, start=2):
        empresa = _col(row, "emp_colab", "EMP_COLAB", "empresa", "EMPRESA")
        if not empresa:
            continue

        tipo_raw = _col(row, "tipo_op", "TIPO_OP", "tipo_operacao").lower()
        if "sistematica" in tipo_raw or "sistemática" in tipo_raw:
            tipo = "Sistemática"
        elif "explorat" in tipo_raw:
            tipo = "Exploratória"
        else:
            tipo = tipo_raw.capitalize() if tipo_raw else ""

        p = Parceiro(
            empresa=empresa,
            unidade_pm=_col(row, "unid_pm", "UNID_PM", "unidade_pm"),
            unidade_pc=_col(row, "unid_pc", "UNID_PC", "unidade_pc"),
            departamento_empresa=_col(row, "departamento_empresa", "DEPARTAMENTO_EMPRESA"),
            indicado_por=_col(row, "indicado_por", "INDICADO_POR"),
            tipo_operacao=tipo,
            estagio_cie=_col(row, "estagio_cie", "ESTAGIO_CIE"),
            status_participacao=_col(row, "status_participacao", "STATUS_PARTICIPACAO"),
            status_prestacao_contas=_col(row, "status_prest_conta", "STATUS_PREST_CONTA", "status_prestacao_contas"),
            status_verba_adm=_col(row, "status_verba_adm", "STATUS_VERBA_ADM"),
        )
        db.session.add(p)
        importados += 1

    db.session.commit()
    _relatorio_flash(importados, erros, "Parceiros")
    return redirect(url_for("parceiros.listar"))
