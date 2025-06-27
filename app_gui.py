import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime
import streamlit.components.v1 as components
import plotly.graph_objects as go

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

# Inicializa os dados
if "insumos" not in st.session_state:
    st.session_state.insumos = pd.DataFrame(columns=["Nome", "Unidade", "Preço Unitário", "Cor"])

if "produtos" not in st.session_state:
    st.session_state.produtos = pd.DataFrame(columns=["Produto", "Insumo", "Quantidade", "Cor"])

# Tabs
tab1, tab2, tab3 = st.tabs(["📦 Cadastro de Insumos", "💪 Cadastro de Produtos", "💰 Montagem de Orçamento"])


# --- Aba 1: Cadastro de Insumos ---
with tab1:
    st.header("Cadastro de Insumos")
    with st.form("form_insumo"):
        nome_insumo = st.text_input("Nome do Insumo")

        unidades_padrao = ["M²", "Litro (L)", "kg", "Unidade"]
        unidade = st.selectbox("Unidade de Medida", options=unidades_padrao + ["Outro..."], index=0)
        if unidade == "Outro...":
            unidade = st.text_input("Informe a nova unidade:")

        preco = st.number_input("Preço Unitário", min_value=0.0, step=0.1)
        cor = st.text_input("Cor", value="Preto")
        submitted = st.form_submit_button("Adicionar Insumo")
        if submitted:
            st.session_state.insumos.loc[len(st.session_state.insumos)] = [nome_insumo, unidade, preco, cor]
            st.success("Insumo adicionado!")

    st.write("### Insumos cadastrados")
    for i, row in st.session_state.insumos.iterrows():
        col1, col2, col3 = st.columns([8, 1, 1])
        with col1:
            st.markdown(f"**{row['Nome'].strip()}** — {row['Unidade']}, R$ {row['Preço Unitário']:.2f}, Cor: {row['Cor']}")
        with col2:
            if st.button("✏️", key=f"edit_insumo_{i}"):
                st.session_state["edit_index"] = i
        with col3:
            if st.button("❌", key=f"del_insumo_{i}"):
                st.session_state.insumos.drop(index=i, inplace=True)
                st.session_state.insumos.reset_index(drop=True, inplace=True)
                st.experimental_rerun()

    if "edit_index" in st.session_state:
        idx = st.session_state["edit_index"]
        row = st.session_state.insumos.loc[idx]
        st.info(f"Editando: {row['Nome'].strip()}")
        novo_preco = st.number_input("Novo Preço Unitário", value=float(row["Preço Unitário"]), min_value=0.0, step=0.5, key="novo_preco_input")
        nova_cor = st.text_input("Nova Cor", value=row["Cor"], key="nova_cor_input")
        if st.button("Salvar Preço Atualizado"):
            st.session_state.insumos.at[idx, "Preço Unitário"] = novo_preco
            st.session_state.insumos.at[idx, "Cor"] = nova_cor
            del st.session_state["edit_index"]
            st.success("Atualização feita com sucesso!")
            st.experimental_rerun()
        if st.button("Cancelar Edição"):
            del st.session_state["edit_index"]

