from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, Parceiro, CONDECORACOES_PARCEIRO
from auth import admin_required

parceiros_bp = Blueprint("parceiros", __name__, url_prefix="/parceiros")


def _parse_data(valor):
    if not valor:
        return None
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


@parceiros_bp.route("/")
@login_required
def listar():
    busca = request.args.get("q", "").strip()
    query = Parceiro.query
    if busca:
        query = query.filter(
            db.or_(Parceiro.nome.ilike(f"%{busca}%"),
                   Parceiro.empresa_instituicao.ilike(f"%{busca}%"))
        )
    registros = query.order_by(Parceiro.nome).all()
    return render_template("parceiros/list.html", registros=registros, busca=busca)


@parceiros_bp.route("/novo", methods=["GET", "POST"])
@login_required
@admin_required
def novo():
    if request.method == "POST":
        p = Parceiro()
        _preencher(p, request.form)
        db.session.add(p)
        db.session.commit()
        flash("Parceiro cadastrado.", "sucesso")
        return redirect(url_for("parceiros.listar"))
    todos = Parceiro.query.order_by(Parceiro.nome).all()
    return render_template("parceiros/form.html", parceiro=None,
                           todos_parceiros=todos,
                           condecoracoes_opcoes=CONDECORACOES_PARCEIRO)


@parceiros_bp.route("/<int:parceiro_id>/editar", methods=["GET", "POST"])
@login_required
@admin_required
def editar(parceiro_id):
    p = db.get_or_404(Parceiro, parceiro_id)
    if request.method == "POST":
        _preencher(p, request.form)
        db.session.commit()
        flash("Parceiro atualizado.", "sucesso")
        return redirect(url_for("parceiros.listar"))
    todos = Parceiro.query.filter(Parceiro.id != parceiro_id).order_by(Parceiro.nome).all()
    return render_template("parceiros/form.html", parceiro=p,
                           todos_parceiros=todos,
                           condecoracoes_opcoes=CONDECORACOES_PARCEIRO)


@parceiros_bp.route("/<int:parceiro_id>/excluir", methods=["POST"])
@login_required
@admin_required
def excluir(parceiro_id):
    p = db.get_or_404(Parceiro, parceiro_id)
    db.session.delete(p)
    db.session.commit()
    flash("Parceiro removido.", "sucesso")
    return redirect(url_for("parceiros.listar"))


@parceiros_bp.route("/excluir-em-massa", methods=["POST"])
@login_required
@admin_required
def excluir_em_massa():
    ids_raw = request.form.get("ids", "")
    ids = [int(i) for i in ids_raw.split(",") if i.strip().isdigit()]
    if not ids:
        flash("Nenhum registro selecionado.", "erro")
        return redirect(url_for("parceiros.listar"))
    removidos = Parceiro.query.filter(Parceiro.id.in_(ids)).delete(synchronize_session=False)
    db.session.commit()
    flash(f"{removidos} parceiro(s) excluído(s).", "sucesso")
    return redirect(url_for("parceiros.listar"))


def _preencher(p, form):
    p.nome = form.get("nome", "").strip()
    p.cpf = form.get("cpf", "").strip()
    p.telefone = form.get("telefone", "").strip()
    p.email = form.get("email", "").strip()
    p.empresa_instituicao = form.get("empresa_instituicao", "").strip()
    p.departamento = form.get("departamento", "").strip()
    ref = form.get("referencia_id")
    p.referencia_id = int(ref) if ref else None
    p.estagio_cie = form.get("estagio_cie", "").strip()
    p.status_participacao = form.get("status_participacao", "").strip()
    # Condecorações: lista múltipla
    conds = form.getlist("condecoracoes_recebidas")
    outra = form.get("condecoracoes_outra", "").strip()
    if outra and "Outra" in conds:
        conds = [c for c in conds if c != "Outra"] + [f"Outra: {outra}"]
    p.condecoracoes_recebidas = ", ".join(conds) if conds else None
    p.data_condecoracoes = _parse_data(form.get("data_condecoracoes"))
    p.local_condecoracoes = form.get("local_condecoracoes", "").strip()
    p.data_ultima_visita = _parse_data(form.get("data_ultima_visita"))
    p.data_ultimo_encontro = _parse_data(form.get("data_ultimo_encontro"))
    p.local_ultimo_encontro = form.get("local_ultimo_encontro", "").strip()
    p.observacoes = form.get("observacoes", "").strip()
