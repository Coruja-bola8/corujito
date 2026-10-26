from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from models import db, Usuario
from auth import admin_required

usuarios_bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


@usuarios_bp.route("/")
@login_required
@admin_required
def listar():
    usuarios = Usuario.query.order_by(Usuario.nome_completo).all()
    return render_template("usuarios/list.html", usuarios=usuarios)


@usuarios_bp.route("/novo", methods=["GET", "POST"])
@login_required
@admin_required
def novo():
    if request.method == "POST":
        u = Usuario(
            nome_completo=request.form.get("nome_completo", "").strip(),
            username=request.form.get("username", "").strip(),
            papel=request.form.get("papel", "viewer"),
        )
        u.set_senha(request.form.get("senha") or "mude123")
        db.session.add(u)
        db.session.commit()
        flash("Usuário cadastrado.", "sucesso")
        return redirect(url_for("usuarios.listar"))
    return render_template("usuarios/form.html", usuario=None)


@usuarios_bp.route("/<int:usuario_id>/editar", methods=["GET", "POST"])
@login_required
@admin_required
def editar(usuario_id):
    u = db.get_or_404(Usuario, usuario_id)
    if request.method == "POST":
        u.nome_completo = request.form.get("nome_completo", "").strip()
        u.username = request.form.get("username", "").strip()
        u.papel = request.form.get("papel", "viewer")
        u.ativo = bool(request.form.get("ativo"))
        nova_senha = request.form.get("senha")
        if nova_senha:
            u.set_senha(nova_senha)
        db.session.commit()
        flash("Usuário atualizado.", "sucesso")
        return redirect(url_for("usuarios.listar"))
    return render_template("usuarios/form.html", usuario=u)


@usuarios_bp.route("/<int:usuario_id>/excluir", methods=["POST"])
@login_required
@admin_required
def excluir(usuario_id):
    if usuario_id == current_user.id:
        flash("Você não pode excluir o próprio usuário.", "erro")
        return redirect(url_for("usuarios.listar"))
    u = db.get_or_404(Usuario, usuario_id)
    db.session.delete(u)
    db.session.commit()
    flash("Usuário removido.", "sucesso")
    return redirect(url_for("usuarios.listar"))
