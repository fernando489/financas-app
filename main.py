import streamlit as st
import pandas as pd
from datetime import date
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Sistema Financeiro MEI", layout="centered")

BASE_PATH = Path(".")
DATA_PATH = BASE_PATH / "data" / "clientes"
DATA_PATH.mkdir(parents=True, exist_ok=True)

USUARIOS_FILE = BASE_PATH / "usuarios.csv"

# ---------------- SESSION ----------------
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario = None

# Inicializa a flag de rerun
if 'rerun' not in st.session_state:
    st.session_state['rerun'] = 0

# Função para forçar rerun
def forcar_rerun():
    st.session_state['rerun'] += 1

# ---------------- FUNÇÕES ----------------
def salvar_pdf(df, usuario):
    pdf_path = BASE_PATH / f"relatorio_{usuario}.pdf"
    doc = SimpleDocTemplate(str(pdf_path))
    styles = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph(f"<b>Relatório Financeiro - {usuario}</b>", styles["Title"]))
    elementos.append(Spacer(1, 10))

    tabela = [["Data", "Descrição", "Tipo", "Valor", "Categoria"]]

    for _, r in df.iterrows():
        tabela.append([
            str(r["data"])[:10],
            r["descricao"],
            r["tipo"],
            f"R$ {r['valor']:.2f}",
            r["categoria"]
        ])

    elementos.append(Table(tabela))
    doc.build(elementos)

    return pdf_path

# ---------------- LOGIN / CADASTRO ----------------
if not st.session_state.logado:

    aba = st.tabs(["🔐 Login", "🆕 Cadastro"])

    # -------- LOGIN --------
    with aba[0]:
        st.subheader("Login")

        user = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        entrar = st.button("Entrar")

        if entrar:
            if USUARIOS_FILE.exists():
                df_users = pd.read_csv(USUARIOS_FILE, dtype=str)

                ok = df_users[
                    (df_users["usuario"].str.strip() == user.strip()) &
                    (df_users["senha"].str.strip() == senha.strip())
                ]

                if not ok.empty:
                    st.session_state.logado = True
                    st.session_state.usuario = user
                    st.success("✅ Login realizado!")
                    forcar_rerun()  # substitui st.rerun()
                else:
                    st.error("❌ Usuário ou senha inválidos")
            else:
                st.error("❌ Arquivo usuarios.csv não encontrado")

    # -------- CADASTRO --------
    with aba[1]:
        st.subheader("Cadastro de Novo Usuário")

        novo_user = st.text_input("Novo usuário")
        nova_senha = st.text_input("Nova senha", type="password")
        cadastrar = st.button("Cadastrar")

        if cadastrar:
            if not novo_user or not nova_senha:
                st.warning("Preencha usuário e senha")
            else:
                if USUARIOS_FILE.exists():
                    df_users = pd.read_csv(USUARIOS_FILE, dtype=str)
                else:
                    df_users = pd.DataFrame(columns=["usuario", "senha"])

                if (df_users["usuario"] == novo_user).any():
                    st.error("Usuário já existe")
                else:
                    novo = pd.DataFrame([{
                        "usuario": novo_user,
                        "senha": nova_senha
                    }])
                    df_users = pd.concat([df_users, novo], ignore_index=True)
                    df_users.to_csv(USUARIOS_FILE, index=False)
                    st.success("✅ Usuário cadastrado! Pode fazer login.")

    st.stop()

# ---------------- APP ----------------
usuario = st.session_state.usuario
st.title("💼 Sistema Financeiro")
st.write(f"👤 Cliente: **{usuario}**")

ARQUIVO_CLIENTE = DATA_PATH / f"{usuario}.csv"

if ARQUIVO_CLIENTE.exists():
    df = pd.read_csv(ARQUIVO_CLIENTE, parse_dates=["data"])
else:
    df = pd.DataFrame(columns=["data", "descricao", "valor", "tipo", "categoria"])

# ---------------- FORM ----------------
st.subheader("📝 Novo lançamento")

with st.form("form_lancamento", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
        data = st.date_input("Data", value=date.today())
        descricao = st.text_input("Descrição")

    with col2:
        valor = st.number_input("Valor (R$)", step=0.01, format="%.2f")
        tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
        categoria_base = st.selectbox(
            "Categoria",
            ["Aluguel", "Fornecedor", "Combustível", "Alimentação", "Impostos", "Outros"]
        )
        categoria = st.text_input("Categoria personalizada") if categoria_base == "Outros" else categoria_base

    salvar = st.form_submit_button("Salvar lançamento")

if salvar:
    novo = pd.DataFrame([{
        "data": data,
        "descricao": descricao,
        "valor": valor,
        "tipo": tipo,
        "categoria": categoria
    }])
    df = pd.concat([df, novo], ignore_index=True)
    df.to_csv(ARQUIVO_CLIENTE, index=False)
    st.success("✅ Lançamento salvo!")
    forcar_rerun()  # substitui st.rerun()

# ---------------- FILTRO MÊS ----------------
st.subheader("📆 Filtro por mês")

if not df.empty:
    df["mes"] = df["data"].dt.to_period("M").astype(str)
    meses = sorted(df["mes"].unique())

    mes_sel = st.selectbox("Selecione o mês", ["Todos"] + meses)

    if mes_sel != "Todos":
        df_filtrado = df[df["mes"] == mes_sel]
    else:
        df_filtrado = df
else:
    df_filtrado = df

# ---------------- LISTA ----------------
if not df_filtrado.empty:
    st.subheader("📋 Lançamentos")

    for i, row in df_filtrado.iterrows():
        c1, c2, c3, c4, c5, c6 = st.columns([2, 3, 2, 2, 2, 1])
        c1.write(str(row["data"])[:10])
        c2.write(row["descricao"])
        c3.write(row["tipo"])
        c4.write(f"R$ {row['valor']:.2f}")
        c5.write(row["categoria"])

        if c6.button("❌", key=f"del_{i}"):
            df = df.drop(i)
            df.to_csv(ARQUIVO_CLIENTE, index=False)
            forcar_rerun()  # substitui st.rerun()

    # ---------------- GRÁFICO ----------------
    st.subheader("📈 Receita x Despesa")

    resumo = df_filtrado.groupby("tipo")["valor"].sum()
    st.bar_chart(resumo)

    # ---------------- PDF ----------------
    st.subheader("🧾 Relatório em PDF")

    pdf_path = salvar_pdf(df_filtrado, usuario)

    with open(pdf_path, "rb") as f:
        st.download_button(
            "Download PDF",
            data=f,
            file_name=f"relatorio_{usuario}.pdf"
        )

else:
    st.info("Nenhum lançamento para o período selecionado.")

# ---------------- LOGOUT ----------------
st.divider()
if st.button("Sair"):
    st.session_state.logado = False
    st.session_state.usuario = None
    forcar_rerun()  # substitui st.rerun()
