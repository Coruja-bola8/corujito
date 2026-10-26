from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from models import db, VerbaOperacional
from auth import admin_required

verba_op_bp = Blueprint("verba_operacional", __name__, url_prefix="/verba-operacional")


def _parse_data(valor):
    if not valor:
        return None
    return datetime.strptime(valor, "%Y-%m-%d").date()


@verba_op_bp.route("/")
@login_required
def listar():
    registros = VerbaOperacional.query.order_by(VerbaOperacional.data_recebimento.desc()).all()
    total = sum(float(r.valor) for r in registros)
    return render_template("verba_operacional/list.html", registros=registros, total=total)


@verba_op_bp.route("/novo", methods=["GET", "POST"])
@login_required
@admin_required
def novo():
    if request.method == "POST":
        r = VerbaOperacional()
        _preencher(r, request.form)
        db.session.add(r)
        db.session.commit()
        flash("Registro de verba operacional adicionado.", "sucesso")
        return redirect(url_for("verba_operacional.listar"))
    return render_template("verba_operacional/form.html", registro=None)


@verba_op_bp.route("/<int:registro_id>/editar", methods=["GET", "POST"])
@login_required
@admin_required
def editar(registro_id):
    r = db.get_or_404(VerbaOperacional, registro_id)
    if request.method == "POST":
        _preencher(r, request.form)
        db.session.commit()
        flash("Registro atualizado.", "sucesso")
        return redirect(url_for("verba_operacional.listar"))
    return render_template("verba_operacional/form.html", registro=r)


@verba_op_bp.route("/<int:registro_id>/excluir", methods=["POST"])
@login_required
@admin_required
def excluir(registro_id):
    r = db.get_or_404(VerbaOperacional, registro_id)
    db.session.delete(r)
    db.session.commit()
    flash("Registro removido.", "sucesso")
    return redirect(url_for("verba_operacional.listar"))


def _preencher(r, form):
    r.data_recebimento = _parse_data(form.get("data_recebimento"))
    r.semestre_referencia = form.get("semestre_referencia", "").strip()
    valor = form.get("valor", "0").replace(",", ".")
    r.valor = float(valor) if valor else 0
    r.origem = form.get("origem", "").strip()
    r.quem_recebeu = form.get("quem_recebeu", "").strip()
    r.tipo_verba = form.get("tipo_verba", "").strip()
    r.recibo_remessa = form.get("recibo_remessa", "").strip()
    r.status = form.get("status", "").strip()
    r.observacoes = form.get("observacoes", "").strip()
