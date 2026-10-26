from datetime import date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

CATEGORIAS_POSTO = [
    "Oficial Superior",
    "Oficial Intermediário",
    "Oficial Subalterno",
    "Subtenente",
    "1º Sargento",
    "2º Sargento",
    "3º Sargento",
]

FONTES_VERBA_ADM = ["Verba do CIE", "FUNADOM"]

CONDECORACOES_PARCEIRO = [
    "Challenge Coin",
    "Diploma Amigo do CMSE",
    "Diploma Amigo do Exército",
    "Medalha do Exército",
    "Medalha Soldado do Silêncio",
    "Medalha do Pacificador",
    "Outra",
]


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"
    id = db.Column(db.Integer, primary_key=True)
    nome_completo = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    papel = db.Column(db.String(20), nullable=False, default="viewer")
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.Date, default=date.today)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def checar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    @property
    def is_admin(self):
        return self.papel == "admin"


class Militar(db.Model):
    __tablename__ = "militares"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14))
    idt = db.Column(db.String(30))
    posto_grad = db.Column(db.String(40), nullable=False)
    categoria_posto = db.Column(db.String(30))
    arma = db.Column(db.String(20))
    situacao = db.Column(db.String(30))
    circulo = db.Column(db.String(40))
    ano_formacao = db.Column(db.Integer)
    dt_praca = db.Column(db.Date)
    dt_ult_promocao = db.Column(db.Date)
    dt_om = db.Column(db.Date)
    dt_sede = db.Column(db.Date)
    observacoes = db.Column(db.Text)

    condecoracoes = db.relationship("Condecoracao", backref="militar", cascade="all, delete-orphan")
    cursos = db.relationship("Curso", backref="militar", cascade="all, delete-orphan")
    cargos = db.relationship("Cargo", backref="ocupante")

    @property
    def anos_sede(self):
        if not self.dt_sede:
            return None
        hoje = date.today()
        anos = hoje.year - self.dt_sede.year - (
            (hoje.month, hoje.day) < (self.dt_sede.month, self.dt_sede.day)
        )
        return anos

    @property
    def intervalo_tempo_sede(self):
        anos = self.anos_sede
        if anos is None:
            return "-"
        if anos >= 9:
            return "Mais de 9 anos"
        if anos >= 5:
            return "Entre 5 e 9 anos"
        if anos >= 3:
            return "Entre 3 e 5 anos"
        return "Menos de 3 anos"


class Cargo(db.Model):
    """Quadro de Cargos Previstos (QCP) e Quadro de Cargos (QC)."""
    __tablename__ = "cargos"
    id = db.Column(db.Integer, primary_key=True)
    cargo = db.Column(db.String(150), nullable=False)
    categoria_posto_previsto = db.Column(db.String(30), nullable=False)
    # Novos campos: vagas no QC (autorizado) e QCP (previsto na OM)
    vagas_qc = db.Column(db.Integer, default=0)   # vagas no QC oficial
    vagas_qcp = db.Column(db.Integer, default=1)  # vagas no QCP da OM
    habilitacao_exigida = db.Column(db.String(150))
    habilitacao_confirmada = db.Column(db.Boolean, default=False)
    ocupante_id = db.Column(db.Integer, db.ForeignKey("militares.id"), nullable=True)
    observacoes = db.Column(db.Text)

    @property
    def status_conformidade(self):
        if not self.ocupante_id:
            return "Claro (vago)"
        if self.habilitacao_exigida and not self.habilitacao_confirmada:
            return "Ocupado - habilitação pendente"
        return "Conforme"


class VerbaOperacional(db.Model):
    __tablename__ = "verba_operacional"
    id = db.Column(db.Integer, primary_key=True)
    data_recebimento = db.Column(db.Date, nullable=False)
    semestre_referencia = db.Column(db.String(10))
    valor = db.Column(db.Numeric(12, 2), nullable=False)
    origem = db.Column(db.String(150))
    quem_recebeu = db.Column(db.String(50))
    tipo_verba = db.Column(db.String(50))
    recibo_remessa = db.Column(db.String(50))
    status = db.Column(db.String(40))
    observacoes = db.Column(db.Text)


