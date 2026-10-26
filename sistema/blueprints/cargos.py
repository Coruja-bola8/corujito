from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, Cargo, Militar, CATEGORIAS_POSTO
from auth import admin_required

cargos_bp = Blueprint("cargos", __name__, url_prefix="/cargos")


@cargos_bp.route("/")
@login_required
def listar():
    registros = Cargo.query.order_by(Cargo.categoria_posto_previsto, Cargo.cargo).all()
    return render_template("cargos/list.html", registros=registros)


@cargos_bp.route("/novo", methods=["GET", "POST"])
@login_required
@admin_required
def novo():
    if request.method == "POST":
        c = Cargo()
        _preencher(c, request.form)
        db.session.add(c)
        db.session.commit()
        flash("Cargo cadastrado.", "sucesso")
        return redirect(url_for("cargos.listar"))
    militares = Militar.query.order_by(Militar.nome).all()
    return render_template("cargos/form.html", cargo=None, categorias=CATEGORIAS_POSTO, militares=militares)


@cargos_bp.route("/<int:cargo_id>/editar", methods=["GET", "POST"])
@login_required
@admin_required
def editar(cargo_id):
    c = db.get_or_404(Cargo, cargo_id)
    if request.method == "POST":
        _preencher(c, request.form)
        db.session.commit()
        flash("Cargo atualizado.", "sucesso")
        return redirect(url_for("cargos.listar"))
    militares = Militar.query.order_by(Militar.nome).all()
    return render_template("cargos/form.html", cargo=c, categorias=CATEGORIAS_POSTO, militares=militares)


@cargos_bp.route("/<int:cargo_id>/excluir", methods=["POST"])
@login_required
@admin_required
def excluir(cargo_id):
    c = db.get_or_404(Cargo, cargo_id)
    db.session.delete(c)
    db.session.commit()
    flash("Cargo removido.", "sucesso")
    return redirect(url_for("cargos.listar"))


@cargos_bp.route("/excluir-em-massa", methods=["POST"])
@login_required
@admin_required
def excluir_em_massa():
    ids_raw = request.form.get("ids", "")
    ids = [int(i) for i in ids_raw.split(",") if i.strip().isdigit()]
    if not ids:
        flash("Nenhum registro selecionado.", "erro")
        return redirect(url_for("cargos.listar"))
    removidos = Cargo.query.filter(Cargo.id.in_(ids)).delete(synchronize_session=False)
    db.session.commit()
    flash(f"{removidos} cargo(s) excluído(s).", "sucesso")
    return redirect(url_for("cargos.listar"))


def _preencher(c, form):
    c.cargo = form.get("cargo", "").strip()
    c.categoria_posto_previsto = form.get("categoria_posto_previsto")
    try:
        c.vagas_qc = int(form.get("vagas_qc") or 0)
    except ValueError:
        c.vagas_qc = 0
    try:
        c.vagas_qcp = int(form.get("vagas_qcp") or 1)
    except ValueError:
        c.vagas_qcp = 1
    c.habilitacao_exigida = form.get("habilitacao_exigida", "").strip()
    c.habilitacao_confirmada = bool(form.get("habilitacao_confirmada"))
    ocupante = form.get("ocupante_id")
    c.ocupante_id = int(ocupante) if ocupante else None
    c.observacoes = form.get("observacoes", "").strip()
