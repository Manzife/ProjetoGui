import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime
import plotly.graph_objects as go

st.set_page_config(page_title="Orçamento Marcenaria", layout="centered")
st.title("🌳 Sistema de Orçamento para Marcenaria")

# Inicializa os dados
if "insumos" not in st.session_state or st.session_state.insumos.empty:
    st.session_state.insumos = pd.DataFrame(columns=["Nome", "Unidade", "Preço Unitário", "Cor"])
else:
    st.session_state.insumos = st.session_state.insumos.reindex(columns=["Nome", "Unidade", "Preço Unitário", "Cor"])

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
            novo_insumo = {"Nome": nome_insumo, "Unidade": unidade, "Preço Unitário": preco, "Cor": cor}
            st.session_state.insumos = pd.concat([st.session_state.insumos, pd.DataFrame([novo_insumo])], ignore_index=True)
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
    st.subheader("🪚 Armário Padrão (sem tampa)")

    altura = st.slider("Altura (cm)", 30, 250, 180) / 100
    largura = st.slider("Largura (cm)", 30, 250, 100) / 100
    profundidade = st.slider("Profundidade (cm)", 30, 100, 60) / 100

    cores_disponiveis = {
        "Branco": "#F0F0F0",
        "Preto": "#111111",
        "Cinza": "#888888",
        "Madeira": "#a0522d"
    }

    cor_frente = st.selectbox("Cor da Frente", list(cores_disponiveis.keys()), index=3)
    cor_tras = st.selectbox("Cor de Trás", list(cores_disponiveis.keys()), index=3)
    cor_esq = st.selectbox("Cor da Lateral Esquerda", list(cores_disponiveis.keys()), index=3)
    cor_dir = st.selectbox("Cor da Lateral Direita", list(cores_disponiveis.keys()), index=3)
    cor_fundo = st.selectbox("Cor do Fundo", list(cores_disponiveis.keys()), index=3)

    # --- Função para criar faces corretas ---
    def face_mesh(x_range, y_range, z_range, color_hex):
        x = [x_range[0], x_range[1], x_range[1], x_range[0], x_range[0], x_range[1], x_range[1], x_range[0]]
        y = [y_range[0], y_range[0], y_range[1], y_range[1], y_range[0], y_range[0], y_range[1], y_range[1]]
        z = [z_range[0], z_range[0], z_range[0], z_range[0], z_range[1], z_range[1], z_range[1], z_range[1]]
        return go.Mesh3d(
            x=x, y=y, z=z,
            color=color_hex,
            opacity=1.0,
            flatshading=True
        )
    
    # --- Faces do armário (sem tampa) ---
    faces = [
        # Fundo
        face_mesh([0, largura], [0, profundidade], [0, 0.02], cores_disponiveis[cor_fundo]),
        # Lateral Esquerda
        face_mesh([0, 0.02], [0, profundidade], [0, altura], cores_disponiveis[cor_esq]),
        # Lateral Direita
        face_mesh([largura-0.02, largura], [0, profundidade], [0, altura], cores_disponiveis[cor_dir]),
        # Traseira
        face_mesh([0, largura], [profundidade-0.02, profundidade], [0, altura], cores_disponiveis[cor_tras]),
        # Frente (borda)
        face_mesh([0, largura], [0, 0.02], [0, altura], cores_disponiveis[cor_frente])
    ]
    
    fig = go.Figure(data=faces)
    fig.update_layout(
        scene=dict(
            xaxis_title="Largura (m)",
            yaxis_title="Profundidade (m)",
            zaxis_title="Altura (m)",
            aspectmode="data"
        ),
        margin=dict(l=0, r=0, t=0, b=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    area_total = 2 * (altura * profundidade) + 2 * (altura * largura) + (largura * profundidade)
    st.write(f"🔨 Área total estimada de chapa de madeira: **{area_total:.2f} m²**")

    cor_predominante = cor_frente
    if st.button("Adicionar Armário com essas características"):
        existe_insumo = st.session_state.insumos[
            (st.session_state.insumos["Nome"] == "Chapa de Madeira") &
            (st.session_state.insumos["Cor"] == cor_predominante)
        ]
        if not existe_insumo.empty:
            st.session_state.produtos.loc[len(st.session_state.produtos)] = [
                "Armário", "Chapa de Madeira", area_total, cor_predominante
            ]
            st.success("Armário adicionado com sucesso ao orçamento!")
        else:
            st.warning("Não foi encontrado o insumo 'Chapa de Madeira' com essa cor. Cadastre antes de adicionar.")
