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
    deletar_item_historico,
    listar_emails_autorizados,
    adicionar_email_autorizado
)
from fpdf import FPDF
import tempfile
import os

# =============================
# CONFIGURAÇÃO DA API (Cloud ou local)
# =============================
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    # se estiver rodando local sem secrets, importe sua config.py
    try:
        from config import configurar_api
        configurar_api()
    except Exception:
        # sem chave, a aplicação seguirá, mas chamadas à IA retornarão erro amigável
        pass

# =============================
# INICIALIZAÇÃO
# =============================
criar_tabelas()
st.set_page_config(page_title="PedagogIA", page_icon="🎓", layout="wide")

# estado
if "email" not in st.session_state:
    st.session_state.email = None
if "page" not in st.session_state:
    st.session_state.page = "login"  # "login" ou "cadastro"

# =============================
# Helpers IA / PDF
# =============================
def chamar_ia(prompt: str, modelo: str = "models/gemini-2.5-flash") -> str:
    try:
        model = genai.GenerativeModel(modelo)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"[Erro ao chamar a API de IA: {e}]"

def gerar_pdf_bytes(titulo: str, conteudo: str) -> bytes:
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
    try:
        os.unlink(tmp.name)
    except Exception:
        pass
    return data

# =============================
# TELAS: Login / Cadastro
# =============================
def tela_login():
    st.title("🔐 PedagogIA — Login")
    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if validar_login(email.strip(), senha):
            st.session_state.email = email.strip()
            st.success("Login bem-sucedido.")
            st.rerun()
        else:
            st.error("Email ou senha incorretos.")

    st.markdown("---")
    st.info("Se ainda não tem conta, clique em 'Criar Conta' na barra lateral e use um email autorizado.")

def tela_cadastro():
    st.title("📝 PedagogIA — Criar Conta")
    st.write("Apenas e-mails autorizados podem criar conta. Peça autorização para o responsável.")
    email = st.text_input("Email autorizado")
    nome = st.text_input("Nome")
    senha = st.text_input("Senha", type="password")

    if st.button("Criar Conta"):
        em = email.strip()
        if not em:
            st.error("Informe um email.")
            return
        if not email_autorizado(em):
            st.error("Este email NÃO está autorizado. Peça para adicionar à lista de autorizados.")
            return
        ok, msg = registrar_usuario(em, nome.strip(), senha)
        if ok:
            st.success("Conta criada com sucesso. Faça login.")
            st.session_state.page = "login"
            st.rerun()
        else:
            st.error(msg)

