# main.py
import streamlit as st
from config import configurar_api
import google.generativeai as genai
from database import (
    criar_tabelas,
    email_autorizado,
    registrar_usuario,
    salvar_historico,
    listar_historico_usuario,
    obter_item_historico,
    deletar_item_historico
)
from fpdf import FPDF
import tempfile
import os

# 1) Tenta carregar a API KEY do Streamlit Cloud
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
# 2) Se estiver rodando localmente, usa o config.py
except:
    from config import configurar_api
    configurar_api()

# Inicialização
criar_tabelas()
configurar_api()
st.set_page_config(page_title="PedagogIA", page_icon="🎓", layout="wide")

# Função IA
def chamar_ia(prompt, modelo='models/gemini-2.5-flash'):
    try:
        model = genai.GenerativeModel(modelo)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erro ao chamar API: {e}"

# PDF
def gerar_pdf_bytes(titulo, conteudo):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.multi_cell(0, 8, titulo)
    pdf.ln(4)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 6, conteudo)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name)
    with open(tmp.name, "rb") as f:
        data = f.read()
    os.unlink(tmp.name)
    return data

# ---------- LOGIN VIA STREAMLIT ----------
if "user" not in st.session_state:
    st.session_state.user = st.experimental_user  # dados do Google/GitHub

user = st.session_state.user

if user is None:
    st.warning("Faça login para continuar.")
    st.stop()

email = user["email"]
nome = user.get("name", "Professor(a)")

# Verificar autorização
if not email_autorizado(email):
    st.error(f"O e-mail **{email}** não está autorizado a acessar o PedagogIA.")
    st.stop()

# Registrar usuário no banco
registrar_usuario(email, nome)

# Sidebar
st.sidebar.write(f"Conectado como: **{email}**")
if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.rerun()

menu = st.sidebar.selectbox("Navegação", [
    "Gerar Plano de Aula",
    "Analisar Conteúdo",
    "Simulador de Debate",
    "Histórico"
])

st.title("PedagogIA")

# ---------- Funções principais ----------
def gerar_plano():
    st.header("🪄 Plano de Aula")
    tema = st.text_input("Tema da Aula")
    serie = st.text_input("Série/Ano Escolar")
    duracao = st.number_input("Duração (min)", min_value=10, max_value=180, value=50)
    titulo_salvar = f"Plano - {tema}"

    if st.button("Gerar Plano"):
        prompt = f"""
Crie um plano de aula completo e criativo.
Tema: {tema}
Série: {serie}
Duração: {duracao} minutos

Estruture em Markdown:
## Objetivos
## Introdução
## Desenvolvimento
## Atividade prática
## Avaliação
## Tarefa
"""
        texto = chamar_ia(prompt, modelo="models/gemini-2.5-pro")
        st.markdown(texto)

        salvar_historico(email, "Plano de Aula", titulo_salvar, texto)
        st.download_button("Exportar para PDF",
                           data=gerar_pdf_bytes(titulo_salvar, texto),
                           file_name="plano.pdf",
                           mime="application/pdf")

def analisar_conteudo():
    st.header("🔎 Análise")
    texto = st.text_area("Texto")
    tipo = st.selectbox("Tipo", ["Simplificar", "Extrair ideias", "Nivelar leitura"])
    titulo_salvar = "Análise de Conteúdo"

    if st.button("Analisar"):
        prompt = f"{tipo}: {texto}"
        resposta = chamar_ia(prompt)
        st.write(resposta)
        salvar_historico(email, "Análise", titulo_salvar, resposta)
        st.download_button("Exportar PDF",
                           gerar_pdf_bytes(titulo_salvar, resposta),
                           file_name="analise.pdf")

def simular_debate():
    st.header("🏛️ Simulador de Debate")
    tema = st.text_input("Tema")
    lado_a = st.text_input("Lado A")
    lado_b = st.text_input("Lado B")
    titulo_salvar = f"Debate - {tema}"

    if st.button("Gerar Debate"):
        prompt = f"""
Crie um debate estruturado:
Tema: {tema}
Lado A: {lado_a}
Lado B: {lado_b}
"""
        resp = chamar_ia(prompt)
        st.markdown(resp)
        salvar_historico(email, "Debate", titulo_salvar, resp)
        st.download_button("PDF", gerar_pdf_bytes(titulo_salvar, resp),
                           file_name="debate.pdf")

def historico():
    st.header("📚 Histórico")
    itens = listar_historico_usuario(email)

    if not itens:
        st.info("Nenhum conteúdo gerado ainda.")
        return

    for id_, tipo, titulo, created in itens:
        cols = st.columns([6,2,2])
        cols[0].markdown(f"**{titulo}** — _{tipo}_ ({created[:10]})")

        if cols[1].button("Abrir", key=f"open_{id_}"):
            item = obter_item_historico(id_)
            _, em, tp, ttl, conteudo, dt = item
            st.markdown(f"### {ttl} — {tp}")
            st.markdown(conteudo)

            st.download_button("Exportar PDF",
                               gerar_pdf_bytes(ttl, conteudo),
                               file_name=f"{ttl}.pdf")

        if cols[2].button("Excluir", key=f"del_{id_}"):
            deletar_item_historico(id_)
            st.success("Excluído.")
            st.rerun()


# ---------- Roteamento ----------
if menu == "Gerar Plano de Aula":
    gerar_plano()
elif menu == "Analisar Conteúdo":
    analisar_conteudo()
elif menu == "Simulador de Debate":
    simular_debate()
elif menu == "Histórico":
    historico()
