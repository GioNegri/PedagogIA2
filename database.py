import sqlite3
import bcrypt

# ============================================
# CONEXÃO
# ============================================
def conectar():
    return sqlite3.connect("dados.db", check_same_thread=False)

# ============================================
# CRIAÇÃO DE TABELAS
# ============================================
def criar_tabelas():
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            email TEXT PRIMARY KEY,
            nome TEXT,
            senha TEXT,
            autorizado INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            tipo TEXT,
            titulo TEXT,
            conteudo TEXT,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (email) REFERENCES usuarios(email)
        )
    """)

    conn.commit()
    conn.close()

# ============================================
# GERENCIAMENTO DE USUÁRIOS
# ============================================
def registrar_usuario(email, nome, senha):
    conn = conectar()
    cur = conn.cursor()

    hash_senha = bcrypt.hashpw(senha.encode(), bcrypt.gensalt())

    cur.execute("""
        INSERT OR REPLACE INTO usuarios (email, nome, senha, autorizado)
        VALUES (?, ?, ?, 1)
    """, (email, nome, hash_senha))

    conn.commit()
    conn.close()


def email_autorizado(email):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT autorizado FROM usuarios WHERE email = ?", (email,))
    linha = cur.fetchone()
    conn.close()

    if not linha:
        return False
    return linha[0] == 1


def validar_login(email, senha):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT senha FROM usuarios WHERE email = ?", (email,))
    linha = cur.fetchone()
    conn.close()

    if not linha:
        return False

    senha_hash = linha[0]

    return bcrypt.checkpw(senha.encode(), senha_hash)

# ============================================
# HISTÓRICO
# ============================================
def salvar_historico(email, tipo, titulo, conteudo):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO historico (email, tipo, titulo, conteudo)
        VALUES (?, ?, ?, ?)
    """, (email, tipo, titulo, conteudo))

    conn.commit()
    conn.close()


def listar_historico_usuario(email):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, tipo, titulo, created
        FROM historico
        WHERE email = ?
        ORDER BY id DESC
    """, (email,))

    dados = cur.fetchall()
    conn.close()
    return dados


def obter_item_historico(id_):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT * FROM historico WHERE id = ?", (id_,))
    dado = cur.fetchone()
    conn.close()
    return dado


def deletar_item_historico(id_):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("DELETE FROM historico WHERE id = ?", (id_,))
    conn.commit()
    conn.close()
