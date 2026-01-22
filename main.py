import streamlit as st
import pandas as pd
from datetime import date
from pathlib import Path

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

# ---------------- LOGIN ----------------
if not st.session_state.logado:
    st.title("🔐 Login")

    user = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    entrar = st.button("Entrar")

    if entrar:
        if USUARIOS_FILE.exists():
            df_users = pd.read_csv(USUARIOS_FILE, dtype=str)

            # DEBUG (pode remover depois)
            st.write("DEBUG - Conteúdo do usuarios.csv")
            st.write(df_users)

            ok = df_users[
                (df_users["usuario"] == user) &
                (df_users["senha"] == senha)
            ]

            if not ok.empty:
                st.session_state.logado = True
                st.session_state.usuario = user
                st.success("✅ Login realizado!")
                st.rerun()
            else:
                st.error("❌ Usuário ou senha inválidos")
        else:
            st.error("❌ Arquivo usuarios.csv não encontrado")

    st.stop()

# ---------------- APP ----------------
usuario = st.session_state.usuario
st.title("💼 Sistema Financeiro do Cliente")
st.write(f"👤 Cliente: **{usuario}**")

ARQUIVO_CLIENTE = DATA_PATH / f"{usuario}.csv"

if ARQUIVO_CLIENTE.exists():
    df = pd.read_csv(ARQUIVO_CLIENTE, parse_dates=["data"])
else:
    df = pd.DataFrame(columns=["data", "descricao", "valor", "tipo", "categoria"])

# ---------------- FORM LANÇAMENTO ----------------
st.subheader("📝 Novo lançamento")

with st.form("form_lancamento"):
    col1, col2 = st.columns(2)

    with col1:
        data = st.date_input("Data", value=date.today())
        descricao = st.text_input("Descrição")

    with col2:
        valor = st.number_input("Valor (R$)", step=0.01, format="%.2f")
        tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
        categoria = st.selectbox(
            "Categoria",
            ["Aluguel", "Fornecedor", "Combustível", "Alimentação", "Impostos", "Outros"]
        )

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
    st.rerun()

# ---------------- RELATÓRIO ----------------
if not df.empty:
    st.subheader("📋 Lançamentos")

    for i, row in df.iterrows():
        c1, c2, c3, c4, c5, c6 = st.columns([2, 3, 2, 2, 2, 1])
        c1.write(pd.to_datetime(row["data"]).date())
        c2.write(row["descricao"])
        c3.write(row["tipo"])
        c4.write(f"R$ {float(row['valor']):.2f}")
        c5.write(row["categoria"])
        if c6.button("❌", key=f"del_{i}"):
            df = df.drop(i)
            df.to_csv(ARQUIVO_CLIENTE, index=False)
            st.rerun()

    st.subheader("📊 Resumo")

    receitas = df[df["tipo"] == "Receita"]["valor"].astype(float).sum()
    despesas = df[df["tipo"] == "Despesa"]["valor"].astype(float).sum()
    saldo = receitas - despesas

    c1, c2, c3 = st.columns(3)
    c1.metric("Receitas", f"R$ {receitas:,.2f}")
    c2.metric("Despesas", f"R$ {despesas:,.2f}")
    c3.metric("Saldo", f"R$ {saldo:,.2f}")

    st.subheader("⬇️ Baixar Excel")

    excel_path = BASE_PATH / "relatorio.xlsx"
    df.to_excel(excel_path, index=False)

    with open(excel_path, "rb") as f:
        st.download_button(
            "Download Excel",
            data=f,
            file_name=f"relatorio_{usuario}.xlsx"
        )

else:
    st.info("Nenhum lançamento ainda.")

# ---------------- LOGOUT ----------------
if st.button("Sair"):
    st.session_state.logado = False
    st.session_state.usuario = None
    st.rerun()
