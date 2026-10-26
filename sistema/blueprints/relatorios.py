from flask import Blueprint, render_template, request
from flask_login import login_required

from models import db, Condecoracao, Curso, Militar

relatorios_bp = Blueprint("relatorios", __name__, url_prefix="/relatorios")


@relatorios_bp.route("/")
@login_required
def index():
    return render_template("relatorios/index.html")


@relatorios_bp.route("/por-medalha")
@login_required
def por_medalha():
    medalha_selecionada = request.args.get("medalha", "").strip()
    medalhas_disponiveis = [
        row[0] for row in db.session.query(Condecoracao.medalha).distinct().order_by(Condecoracao.medalha).all()
    ]
    registros = []
    if medalha_selecionada:
        registros = (
            Condecoracao.query.filter_by(medalha=medalha_selecionada)
            .join(Militar).order_by(Militar.nome).all()
        )
    return render_template(
        "relatorios/por_medalha.html",
        medalhas=medalhas_disponiveis,
        medalha_selecionada=medalha_selecionada,
        registros=registros,
    )


@relatorios_bp.route("/busca")
@login_required
def busca_nome_cpf():
    termo = request.args.get("q", "").strip()
    militares = []
    if termo:
        like = f"%{termo}%"
        militares = Militar.query.filter(
            db.or_(Militar.nome.ilike(like), Militar.cpf.ilike(like))
        ).order_by(Militar.nome).all()
    return render_template("relatorios/busca.html", termo=termo, militares=militares)
