from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from models import db, Curso, Militar
from auth import admin_required

cursos_bp = Blueprint("cursos", __name__, url_prefix="/cursos")


def _parse_data(valor):
    if not valor:
        return None
    return datetime.strptime(valor, "%Y-%m-%d").date()


@cursos_bp.route("/")
@login_required
def listar():
    busca = request.args.get("q", "").strip()
    query = Curso.query
    if busca:
        query = query.filter(Curso.nome_curso.ilike(f"%{busca}%"))
    registros = query.join(Militar).order_by(Curso.nome_curso, Militar.nome).all()
    return render_template("cursos/list.html", registros=registros, busca=busca)


@cursos_bp.route("/novo", methods=["GET", "POST"])
@login_required
@admin_required
def novo():
    militar_id = request.args.get("militar_id", type=int)
    if request.method == "POST":
        c = Curso()
        _preencher(c, request.form)
        db.session.add(c)
        db.session.commit()
        flash("Curso registrado.", "sucesso")
        return redirect(url_for("pessoal.ficha", militar_id=c.militar_id))
    militares = Militar.query.order_by(Militar.nome).all()
    return render_template("cursos/form.html", registro=None, militares=militares, militar_id=militar_id)


@cursos_bp.route("/<int:registro_id>/editar", methods=["GET", "POST"])
@login_required
@admin_required
def editar(registro_id):
    c = db.get_or_404(Curso, registro_id)
    if request.method == "POST":
        _preencher(c, request.form)
        db.session.commit()
        flash("Curso atualizado.", "sucesso")
        return redirect(url_for("pessoal.ficha", militar_id=c.militar_id))
    militares = Militar.query.order_by(Militar.nome).all()
    return render_template("cursos/form.html", registro=c, militares=militares, militar_id=c.militar_id)


@cursos_bp.route("/<int:registro_id>/excluir", methods=["POST"])
@login_required
@admin_required
def excluir(registro_id):
    c = db.get_or_404(Curso, registro_id)
    militar_id = c.militar_id
    db.session.delete(c)
    db.session.commit()
    flash("Curso removido.", "sucesso")
    return redirect(url_for("pessoal.ficha", militar_id=militar_id))


def _preencher(c, form):
    c.militar_id = int(form.get("militar_id"))
    c.nome_curso = form.get("nome_curso", "").strip()
    c.instituicao = form.get("instituicao", "").strip()
    c.data_conclusao = _parse_data(form.get("data_conclusao"))
    carga = form.get("carga_horaria")
    c.carga_horaria = int(carga) if carga else None
    c.observacoes = form.get("observacoes", "").strip()
