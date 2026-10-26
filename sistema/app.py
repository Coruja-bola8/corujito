import os
from datetime import date
from flask import Flask, redirect, url_for, render_template
from flask_login import login_required
from flask_migrate import Migrate

from models import db
from auth import auth_bp, login_manager

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "troque-esta-chave-antes-de-usar-em-producao")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "instance", "dados.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)
    Migrate(app, db)

    app.register_blueprint(auth_bp)

    from blueprints.dashboard import dashboard_bp
    from blueprints.pessoal import pessoal_bp
    from blueprints.cargos import cargos_bp
    from blueprints.verba_operacional import verba_op_bp
    from blueprints.verba_adm import verba_adm_bp
    from blueprints.estagios import estagios_bp
    from blueprints.parceiros import parceiros_bp
    from blueprints.condecoracoes import condecoracoes_bp
    from blueprints.cursos import cursos_bp
    from blueprints.relatorios import relatorios_bp
    from blueprints.usuarios import usuarios_bp
    from blueprints.importacao import importacao_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(pessoal_bp)
    app.register_blueprint(cargos_bp)
    app.register_blueprint(verba_op_bp)
    app.register_blueprint(verba_adm_bp)
    app.register_blueprint(estagios_bp)
    app.register_blueprint(parceiros_bp)
    app.register_blueprint(condecoracoes_bp)
    app.register_blueprint(cursos_bp)
    app.register_blueprint(relatorios_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(importacao_bp)

    @app.route("/")
    @login_required
    def index():
        return redirect(url_for("dashboard.index"))

    @app.errorhandler(403)
    def acesso_negado(e):
        return render_template("403.html"), 403

    @app.errorhandler(404)
    def nao_encontrado(e):
        return render_template("404.html"), 404

    @app.context_processor
    def inject_globals():
        return {"ano_atual": date.today().year}

    with app.app_context():
        db.create_all()
        _seed_admin_padrao()

    return app


def _seed_admin_padrao():
    """Cria um usuário admin padrão no primeiro uso, se ainda não existir nenhum usuário."""
    from models import Usuario
    if Usuario.query.count() == 0:
        admin = Usuario(nome_completo="Administrador", username="admin", papel="admin")
        admin.set_senha("admin123")
        db.session.add(admin)
        db.session.commit()
        print("=" * 60)
        print("Usuário administrador padrão criado:")
        print("  usuário: admin")
        print("  senha:   admin123")
        print("TROQUE ESSA SENHA no primeiro acesso (menu Usuários).")
        print("=" * 60)


if __name__ == "__main__":
    app = create_app()
    # Segurança: bind exclusivo em loopback — nenhuma interface externa é exposta.
    # Acesso permitido apenas via http://localhost:5000 na própria máquina.
    # Para acesso remoto, usar sessão RDP/TeamViewer na máquina servidora.
    app.run(host="127.0.0.1", port=5000, debug=False)