# --- Aba 2: Cadastro de Produtos ---
with tab2:
    st.header("Cadastro de Produtos")

    st.subheader("🨚 Armário Padrão (automático)")
    altura = st.slider("Altura (cm)", 30, 250, 180)
    largura = st.slider("Largura (cm)", 30, 250, 100)
    profundidade = st.slider("Profundidade (cm)", 30, 100, 60)
    h, l, p = altura / 100, largura / 100, profundidade / 100
    area_total = (l * p) + 2 * (p * h) + 2 * (l * h)
    st.write(f"🔨 Área total estimada de chapa de madeira: **{area_total:.2f} m²**")

    fig = go.Figure(data=[
        go.Mesh3d(
            x=[0, l, l, 0, 0, l, l, 0],
            y=[0, 0, p, p, 0, 0, p, p],
            z=[0, 0, 0, 0, h, h, h, h],
            color='lightblue',
            opacity=0.4,
            i=[0, 0, 0, 4, 4, 4, 1, 1, 5, 2, 2, 6],
            j=[1, 2, 3, 5, 6, 7, 5, 6, 6, 6, 3, 7],
            k=[2, 3, 0, 6, 7, 4, 6, 7, 2, 3, 0, 4],
            flatshading=True
        )
    ])
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), scene=dict(
        xaxis_title="Largura (m)",
        yaxis_title="Profundidade (m)",
        zaxis_title="Altura (m)",
    ))
    st.plotly_chart(fig, use_container_width=True)

    cor_armario = st.selectbox("Cor da Chapa", st.session_state.insumos["Cor"].unique())

    if st.button("Adicionar Armário com essas dimensões"):
        existe_insumo = st.session_state.insumos[
            (st.session_state.insumos["Nome"] == "Chapa de Madeira") &
            (st.session_state.insumos["Cor"] == cor_armario)
        ]
        if not existe_insumo.empty:
            st.session_state.produtos.loc[len(st.session_state.produtos)] = [
                "Armário", "Chapa de Madeira", area_total, cor_armario
            ]
            st.success("Armário adicionado com sucesso ao orçamento!")
        else:
            st.warning("Não foi encontrado o insumo 'Chapa de Madeira' com essa cor. Cadastre antes de adicionar.")

    st.subheader("Cadastrar Produto Manualmente")
    st.session_state.insumos["InsumoCompleto"] = st.session_state.insumos["Nome"] + " - " + st.session_state.insumos["Cor"]
    with st.form("form_produto"):
        nome_produto = st.text_input("Nome do Produto")
        insumo_sel = st.selectbox("Escolher Insumo (com Cor)", st.session_state.insumos["InsumoCompleto"])
        cor_sel = insumo_sel.split(" - ")[-1]
        qtd_insumo = st.number_input("Quantidade do Insumo", min_value=0.1, step=0.1)
        submitted_prod = st.form_submit_button("Adicionar ao Produto")
        if submitted_prod:
            nome_base, cor_base = insumo_sel.split(" - ")
            st.session_state.produtos.loc[len(st.session_state.produtos)] = [nome_produto, nome_base, qtd_insumo, cor_base]
            st.success("Componente adicionado ao produto!")

    st.write("### Produtos cadastrados")
    for i, row in st.session_state.produtos.iterrows():
        col1, col2 = st.columns([10, 1])
        with col1:
            st.markdown(f"**{row['Produto']}** → {row['Quantidade']}x {row['Insumo']} ({row['Cor']})")
        with col2:
            if st.button("❌", key=f"del_prod_{i}"):
                st.session_state.produtos.drop(index=i, inplace=True)
                st.session_state.produtos.reset_index(drop=True, inplace=True)
                st.experimental_rerun()

# --- Aba 3: Montagem de Orçamento ---
with tab3:
    st.header("Montar Orçamento")
    clientes = st.text_input("Nome do Cliente")
    orcamento = []
    produtos_disponiveis = st.session_state.produtos["Produto"].unique()

    for produto in produtos_disponiveis:
        qtd = st.number_input(f"Quantidade de '{produto}'", min_value=0, step=1, key=produto)
        if qtd > 0:
            orcamento.append({"Produto": produto, "Quantidade": qtd})

    imposto = st.number_input("Imposto (%)", min_value=0.0, value=10.0)
    margem = st.number_input("Margem de Lucro (%)", min_value=0.0, value=30.0)

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
            pdf.cell(200, 10, txt=f"Cor: {item['Cor']}", ln=True)
            pdf.cell(200, 10, txt=f"Preço Unitário: R$ {item['Unitario']:.2f}", ln=True)
            pdf.cell(200, 10, txt=f"Subtotal: R$ {item['Subtotal']:.2f}", ln=True)
            total_geral += item['Subtotal']
        pdf.ln(10)
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(200, 10, txt=f"Total Geral: R$ {total_geral:.2f}", ln=True)
        nome_arquivo = f"orcamento_{cliente.lower().replace(' ', '_')}.pdf"
        pdf.output(nome_arquivo)
        return nome_arquivo

    if st.button("Gerar Orçamento em PDF") and clientes and orcamento:
        detalhes = []
        for item in orcamento:
            comp = st.session_state.produtos[st.session_state.produtos["Produto"] == item["Produto"]]
            custo_total = 0
            for _, row in comp.iterrows():
                preco_insumo = st.session_state.insumos.loc[
                    (st.session_state.insumos["Nome"] == row["Insumo"]) &
                    (st.session_state.insumos["Cor"] == row["Cor"]), "Preço Unitário"
                ].values[0]
                custo_total += preco_insumo * row["Quantidade"]
            custo_unit = custo_total * (1 + imposto / 100) * (1 + margem / 100)
            subtotal = custo_unit * item["Quantidade"]
            cor = comp.iloc[0]["Cor"]
            detalhes.append({"Produto": item["Produto"], "Quantidade": item["Quantidade"], "Unitario": custo_unit, "Subtotal": subtotal, "Cor": cor})

        pdf_path = gerar_pdf(clientes, detalhes)
        with open(pdf_path, "rb") as f:
            st.download_button("📄 Baixar PDF do Orçamento", f, file_name=pdf_path)
