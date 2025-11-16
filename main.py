import streamlit as st
import google.generativeai as genai

from database import (
    criar_tabelas,
    email_autorizado,
    registrar_usuario,
    validar_login,
    salvar_historico,
    listar_historico_usuario,
    obter_item_historico,
    deletar_item_historico
)

from fpdf import FPDF
import tempfile
import os

# ======================================
# CONFIG GEMINI
# ======================================
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    from config import configurar_api
    configurar_api()

# ======================================
# INICIALIZAÇÃO
# ======================================
st.set_page_config(page_title="PedagogIA", page_icon="🎓", layout="wide")
criar_tabelas()

if "email" not in st.session_state:
    st.session_state.email = None

if "page" not in st.session_state:
    st.session_state.page = "login"   # login/cadastro

# ======================================
# FUNÇÃO IA
# ======================================
def chamar_ia(prompt, modelo="models/gemini-2.5-flash"):
    try:
        model = genai.GenerativeModel(modelo)
        resp = model.generate_content(prompt)
        return resp.text
    except Exception as e:
        return f"Erro: {e}"

# ======================================
# PDF
# ======================================
def gerar_pdf_bytes(titulo, conteudo):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.multi_cell(0, 8, titulo)
    pdf.ln(4)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 6, conteudo)

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp.name)

    with open(temp.name, "rb") as f:
        data = f.read()

    os.unlink(temp.name)
    return data

# ======================================
# TELAS
# ======================================
def tela_login():
    st.title("🔐 Login")

    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if validar_login(email, senha):
            st.session_state.email = email
            st.rerun()
        else:
            st.error("Email ou senha incorretos.")


def tela_cadastro():
    st.title("📝 Criar Conta")

    email = st.text_input("Email autorizado")
    nome = st.text_input("Nome")
    senha = st.text_input("Senha", type="password")

    if st.button("Criar"):
        if not email_autorizado(email):
            st.error("Este email NÃO está autorizado.")
        else:
            registrar_usuario(email, nome, senha)
            st.success("Conta criada. Faça login.")
            st.session_state.page = "login"
            st.rerun()

# ======================================
# APP PRINCIPAL
# ======================================
def app_principal():
    email = st.session_state.email

    st.sidebar.write(f"Conectado como **{email}**")

    if st.sidebar.button("Logout"):
        st.session_state.email = None
        st.rerun()

    menu = st.sidebar.selectbox("Menu", [
        "Gerar Plano de Aula",
        "Analisar Conteúdo",
        "Simulador de Debate",
        "Histórico"
    ])

    st.title("PedagogIA 🎓")

    if menu == "Gerar Plano de Aula":
        gerar_plano()
    elif menu == "Analisar Conteúdo":
        analisar_conteudo()
    elif menu == "Simulador de Debate":
        simular_debate()
    elif menu == "Histórico":
        historico()

# ======================================
# FUNCIONALIDADES
# ======================================
def gerar_plano():
    st.header("🪄 Plano de Aula")
    tema = st.text_input("Tema")
    serie = st.text_input("Série/Ano")
    duracao = st.number_input("Duração", 10, 200, 50)

    if st.button("Gerar"):
        prompt = f"""
Crie um plano de aula completo e detalhado.
Tema: {tema}
Série: {serie}
Duração: {duracao} minutos.
"""
        texto = chamar_ia(prompt)
        st.markdown(texto)

        salvar_historico(st.session_state.email, "Plano", tema, texto)

def analisar_conteudo():
    st.header("🔎 Análise")
    texto = st.text_area("Texto")

    if st.button("Analisar"):
        resp = chamar_ia(f"Analise o texto: {texto}")
        st.write(resp)

        salvar_historico(st.session_state.email, "Análise", "Análise", resp)

def simular_debate():
    st.header("🏛 Debate")
    tema = st.text_input("Tema")

    if st.button("Gerar Debate"):
        resp = chamar_ia(f"Simule um debate sobre o tema: {tema}")
        st.write(resp)

        salvar_historico(st.session_state.email, "Debate", tema, resp)

def historico():
    st.header("📚 Histórico")
    itens = listar_historico_usuario(st.session_state.email)

    for id_, tipo, titulo, created in itens:
        st.write(f"**{titulo}** — {tipo} ({created})")

        if st.button("Abrir", key=f"open_{id_}"):
            item = obter_item_historico(id_)
            st.markdown(item[4])

# ======================================
# MENU LATERAL (quando não logado)
# ======================================
if st.session_state.email is None:
    st.sidebar.title("Acesso")

    if st.sidebar.button("Login"):
        st.session_state.page = "login"

    if st.sidebar.button("Criar Conta"):
        st.session_state.page = "cadastro"

    if st.session_state.page == "login":
        tela_login()
    else:
        tela_cadastro()
else:
    app_principal()
