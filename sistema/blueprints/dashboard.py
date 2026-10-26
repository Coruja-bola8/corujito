from datetime import date, timedelta
from flask import Blueprint, render_template, request
from flask_login import login_required
from sqlalchemy import func, extract

from models import (
    db, Militar, Cargo, VerbaOperacional, VerbaAdm,
    TurmaEstagio, ParticipanteEstagio, CATEGORIAS_POSTO
)

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/")
@login_required
def index():
    hoje = date.today()
    em_30_dias: date = hoje + timedelta(days=30)
# NOVO: lê o período escolhido pelo usuário via URL#
    ano_filtro = request.args.get('ano', '', type=str).strip() # ex: '2026'
    sem_filtro = request.args.get('semestre', '', type=str).strip() # ex: '1' ou '2'
# Monta o label para exibir no card (ex: '1º Semestre de 2026')
    if ano_filtro and sem_filtro:
        label_periodo = f'{sem_filtro}o Semestre de {ano_filtro}'
    elif ano_filtro:
        label_periodo = f'Ano de {ano_filtro}'
    else:
        label_periodo = 'Todo o periodo'
    ano_atual = hoje.year

    # ── Efetivo ───────────────────────────────────────────────────────────────
    efetivo_total = Militar.query.count()
    efetivo_por_situacao = (
        db.session.query(Militar.situacao, func.count(Militar.id))
        .group_by(Militar.situacao).all()
    )

    # ── QC / QCP — vagas x ocupados x claros por categoria ───────────────────
    # O efetivo previsto da OM é a SOMA das vagas_qcp de todos os cargos
    efetivo_qcp_total = db.session.query(func.coalesce(func.sum(Cargo.vagas_qcp), 0)).scalar()
    efetivo_qc_total  = db.session.query(func.coalesce(func.sum(Cargo.vagas_qc), 0)).scalar()

    claros_por_categoria = []
    for cat in CATEGORIAS_POSTO:
        cargos_cat = Cargo.query.filter_by(categoria_posto_previsto=cat).all()
        vagas_qcp = sum(c.vagas_qcp or 1 for c in cargos_cat)
        vagas_qc  = sum(c.vagas_qc or 0 for c in cargos_cat)
        ocupados  = sum(1 for c in cargos_cat if c.ocupante_id)
        claros_qcp = vagas_qcp - ocupados
        claros_qc  = vagas_qc - ocupados
        claros_por_categoria.append({
            "categoria": cat,
            "vagas_qc": vagas_qc,
            "vagas_qcp": vagas_qcp,
            "ocupados": ocupados,
            "claros_qcp": claros_qcp,
            "claros_qc": claros_qc,
        })

    # ── Verba Operacional ─────────────────────────────────────────────────────
    # nn NOVO: query com filtro de período 
    query_verba = VerbaOperacional.query # começa sem filtro
    if ano_filtro: # se o usuário escolheu um ano, filtra por ele
        query_verba = query_verba.filter(func.strftime('%Y', VerbaOperacional.data_recebimento) == ano_filtro)
    if sem_filtro: # se escolheu semestre, filtra os meses
        if sem_filtro == '1':
            query_verba = query_verba.filter(func.strftime('%m', VerbaOperacional.data_recebimento).in_(['01','02','03','04','05','06']))
        elif sem_filtro == '2':
            query_verba = query_verba.filter(
                func.strftime('%m', VerbaOperacional.data_recebimento).in_(['07','08','09','10','11','12']))

# Calcula os totais com os filtros aplicados
    ids_filtrados = [r.id for r in query_verba.all()]
    recebido_total = db.session.query(func.coalesce(func.sum(VerbaOperacional.valor), 0)).filter(VerbaOperacional.id.in_(ids_filtrados)).scalar()
    a_prestar = db.session.query(func.coalesce(func.sum(VerbaOperacional.valor), 0)).filter(
        VerbaOperacional.status == 'A prestar conta',
        VerbaOperacional.id.in_(ids_filtrados)).scalar()

