"""
migrar_banco.py — SGAUM v1.1.0
Atualiza o banco de dados existente adicionando as colunas novas.
Seguro: verifica se cada coluna já existe antes de adicionar.
Não apaga nenhum dado existente.

Uso:
  python migrar_banco.py
  (execute na pasta sistema do pen drive, com PYTHONPATH apontando para pacotes)
"""

import sqlite3
import os
import shutil
from datetime import datetime

# ── Localiza o banco ──────────────────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH  = os.path.join(BASE_DIR, "instance", "dados.db")

if not os.path.exists(DB_PATH):
    print(f"[ERRO] Banco não encontrado em: {DB_PATH}")
    print("Verifique se o arquivo dados.db está em: sistema\\instance\\dados.db")
    input("Pressione Enter para sair...")
    exit(1)

# ── Backup antes de migrar ────────────────────────────────────────────────────
TS = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP = os.path.join(BASE_DIR, "instance", f"dados_pre_migracao_{TS}.db")
shutil.copy2(DB_PATH, BACKUP)
print(f"[OK] Backup criado: instance/dados_pre_migracao_{TS}.db")

# ── Conecta ───────────────────────────────────────────────────────────────────
conn = sqlite3.connect(DB_PATH)
cur  = conn.cursor()

def colunas_existentes(tabela):
    """Retorna set com os nomes das colunas atuais de uma tabela."""
    cur.execute(f"PRAGMA table_info({tabela})")
    return {row[1] for row in cur.fetchall()}

def tabela_existe(tabela):
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tabela,))
    return cur.fetchone() is not None

def add_col(tabela, coluna, definicao):
    """Adiciona coluna apenas se não existir."""
    if coluna not in colunas_existentes(tabela):
        cur.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {definicao}")
        print(f"  [+] {tabela}.{coluna}")
        return True
    print(f"  [=] {tabela}.{coluna} (já existe)")
    return False

# ═══════════════════════════════════════════════════════════════════════════════
print("\nIniciando migração do banco de dados...")
print("=" * 55)

# ── Tabela: cargos ────────────────────────────────────────────────────────────
if tabela_existe("cargos"):
    print("\n[cargos]")
    add_col("cargos", "vagas_qc",  "INTEGER DEFAULT 0")
    add_col("cargos", "vagas_qcp", "INTEGER DEFAULT 1")
else:
    print("\n[AVISO] Tabela 'cargos' não encontrada — será criada pelo sistema.")

# ── Tabela: parceiros ─────────────────────────────────────────────────────────
if tabela_existe("parceiros"):
    print("\n[parceiros]")
    # Campos do modelo antigo que podem ter nomes diferentes
    cols = colunas_existentes("parceiros")

    # Campos novos do modelo expandido v1.1.0
    add_col("parceiros", "nome",                  "TEXT")
    add_col("parceiros", "cpf",                   "TEXT")
    add_col("parceiros", "telefone",              "TEXT")
    add_col("parceiros", "email",                 "TEXT")
    add_col("parceiros", "empresa_instituicao",   "TEXT")
    add_col("parceiros", "departamento",          "TEXT")
    add_col("parceiros", "referencia_id",         "INTEGER")
    add_col("parceiros", "estagio_cie",           "TEXT")
    add_col("parceiros", "status_participacao",   "TEXT")
    add_col("parceiros", "condecoracoes_recebidas", "TEXT")
    add_col("parceiros", "data_condecoracoes",    "DATE")
    add_col("parceiros", "local_condecoracoes",   "TEXT")
    add_col("parceiros", "data_ultima_visita",    "DATE")
    add_col("parceiros", "data_ultimo_encontro",  "DATE")
    add_col("parceiros", "local_ultimo_encontro", "TEXT")
    add_col("parceiros", "observacoes",           "TEXT")

    # Migrar dados do campo 'empresa' antigo para 'empresa_instituicao' se necessário
    if "empresa" in cols and "empresa_instituicao" in colunas_existentes("parceiros"):
        cur.execute("""
            UPDATE parceiros
            SET empresa_instituicao = empresa
            WHERE empresa_instituicao IS NULL AND empresa IS NOT NULL
        """)
        migrados = cur.rowcount
        if migrados > 0:
            print(f"  [>>] {migrados} registro(s): campo 'empresa' copiado para 'empresa_instituicao'")

    # Migrar campo 'nome': se não havia nome, usa a empresa como nome
    cur.execute("""
        UPDATE parceiros
        SET nome = COALESCE(empresa_instituicao, empresa, 'Sem nome')
        WHERE nome IS NULL OR nome = ''
    """)
    migrados = cur.rowcount
    if migrados > 0:
        print(f"  [>>] {migrados} registro(s): campo 'nome' preenchido automaticamente")

else:
    print("\n[AVISO] Tabela 'parceiros' não encontrada — será criada pelo sistema.")

# ── Tabela: militares ─────────────────────────────────────────────────────────
if tabela_existe("militares"):
    print("\n[militares]")
    # Garante campos que podem ter sido adicionados em versões intermediárias
    add_col("militares", "categoria_posto", "TEXT")
    add_col("militares", "observacoes",     "TEXT")

# ── Tabela: verba_adm ────────────────────────────────────────────────────────
if tabela_existe("verba_adm"):
    print("\n[verba_adm]")
    add_col("verba_adm", "tipo_servico_material", "TEXT")
    add_col("verba_adm", "empenhado_em",          "DATE")
    add_col("verba_adm", "liquidado_em",          "DATE")

# ── Tabela: condecoracoes ────────────────────────────────────────────────────
if tabela_existe("condecoracoes"):
    print("\n[condecoracoes]")
    add_col("condecoracoes", "observacoes", "TEXT")

# ── Tabela: cursos ───────────────────────────────────────────────────────────
if tabela_existe("cursos"):
    print("\n[cursos]")
    add_col("cursos", "observacoes", "TEXT")

# ═══════════════════════════════════════════════════════════════════════════════
conn.commit()
conn.close()

print("\n" + "=" * 55)
print("[OK] Migração concluída com sucesso!")
print(f"[OK] Backup salvo em: instance/dados_pre_migracao_{TS}.db")
print("\nAgora inicie o sistema normalmente com iniciar_portatil.bat")
input("\nPressione Enter para sair...")