class VerbaAdm(db.Model):
    __tablename__ = "verba_adm"
    id = db.Column(db.Integer, primary_key=True)
    fonte = db.Column(db.String(30), nullable=False)
    ug = db.Column(db.String(40))
    nc = db.Column(db.String(40), nullable=False)
    nd = db.Column(db.String(40))
    empresa = db.Column(db.String(150))
    tipo_servico_material = db.Column(db.String(150))
    data = db.Column(db.Date)
    prazo_empenho = db.Column(db.Date)
    prazo_liquidacao = db.Column(db.Date)
    valor = db.Column(db.Numeric(12, 2))
    empenhado_em = db.Column(db.Date)
    liquidado_em = db.Column(db.Date)
    status = db.Column(db.String(40))
    observacoes = db.Column(db.Text)


class TurmaEstagio(db.Model):
    __tablename__ = "turmas_estagio"
    id = db.Column(db.Integer, primary_key=True)
    estagio_turno = db.Column(db.String(150), nullable=False)
    doc_ref = db.Column(db.String(80))
    dt_doc_ref = db.Column(db.Date)
    dt_inicio_ead = db.Column(db.Date)
    dt_fim_ead = db.Column(db.Date)
    dt_inicio_presencial = db.Column(db.Date)
    dt_fim_presencial = db.Column(db.Date)
    prazo_indicacao = db.Column(db.Date)
    encaminhamento = db.Column(db.String(150))
    participantes = db.relationship("ParticipanteEstagio", backref="turma", cascade="all, delete-orphan")


class ParticipanteEstagio(db.Model):
    __tablename__ = "participantes_estagio"
    id = db.Column(db.Integer, primary_key=True)
    turma_id = db.Column(db.Integer, db.ForeignKey("turmas_estagio.id"), nullable=False)
    nome_voluntario = db.Column(db.String(150), nullable=False)
    empresa = db.Column(db.String(150))
    indicado_por = db.Column(db.String(120))
    encaminhamento = db.Column(db.String(150))
    doc_remessa_pedido = db.Column(db.String(80))
    status_participacao = db.Column(db.String(40))


class Parceiro(db.Model):
    """Parceiro/colaborador civil — modelo expandido conforme requisitos v1.1.0."""
    __tablename__ = "parceiros"
    id = db.Column(db.Integer, primary_key=True)
    # Identificação pessoal
    nome = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14))
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(150))
    # Vínculo institucional
    empresa_instituicao = db.Column(db.String(150))
    departamento = db.Column(db.String(120))
    # Relacionamento / indicação
    referencia_id = db.Column(db.Integer, db.ForeignKey("parceiros.id"), nullable=True)
    # Estágio / participação
    estagio_cie = db.Column(db.String(80))
    status_participacao = db.Column(db.String(40))
    # Condecorações recebidas
    condecoracoes_recebidas = db.Column(db.String(300))  # CSV dos tipos
    data_condecoracoes = db.Column(db.Date)
    local_condecoracoes = db.Column(db.String(150))
    # Histórico de relacionamento
    data_ultima_visita = db.Column(db.Date)
    data_ultimo_encontro = db.Column(db.Date)
    local_ultimo_encontro = db.Column(db.String(150))
    observacoes = db.Column(db.Text)

    referencia = db.relationship("Parceiro", remote_side=[id], backref="indicados")


class Condecoracao(db.Model):
    __tablename__ = "condecoracoes"
    id = db.Column(db.Integer, primary_key=True)
    militar_id = db.Column(db.Integer, db.ForeignKey("militares.id"), nullable=False)
    medalha = db.Column(db.String(150), nullable=False)
    data_concessao = db.Column(db.Date)
    orgao_concessor = db.Column(db.String(150))
    observacoes = db.Column(db.Text)


class Curso(db.Model):
    __tablename__ = "cursos"
    id = db.Column(db.Integer, primary_key=True)
    militar_id = db.Column(db.Integer, db.ForeignKey("militares.id"), nullable=False)
    nome_curso = db.Column(db.String(150), nullable=False)
    instituicao = db.Column(db.String(150))
    data_conclusao = db.Column(db.Date)
    carga_horaria = db.Column(db.Integer)
    observacoes = db.Column(db.Text)
