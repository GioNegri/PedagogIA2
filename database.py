import sqlite3
from datetime import datetime
import bcrypt
from typing import Optional, List, Tuple

DB_PATH = "pedagogia.db"

def conectar():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def criar_tabelas():
    """Cria tabelas essenciais e adiciona emails autorizados iniciais."""
    conn = conectar()
    c = conn.cursor()

    # tabela de emails autorizados
    c.execute("""
    CREATE TABLE IF NOT EXISTS emails_autorizados (
        email TEXT PRIMARY KEY
    )
    """)

    # tabela de usuários cadastrados
    c.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        email TEXT PRIMARY KEY,
        nome TEXT,
        senha_hash BLOB NOT NULL
    )
    """)

    # histórico de conteúdos gerados
    c.execute("""
    CREATE TABLE IF NOT EXISTS historico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        tipo TEXT,
        titulo TEXT,
        conteudo TEXT,
        created_at TEXT,
        FOREIGN KEY(email) REFERENCES usuarios(email)
    )
    """)

    # --- seeds: adicione aqui emails que podem criar conta ---
    # Ex.: gn@gmail.com e giovannenegri@gmail.com (você pode remover depois)
    seeds = [
        ("gn@gmail.com",),
        ("giovannenegri@gmail.com",)
    ]
    c.executemany("INSERT OR IGNORE INTO emails_autorizados (email) VALUES (?)", seeds)

    conn.commit()
    conn.close()

# ---------- Emails autorizados ----------
def listar_emails_autorizados() -> List[Tuple[str]]:
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT email FROM emails_autorizados ORDER BY email")
    rows = c.fetchall()
    conn.close()
    return rows

def adicionar_email_autorizado(email: str) -> bool:
    conn = conectar()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO emails_autorizados (email) VALUES (?)", (email,))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

def remover_email_autorizado(email: str) -> None:
    conn = conectar()
    c = conn.cursor()
    c.execute("DELETE FROM emails_autorizados WHERE email = ?", (email,))
    conn.commit()
    conn.close()

def email_autorizado(email: str) -> bool:
    """Retorna True se o email está na lista autorizada (permitido criar conta)."""
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT 1 FROM emails_autorizados WHERE email = ?", (email,))
    row = c.fetchone()
    conn.close()
    return row is not None

# ---------- Usuários ----------
def registrar_usuario(email: str, nome: str, senha_plain: str) -> Tuple[bool, str]:
    """Cria usuário (apenas se email estiver autorizado)."""
    if not email_autorizado(email):
        return False, "Email não autorizado para criação de conta."

    senha_hash = bcrypt.hashpw(senha_plain.encode("utf-8"), bcrypt.gensalt())
    conn = conectar()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO usuarios (email, nome, senha_hash) VALUES (?, ?, ?)",
                  (email, nome, senha_hash))
        conn.commit()
        return True, "Usuário registrado."
    except sqlite3.IntegrityError:
        return False, "Usuário já existe."
    finally:
        conn.close()

def validar_login(email: str, senha_plain: str) -> bool:
    """Valida credenciais (comparing bcrypt hashes)."""
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT senha_hash FROM usuarios WHERE email = ?", (email,))
    row = c.fetchone()
    conn.close()
    if not row:
        return False
    senha_hash = row[0]  # bytes
    try:
        return bcrypt.checkpw(senha_plain.encode("utf-8"), senha_hash)
    except Exception:
        return False

def remover_usuario(email: str) -> None:
    conn = conectar()
    c = conn.cursor()
    c.execute("DELETE FROM usuarios WHERE email = ?", (email,))
    conn.commit()
    conn.close()

# ---------- Histórico ----------
def salvar_historico(email: str, tipo: str, titulo: str, conteudo: str) -> None:
    conn = conectar()
    c = conn.cursor()
    c.execute("""
        INSERT INTO historico (email, tipo, titulo, conteudo, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (email, tipo, titulo, conteudo, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def listar_historico_usuario(email: str):
    conn = conectar()
    c = conn.cursor()
    c.execute("""
        SELECT id, tipo, titulo, created_at
        FROM historico
        WHERE email = ?
        ORDER BY id DESC
    """, (email,))
    rows = c.fetchall()
    conn.close()
    return rows

def listar_historico_todos():
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT id, email, tipo, titulo, created_at FROM historico ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def obter_item_historico(item_id: int):
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT id, email, tipo, titulo, conteudo, created_at FROM historico WHERE id = ?", (item_id,))
    row = c.fetchone()
    conn.close()
    return row

def deletar_item_historico(item_id: int) -> None:
    conn = conectar()
    c = conn.cursor()
    c.execute("DELETE FROM historico WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