# =============================
# APP PRINCIPAL (após login)
# =============================
def app_principal():
    utilisateur = st.session_state.email
    st.sidebar.write(f"Conectado como: **{utilisateur}**")
    if st.sidebar.button("Logout"):
        st.session_state.email = None
        st.rerun()

    menu = st.sidebar.selectbox("Menu", [
        "Gerar Plano de Aula",
        "Analisar Conteúdo",
        "Simulador de Debate",
        "Histórico",
        "Gerenciar Emails Autorizados (opcional)"
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
    elif menu == "Gerenciar Emails Autorizados (opcional)":
        gerenciar_emails_autorizados()

# =============================
# FUNCIONALIDADES
# =============================
def gerar_plano():
    st.header("🪄 Gerador de Plano de Aula")
    tema = st.text_input("Tema da Aula")
    serie = st.text_input("Série/Ano Escolar")
    duracao = st.number_input("Duração (minutos)", min_value=10, max_value=180, value=50)
    titulo_salvar = st.text_input("Título para salvar (opcional):", f"Plano - {tema}")

    if st.button("Gerar Plano"):
        if not tema.strip():
            st.error("Informe o tema.")
            return
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
        with st.spinner("Gerando..."):
            texto = chamar_ia(prompt, modelo="models/gemini-2.5-flash")
        st.markdown(texto)
        salvar_historico(st.session_state.email, "Plano de Aula", titulo_salvar or tema, texto)
        st.download_button("Exportar para PDF", data=gerar_pdf_bytes(titulo_salvar or tema, texto),
                           file_name=f"{(titulo_salvar or tema).replace(' ','_')}.pdf", mime="application/pdf")

def analisar_conteudo():
    st.header("🔎 Analisador de Conteúdo")
    texto = st.text_area("Cole o texto aqui:", height=250)
    tipo = st.selectbox("Tipo de análise", ["Nivelamento de Leitura", "Simplificar para Crianças", "Extrair Conceitos-Chave"])
    titulo_salvar = st.text_input("Título para salvar (opcional):", "Análise de Conteúdo")

    if st.button("Analisar"):
        if not texto.strip():
            st.error("Insira um texto.")
            return
        prompt = f"Texto para análise: '''{texto}'''\nTarefa: {tipo}"
        with st.spinner("Analisando..."):
            resposta = chamar_ia(prompt)
        st.write(resposta)
        salvar_historico(st.session_state.email, "Análise", titulo_salvar or tipo, resposta)
        st.download_button("Exportar Análise em PDF", data=gerar_pdf_bytes(titulo_salvar or tipo, resposta),
                           file_name=f"{(titulo_salvar or tipo).replace(' ','_')}.pdf", mime="application/pdf")

def simular_debate():
    st.header("🏛️ Simulador de Debate")
    tema = st.text_input("Tema Central do Debate")
    lado_a = st.text_input("Lado A (perspectiva)")
    lado_b = st.text_input("Lado B (perspectiva)")
    titulo_salvar = st.text_input("Título para salvar (opcional):", f"Debate - {tema}")

    if st.button("Gerar Debate"):
        if not tema.strip():
            st.error("Informe um tema.")
            return
        prompt = f"""
Crie um roteiro para um debate em sala de aula.
Tema: {tema}
Lado A: {lado_a}
Lado B: {lado_b}

Estruture a resposta em Markdown com resumos e 3 argumentos para cada lado.
"""
        with st.spinner("Gerando..."):
            resp = chamar_ia(prompt)
        st.markdown(resp)
        salvar_historico(st.session_state.email, "Debate", titulo_salvar or tema, resp)
        st.download_button("Exportar Debate em PDF", data=gerar_pdf_bytes(titulo_salvar or tema, resp),
                           file_name=f"{(titulo_salvar or tema).replace(' ','_')}.pdf", mime="application/pdf")

# ---------- Histórico (clicável) ----------
def historico():
    st.header("📚 Histórico")
    itens = listar_historico_usuario(st.session_state.email)
    if not itens:
        st.info("Você ainda não gerou nada.")
        return
    for id_, tipo, titulo, created in itens:
        cols = st.columns([6, 2, 2])
        cols[0].markdown(f"**{titulo}** — _{tipo}_  \n{created.split('T')[0]}")
        if cols[1].button("Abrir", key=f"open_{id_}"):
            item = obter_item_historico(id_)
            if item:
                _, em, tp, ttl, conteudo, dt = item
                st.markdown(f"### {ttl} — {tp}")
                st.write(f"_Gerado por {em} em {dt}_")
                st.markdown(conteudo)
                st.download_button("Exportar em PDF", data=gerar_pdf_bytes(ttl, conteudo),
                                   file_name=f"{ttl.replace(' ','_')}.pdf", mime="application/pdf")
        if cols[2].button("Excluir", key=f"del_{id_}"):
            deletar_item_historico(id_)
            st.success("Item excluído.")
            st.rerun()

# ---------- Gerenciar emails autorizados (simples) ----------
def gerenciar_emails_autorizados():
    st.header("🔑 Emails autorizados (apenas para manutenção)")
    st.info("Aqui você pode ver e adicionar e-mails que poderão criar contas. (Sem remoção via UI por segurança.)")
    rows = listar_emails_autorizados()
    st.write("Emails autorizados:")
    for r in rows:
        st.write("-", r[0])

    novo = st.text_input("Adicionar novo email autorizado")
    if st.button("Adicionar email autorizado"):
        if novo.strip():
            if adicionar_email_autorizado(novo.strip()):
                st.success("Email adicionado. Agora esse email poderá criar conta.")
                st.rerun()
            else:
                st.error("Falha ao adicionar (talvez já exista).")

# =============================
# ROTEAMENTO PÁGINAS (login / cadastro / app)
# =============================
if st.session_state.email is None:
    # mostra menu lateral para escolher entre login / cadastro
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

