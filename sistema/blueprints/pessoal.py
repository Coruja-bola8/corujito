from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from models import db, Militar, CATEGORIAS_POSTO
from auth import admin_required

pessoal_bp = Blueprint("pessoal", __name__, url_prefix="/pessoal")


def _parse_data(valor):
    if not valor:
        return None
    return datetime.strptime(valor, "%Y-%m-%d").date()


@pessoal_bp.route("/")
@login_required
def listar():
    busca = request.args.get("q", "").strip()
    query = Militar.query
    if busca:
        like = f"%{busca}%"
        query = query.filter(db.or_(Militar.nome.ilike(like), Militar.cpf.ilike(like)))
    militares = query.order_by(Militar.nome).all()
    return render_template("pessoal/list.html", militares=militares, busca=busca)


@pessoal_bp.route("/novo", methods=["GET", "POST"])
@login_required
@admin_required
def novo():
    if request.method == "POST":
        m = Militar()
        _preencher(m, request.form)
        db.session.add(m)
        db.session.commit()
        flash("Militar cadastrado com sucesso.", "sucesso")
        return redirect(url_for("pessoal.listar"))
    return render_template("pessoal/form.html", militar=None, categorias=CATEGORIAS_POSTO)


@pessoal_bp.route("/<int:militar_id>/editar", methods=["GET", "POST"])
@login_required
@admin_required
def editar(militar_id):
    m = db.get_or_404(Militar, militar_id)
    if request.method == "POST":
        _preencher(m, request.form)
        db.session.commit()
        flash("Dados atualizados.", "sucesso")
        return redirect(url_for("pessoal.listar"))
    return render_template("pessoal/form.html", militar=m, categorias=CATEGORIAS_POSTO)


@pessoal_bp.route("/<int:militar_id>/excluir", methods=["POST"])
@login_required
@admin_required
def excluir(militar_id):
    m = db.get_or_404(Militar, militar_id)
    db.session.delete(m)
    db.session.commit()
    flash("Militar removido.", "sucesso")
    return redirect(url_for("pessoal.listar"))


@pessoal_bp.route("/<int:militar_id>/ficha")
@login_required
def ficha(militar_id):
    m = db.get_or_404(Militar, militar_id)
    return render_template("pessoal/ficha.html", m=m)


def _preencher(m, form):
    m.nome = form.get("nome", "").strip()
    m.cpf = form.get("cpf", "").strip()
    m.idt = form.get("idt", "").strip()
    m.posto_grad = form.get("posto_grad", "").strip()
    m.categoria_posto = form.get("categoria_posto") or None
    m.arma = form.get("arma", "").strip()
    m.situacao = form.get("situacao", "").strip()
    m.circulo = form.get("circulo", "").strip()
    ano = form.get("ano_formacao")
    m.ano_formacao = int(ano) if ano else None
    m.dt_praca = _parse_data(form.get("dt_praca"))
    m.dt_ult_promocao = _parse_data(form.get("dt_ult_promocao"))
    m.dt_om = _parse_data(form.get("dt_om"))
    m.dt_sede = _parse_data(form.get("dt_sede"))
    m.observacoes = form.get("observacoes", "").strip()
