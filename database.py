# database.py
import sqlite3
from datetime import datetime

DB_PATH = "pedagogia.db"

def conectar():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def criar_tabelas():
    conn = conectar()
    c = conn.cursor()

    # Tabela de usuários (dados básicos — sem senha)
    c.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        email TEXT PRIMARY KEY,
        nome TEXT
    )
    """)

    # Tabela de histórico
    c.execute("""
    CREATE TABLE IF NOT EXISTS historico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        tipo TEXT,
        titulo TEXT,
        conteudo TEXT,
        created_at TEXT
    )
    """)

    # Lista de e-mails permitidos para entrar no sistema
    c.execute("""
    CREATE TABLE IF NOT EXISTS emails_autorizados (
        email TEXT PRIMARY KEY
    )
    """)

    # Seu e-mail como autorizado
    c.execute("""
    INSERT OR IGNORE INTO emails_autorizados (email) VALUES (?)
    """, ("giovannenegri@gmail.com",))

    conn.commit()
    conn.close()


# ---------- Emails autorizados ----------
def email_autorizado(email):
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT email FROM emails_autorizados WHERE email = ?", (email,))
    row = c.fetchone()
    conn.close()
    return row is not None


# ---------- Usuários ----------
def registrar_usuario(email, nome):
    """
    Registra o usuário apenas com email e nome.
    """
    conn = conectar()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO usuarios (email, nome) VALUES (?, ?)", (email, nome))
    conn.commit()
    conn.close()


# ---------- Histórico ----------
def salvar_historico(email, tipo, titulo, conteudo):
    conn = conectar()
    c = conn.cursor()
    c.execute("INSERT INTO historico (email, tipo, titulo, conteudo, created_at) VALUES (?, ?, ?, ?, ?)",
              (email, tipo, titulo, conteudo, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def listar_historico_usuario(email):
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT id, tipo, titulo, created_at FROM historico WHERE email = ? ORDER BY created_at DESC", (email,))
    rows = c.fetchall()
    conn.close()
    return rows

def obter_item_historico(item_id):
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT id, email, tipo, titulo, conteudo, created_at FROM historico WHERE id = ?", (item_id,))
    row = c.fetchone()
    conn.close()
    return row

def deletar_item_historico(item_id):
    conn = conectar()
    c = conn.cursor()
    c.execute("DELETE FROM historico WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