# Lista os anos disponíveis para preencher o seletor na tela
    anos_disponiveis = db.session.query(func.strftime('%Y', VerbaOperacional.data_recebimento)).distinct().order_by(func.strftime('%Y', VerbaOperacional.data_recebimento).desc()).all()
    anos_disponiveis = [a[0] for a in anos_disponiveis if a[0]]
        
    # ── Verba Administrativa — por fonte, por semestre e por ano ──────────────
    empenhos_vencendo = VerbaAdm.query.filter(
        VerbaAdm.prazo_empenho.isnot(None),
        VerbaAdm.prazo_empenho <= em_30_dias,
        VerbaAdm.status.in_(["Aguardando", "Atrasado"]),
    ).order_by(VerbaAdm.prazo_empenho).all()

    liquidacoes_vencendo = VerbaAdm.query.filter(
        VerbaAdm.prazo_liquidacao.isnot(None),
        VerbaAdm.prazo_liquidacao <= em_30_dias,
        VerbaAdm.status.in_(["Empenhado"]),
    ).order_by(VerbaAdm.prazo_liquidacao).all()

    # Total por fonte (geral)
    verba_por_fonte = (
        db.session.query(VerbaAdm.fonte, func.coalesce(func.sum(VerbaAdm.valor), 0))
        .group_by(VerbaAdm.fonte).all()
    )

    # Histórico anual por fonte
    verba_anual_por_fonte = (
        db.session.query(
            VerbaAdm.fonte,
            extract("year", VerbaAdm.data).label("ano"),
            func.coalesce(func.sum(VerbaAdm.valor), 0).label("total")
        )
        .filter(VerbaAdm.data.isnot(None))
        .group_by(VerbaAdm.fonte, "ano")
        .order_by("ano", VerbaAdm.fonte)
        .all()
    )

    # Histórico semestral por fonte (ano atual)
    verba_semestral = []
    for sem in [1, 2]:
        mes_ini = 1 if sem == 1 else 7
        mes_fim = 6 if sem == 1 else 12
        rows = (
            db.session.query(VerbaAdm.fonte,
                             func.coalesce(func.sum(VerbaAdm.valor), 0))
            .filter(
                VerbaAdm.data.isnot(None),
                extract("year", VerbaAdm.data) == ano_atual,
                extract("month", VerbaAdm.data) >= mes_ini,
                extract("month", VerbaAdm.data) <= mes_fim,
            )
            .group_by(VerbaAdm.fonte).all()
        )
        verba_semestral.append({"semestre": f"{sem}º/{ano_atual}", "dados": rows})

    # ── Estágios ──────────────────────────────────────────────────────────────
    turmas = TurmaEstagio.query.order_by(TurmaEstagio.dt_doc_ref.desc()).limit(6).all()
    resumo_turmas = []
    for t in turmas:
        indicados = ParticipanteEstagio.query.filter_by(turma_id=t.id).count()
        fizeram = ParticipanteEstagio.query.filter_by(
            turma_id=t.id, status_participacao="Efetivamente fez"
        ).count()
        resumo_turmas.append({"turma": t, "indicados": indicados, "fizeram": fizeram})

    prazos_indicacao_vencendo = TurmaEstagio.query.filter(
        TurmaEstagio.prazo_indicacao.isnot(None),
        TurmaEstagio.prazo_indicacao >= hoje,
        TurmaEstagio.prazo_indicacao <= em_30_dias,
    ).order_by(TurmaEstagio.prazo_indicacao).all()

    return render_template(
        "dashboard.html",
        efetivo_total=efetivo_total,
        efetivo_por_situacao=efetivo_por_situacao,
        efetivo_qcp_total=efetivo_qcp_total,
        efetivo_qc_total=efetivo_qc_total,
        claros_por_categoria=claros_por_categoria,
        recebido_total=recebido_total,
        a_prestar=a_prestar,
        label_periodo=label_periodo,
        anos_disponiveis=anos_disponiveis,
        ano_filtro=ano_filtro,
        sem_filtro=sem_filtro,
        empenhos_vencendo=empenhos_vencendo,
        liquidacoes_vencendo=liquidacoes_vencendo,
        verba_por_fonte=verba_por_fonte,
        verba_anual_por_fonte=verba_anual_por_fonte,
        verba_semestral=verba_semestral,
        resumo_turmas=resumo_turmas,
        prazos_indicacao_vencendo=prazos_indicacao_vencendo,
        hoje=hoje,
        ano_atual=ano_atual,
    )
