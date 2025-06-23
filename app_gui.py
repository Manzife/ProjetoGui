import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime
import streamlit.components.v1 as components

st.set_page_config(page_title="Orçamento Marcenaria", layout="centered")
st.title("🌳 Sistema de Orçamento para Marcenaria")

# CSS para mostrar botão de exclusão apenas ao passar o mouse
st.markdown("""
    <style>
    .delete-btn {
        visibility: hidden;
    }
    .stDataFrame tbody tr:hover .delete-btn {
        visibility: visible;
    }
    </style>
""", unsafe_allow_html=True)

# Inicializa os dados se não existirem
if "insumos" not in st.session_state:
    st.session_state.insumos = pd.DataFrame(columns=["Nome", "Unidade", "Preço Unitário"])

if "produtos" not in st.session_state:
    st.session_state.produtos = pd.DataFrame(columns=["Produto", "Insumo", "Quantidade"])

# 1. Cadastro de Insumos
st.header("1. Cadastro de Insumos")
with st.form("form_insumo"):
    nome_insumo = st.text_input("Nome do Insumo")
    unidade = st.text_input("Unidade de Medida")
    preco = st.number_input("Preço Unitário", min_value=0.0, step=0.1)
    submitted = st.form_submit_button("Adicionar Insumo")
    if submitted:
        st.session_state.insumos.loc[len(st.session_state.insumos)] = [nome_insumo, unidade, preco]
        st.success("Insumo adicionado!")

# Mostrar tabela com botão de exclusão
st.write("### Insumos cadastrados")
for i, row in st.session_state.insumos.iterrows():
    col1, col2, col3 = st.columns([8, 1, 1])
    with col1:
        st.markdown(f"**{row['Nome'].strip()}** — {row['Unidade']}, R$ {row['Preço Unitário']:.2f}")
    with col2:
        if st.button("✏️", key=f"edit_insumo_{i}"):
            st.session_state[f"edit_index"] = i
    with col3:
        if st.button("❌", key=f"del_insumo_{i}"):
            st.session_state.insumos.drop(index=i, inplace=True)
            st.session_state.insumos.reset_index(drop=True, inplace=True)
            st.experimental_rerun()

# Campo de edição de preço
if "edit_index" in st.session_state:
    idx = st.session_state["edit_index"]
    row = st.session_state.insumos.loc[idx]
    st.info(f"Editando: {row['Nome'].strip()}")
    novo_preco = st.number_input("Novo Preço Unitário", value=float(row["Preço Unitário"]), min_value=0.0, step=0.5, key="novo_preco_input")
    if st.button("Salvar Preço Atualizado"):
        st.session_state.insumos.at[idx, "Preço Unitário"] = novo_preco
        del st.session_state["edit_index"]
        st.success("Preço atualizado com sucesso!")
        st.experimental_rerun()
    if st.button("Cancelar Edição"):
        del st.session_state["edit_index"]

# 2. Cadastro de Produtos
st.header("2. Cadastro de Produtos")
with st.form("form_produto"):
    nome_produto = st.text_input("Nome do Produto")
    insumo_sel = st.selectbox("Escolher Insumo", st.session_state.insumos["Nome"])
    qtd_insumo = st.number_input("Quantidade do Insumo", min_value=0.1, step=0.1)
    submitted_prod = st.form_submit_button("Adicionar ao Produto")
    if submitted_prod:
        st.session_state.produtos.loc[len(st.session_state.produtos)] = [nome_produto, insumo_sel, qtd_insumo]
        st.success("Componente adicionado ao produto!")

st.write("### Produtos cadastrados")
for i, row in st.session_state.produtos.iterrows():
    col1, col2 = st.columns([10, 1])
    with col1:
        st.markdown(f"**{row['Produto']}** → {row['Quantidade']}x {row['Insumo']}")
    with col2:
        if st.button("❌", key=f"del_prod_{i}"):
            st.session_state.produtos.drop(index=i, inplace=True)
            st.session_state.produtos.reset_index(drop=True, inplace=True)
            st.experimental_rerun()

# 3. Montagem de Orçamento
st.header("3. Montar Orçamento")
clientes = st.text_input("Nome do Cliente")
orcamento = []
produtos_disponiveis = st.session_state.produtos["Produto"].unique()

for produto in produtos_disponiveis:
    qtd = st.number_input(f"Quantidade de '{produto}'", min_value=0, step=1, key=produto)
    if qtd > 0:
        orcamento.append({"Produto": produto, "Quantidade": qtd})

imposto = st.number_input("Imposto (%)", min_value=0.0, value=10.0)
margem = st.number_input("Margem de Lucro (%)", min_value=0.0, value=30.0)

# Botão para gerar PDF
def gerar_pdf(cliente, itens):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Orçamento - {cliente}", ln=True, align="C")

    total_geral = 0
    for item in itens:
        pdf.ln(8)
        pdf.cell(200, 10, txt=f"Produto: {item['Produto']}", ln=True)
        pdf.cell(200, 10, txt=f"Quantidade: {item['Quantidade']}", ln=True)
        pdf.cell(200, 10, txt=f"Preço Unitário: R$ {item['Unitario']:.2f}", ln=True)
        pdf.cell(200, 10, txt=f"Subtotal: R$ {item['Subtotal']:.2f}", ln=True)
        total_geral += item['Subtotal']

    pdf.ln(10)
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, txt=f"Total Geral: R$ {total_geral:.2f}", ln=True)

    nome_arquivo = f"orcamento_{cliente.lower().replace(' ', '_')}.pdf"
    pdf.output(nome_arquivo)
    return nome_arquivo

# Cálculo do orçamento final
if st.button("Gerar Orçamento em PDF") and clientes and orcamento:
    detalhes = []
    for item in orcamento:
        comp = st.session_state.produtos[st.session_state.produtos["Produto"] == item["Produto"]]
        custo_total = 0
        for _, row in comp.iterrows():
            preco_insumo = st.session_state.insumos.loc[st.session_state.insumos["Nome"] == row["Insumo"], "Preço Unitário"].values[0]
            custo_total += preco_insumo * row["Quantidade"]
        custo_unit = custo_total * (1 + imposto / 100) * (1 + margem / 100)
        subtotal = custo_unit * item["Quantidade"]
        detalhes.append({"Produto": item["Produto"], "Quantidade": item["Quantidade"], "Unitario": custo_unit, "Subtotal": subtotal})

    pdf_path = gerar_pdf(clientes, detalhes)
    with open(pdf_path, "rb") as f:
        st.download_button("📄 Baixar PDF do Orçamento", f, file_name=pdf_path)
