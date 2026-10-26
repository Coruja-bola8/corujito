from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from models import db, TurmaEstagio, ParticipanteEstagio
from auth import admin_required

estagios_bp = Blueprint("estagios", __name__, url_prefix="/estagios")


def _parse_data(valor):
    if not valor:
        return None
    return datetime.strptime(valor, "%Y-%m-%d").date()


# --- Turmas ---

@estagios_bp.route("/")
@login_required
def listar_turmas():
    turmas = TurmaEstagio.query.order_by(TurmaEstagio.dt_doc_ref.desc()).all()
    return render_template("estagios/turmas.html", turmas=turmas)


@estagios_bp.route("/nova", methods=["GET", "POST"])
@login_required
@admin_required
def nova_turma():
    if request.method == "POST":
        t = TurmaEstagio()
        _preencher_turma(t, request.form)
        db.session.add(t)
        db.session.commit()
        flash("Turma de estágio cadastrada.", "sucesso")
        return redirect(url_for("estagios.listar_turmas"))
    return render_template("estagios/turma_form.html", turma=None)


@estagios_bp.route("/<int:turma_id>/editar", methods=["GET", "POST"])
@login_required
@admin_required
def editar_turma(turma_id):
    t = db.get_or_404(TurmaEstagio, turma_id)
    if request.method == "POST":
        _preencher_turma(t, request.form)
        db.session.commit()
        flash("Turma atualizada.", "sucesso")
        return redirect(url_for("estagios.listar_turmas"))
    return render_template("estagios/turma_form.html", turma=t)


@estagios_bp.route("/<int:turma_id>/excluir", methods=["POST"])
@login_required
@admin_required
def excluir_turma(turma_id):
    t = db.get_or_404(TurmaEstagio, turma_id)
    db.session.delete(t)
    db.session.commit()
    flash("Turma removida.", "sucesso")
    return redirect(url_for("estagios.listar_turmas"))


def _preencher_turma(t, form):
    t.estagio_turno = form.get("estagio_turno", "").strip()
    t.doc_ref = form.get("doc_ref", "").strip()
    t.dt_doc_ref = _parse_data(form.get("dt_doc_ref"))
    t.dt_inicio_ead = _parse_data(form.get("dt_inicio_ead"))
    t.dt_fim_ead = _parse_data(form.get("dt_fim_ead"))
    t.dt_inicio_presencial = _parse_data(form.get("dt_inicio_presencial"))
    t.dt_fim_presencial = _parse_data(form.get("dt_fim_presencial"))
    t.prazo_indicacao = _parse_data(form.get("prazo_indicacao"))
    t.encaminhamento = form.get("encaminhamento", "").strip()


# --- Participantes ---

@estagios_bp.route("/<int:turma_id>/participantes")
@login_required
def listar_participantes(turma_id):
    turma = db.get_or_404(TurmaEstagio, turma_id)
    participantes = ParticipanteEstagio.query.filter_by(turma_id=turma_id).all()
    return render_template("estagios/participantes.html", turma=turma, participantes=participantes)


@estagios_bp.route("/<int:turma_id>/participantes/novo", methods=["GET", "POST"])
@login_required
@admin_required
def novo_participante(turma_id):
    turma = db.get_or_404(TurmaEstagio, turma_id)
    if request.method == "POST":
        p = ParticipanteEstagio(turma_id=turma_id)
        _preencher_participante(p, request.form)
        db.session.add(p)
        db.session.commit()
        flash("Participante adicionado.", "sucesso")
        return redirect(url_for("estagios.listar_participantes", turma_id=turma_id))
    return render_template("estagios/participante_form.html", turma=turma, participante=None)


@estagios_bp.route("/participantes/<int:participante_id>/editar", methods=["GET", "POST"])
@login_required
@admin_required
def editar_participante(participante_id):
    p = db.get_or_404(ParticipanteEstagio, participante_id)
    if request.method == "POST":
        _preencher_participante(p, request.form)
        db.session.commit()
        flash("Participante atualizado.", "sucesso")
        return redirect(url_for("estagios.listar_participantes", turma_id=p.turma_id))
    return render_template("estagios/participante_form.html", turma=p.turma, participante=p)


@estagios_bp.route("/participantes/<int:participante_id>/excluir", methods=["POST"])
@login_required
@admin_required
def excluir_participante(participante_id):
    p = db.get_or_404(ParticipanteEstagio, participante_id)
    turma_id = p.turma_id
    db.session.delete(p)
    db.session.commit()
    flash("Participante removido.", "sucesso")
    return redirect(url_for("estagios.listar_participantes", turma_id=turma_id))


def _preencher_participante(p, form):
    p.nome_voluntario = form.get("nome_voluntario", "").strip()
    p.empresa = form.get("empresa", "").strip()
    p.indicado_por = form.get("indicado_por", "").strip()
    p.encaminhamento = form.get("encaminhamento", "").strip()
    p.doc_remessa_pedido = form.get("doc_remessa_pedido", "").strip()
    p.status_participacao = form.get("status_participacao", "").strip()
