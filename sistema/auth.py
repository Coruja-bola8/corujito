from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import timedelta
from models import db, Usuario

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Faça login para continuar."
# Sessão expira quando o navegador fecha (sem "lembrar de mim")
login_manager.session_protection = "strong"

auth_bp = Blueprint("auth", __name__)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Nunca redireciona usuário já logado sem exigir nova autenticação
    # (session_protection=strong + permanent=False garantem que fechar o
    # navegador destrói a sessão)
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        senha = request.form.get("senha", "")
        usuario = Usuario.query.filter_by(username=username).first()
        if usuario and usuario.ativo and usuario.checar_senha(senha):
            # remember=False: sessão não persiste após fechar o navegador
            login_user(usuario, remember=False)
            proximo = request.args.get("next")
            return redirect(proximo or url_for("dashboard.index"))
        flash("Usuário ou senha inválidos, ou usuário inativo.", "erro")
    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sessão encerrada. Até logo!", "sucesso")
    return redirect(url_for("auth.login"))
