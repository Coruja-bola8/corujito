from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from models import db, VerbaAdm, FONTES_VERBA_ADM
from auth import admin_required

verba_adm_bp = Blueprint("verba_adm", __name__, url_prefix="/verba-adm")


def _parse_data(valor):
    if not valor:
        return None
    return datetime.strptime(valor, "%Y-%m-%d").date()


@verba_adm_bp.route("/")
@login_required
def listar():
    fonte = request.args.get("fonte", "")
    query = VerbaAdm.query
    if fonte:
        query = query.filter_by(fonte=fonte)
    registros = query.order_by(VerbaAdm.prazo_empenho).all()
    return render_template(
        "verba_adm/list.html", registros=registros, fontes=FONTES_VERBA_ADM, fonte_filtro=fonte
    )


@verba_adm_bp.route("/novo", methods=["GET", "POST"])
@login_required
@admin_required
def novo():
    if request.method == "POST":
        r = VerbaAdm()
        _preencher(r, request.form)
        db.session.add(r)
        db.session.commit()
        flash("NC cadastrada.", "sucesso")
        return redirect(url_for("verba_adm.listar"))
    return render_template("verba_adm/form.html", registro=None, fontes=FONTES_VERBA_ADM)


@verba_adm_bp.route("/<int:registro_id>/editar", methods=["GET", "POST"])
@login_required
@admin_required
def editar(registro_id):
    r = db.get_or_404(VerbaAdm, registro_id)
    if request.method == "POST":
        _preencher(r, request.form)
        db.session.commit()
        flash("NC atualizada.", "sucesso")
        return redirect(url_for("verba_adm.listar"))
    return render_template("verba_adm/form.html", registro=r, fontes=FONTES_VERBA_ADM)


@verba_adm_bp.route("/<int:registro_id>/excluir", methods=["POST"])
@login_required
@admin_required
def excluir(registro_id):
    r = db.get_or_404(VerbaAdm, registro_id)
    db.session.delete(r)
    db.session.commit()
    flash("NC removida.", "sucesso")
    return redirect(url_for("verba_adm.listar"))


def _preencher(r, form):
    r.fonte = form.get("fonte")
    r.ug = form.get("ug", "").strip()
    r.nc = form.get("nc", "").strip()
    r.nd = form.get("nd", "").strip()
    r.empresa = form.get("empresa", "").strip()
    r.tipo_servico_material = form.get("tipo_servico_material", "").strip()
    r.data = _parse_data(form.get("data"))
    r.prazo_empenho = _parse_data(form.get("prazo_empenho"))
    r.prazo_liquidacao = _parse_data(form.get("prazo_liquidacao"))
    valor = form.get("valor", "0").replace(",", ".")
    r.valor = float(valor) if valor else 0
    r.empenhado_em = _parse_data(form.get("empenhado_em"))
    r.liquidado_em = _parse_data(form.get("liquidado_em"))
    r.status = form.get("status", "").strip()
    r.observacoes = form.get("observacoes", "").strip()
