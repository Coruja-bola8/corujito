from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from models import db, Condecoracao, Militar
from auth import admin_required

condecoracoes_bp = Blueprint("condecoracoes", __name__, url_prefix="/condecoracoes")


def _parse_data(valor):
    if not valor:
        return None
    return datetime.strptime(valor, "%Y-%m-%d").date()


@condecoracoes_bp.route("/")
@login_required
def listar():
    busca_medalha = request.args.get("medalha", "").strip()
    query = Condecoracao.query
    if busca_medalha:
        query = query.filter(Condecoracao.medalha.ilike(f"%{busca_medalha}%"))
    registros = query.join(Militar).order_by(Condecoracao.medalha, Militar.nome).all()
    return render_template("condecoracoes/list.html", registros=registros, busca_medalha=busca_medalha)


@condecoracoes_bp.route("/novo", methods=["GET", "POST"])
@login_required
@admin_required
def novo():
    militar_id = request.args.get("militar_id", type=int)
    if request.method == "POST":
        c = Condecoracao()
        _preencher(c, request.form)
        db.session.add(c)
        db.session.commit()
        flash("Condecoração registrada.", "sucesso")
        return redirect(url_for("pessoal.ficha", militar_id=c.militar_id))
    militares = Militar.query.order_by(Militar.nome).all()
    return render_template("condecoracoes/form.html", registro=None, militares=militares, militar_id=militar_id)


@condecoracoes_bp.route("/<int:registro_id>/editar", methods=["GET", "POST"])
@login_required
@admin_required
def editar(registro_id):
    c = db.get_or_404(Condecoracao, registro_id)
    if request.method == "POST":
        _preencher(c, request.form)
        db.session.commit()
        flash("Condecoração atualizada.", "sucesso")
        return redirect(url_for("pessoal.ficha", militar_id=c.militar_id))
    militares = Militar.query.order_by(Militar.nome).all()
    return render_template("condecoracoes/form.html", registro=c, militares=militares, militar_id=c.militar_id)


@condecoracoes_bp.route("/<int:registro_id>/excluir", methods=["POST"])
@login_required
@admin_required
def excluir(registro_id):
    c = db.get_or_404(Condecoracao, registro_id)
    militar_id = c.militar_id
    db.session.delete(c)
    db.session.commit()
    flash("Condecoração removida.", "sucesso")
    return redirect(url_for("pessoal.ficha", militar_id=militar_id))


def _preencher(c, form):
    c.militar_id = int(form.get("militar_id"))
    c.medalha = form.get("medalha", "").strip()
    c.data_concessao = _parse_data(form.get("data_concessao"))
    c.orgao_concessor = form.get("orgao_concessor", "").strip()
    c.observacoes = form.get("observacoes", "").strip()
