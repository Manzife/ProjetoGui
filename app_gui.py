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
# --- Aba 2: Cadastro de Produtos (versão avançada) ---
with tab2:
    st.header("Cadastro de Produtos")
    st.subheader("🪚 Armário Personalizado")

    # --- Dimensões do armário ---
    altura = st.slider("Altura (cm)", 30, 250, 180) / 100
    largura = st.slider("Largura (cm)", 30, 250, 100) / 100
    profundidade = st.slider("Profundidade (cm)", 30, 100, 60) / 100

    # --- Escolha das cores ---
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

    # --- Faces e espessura ---
    faces_opcoes = ["Fundo", "Lateral Esquerda", "Lateral Direita", "Traseira", "Frente"]
    faces_selecionadas = st.multiselect(
        "Selecione as faces para montar",
        faces_opcoes,
        default=faces_opcoes
    )

    espessuras = {}
    for face in faces_selecionadas:
        espessuras[face] = st.number_input(
            f"Espessura da {face} (m)",
            min_value=0.01,
            max_value=0.1,
            value=0.02,
            step=0.01
        )

    # --- Função para criar faces ---
    def face_mesh(x_range, y_range, z_range, color_hex):
        x = [x_range[0], x_range[1], x_range[1], x_range[0], x_range[0], x_range[1], x_range[1], x_range[0]]
        y = [y_range[0], y_range[0], y_range[1], y_range[1], y_range[0], y_range[0], y_range[1], y_range[1]]
        z = [z_range[0], z_range[0], z_range[0], z_range[0], z_range[1], z_range[1], z_range[1], z_range[1]]
        return go.Mesh3d(x=x, y=y, z=z, color=color_hex, opacity=1.0, flatshading=True)

    # --- Criação das faces selecionadas ---
    faces = []
    area_por_espessura = {}

    for face in faces_selecionadas:
        esp = espessuras[face]

        if face == "Fundo":
            faces.append(face_mesh([0, largura], [0, profundidade], [0, esp], cores_disponiveis[cor_fundo]))
            area_por_espessura[esp] = area_por_espessura.get(esp, 0) + (largura * profundidade)

        elif face == "Lateral Esquerda":
            faces.append(face_mesh([0, esp], [0, profundidade], [0, altura], cores_disponiveis[cor_esq]))
            area_por_espessura[esp] = area_por_espessura.get(esp, 0) + (altura * profundidade)

        elif face == "Lateral Direita":
            faces.append(face_mesh([largura-esp, largura], [0, profundidade], [0, altura], cores_disponiveis[cor_dir]))
            area_por_espessura[esp] = area_por_espessura.get(esp, 0) + (altura * profundidade)

        elif face == "Traseira":
            faces.append(face_mesh([0, largura], [profundidade-esp, profundidade], [0, altura], cores_disponiveis[cor_tras]))
            area_por_espessura[esp] = area_por_espessura.get(esp, 0) + (largura * altura)

        elif face == "Frente":
            faces.append(face_mesh([0, largura], [0, esp], [0, altura], cores_disponiveis[cor_frente]))
            area_por_espessura[esp] = area_por_espessura.get(esp, 0) + (largura * altura)

    # --- Visualização 3D ---
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

    # --- Consumo de madeira por espessura ---
    df_madeira = pd.DataFrame([
        {"Espessura (m)": esp, 
         "Área Total (m²)": area, 
         "Chapas 2.2x1.6m": area / (2.2*1.6)}
        for esp, area in area_por_espessura.items()
    ])
    st.write("### Consumo de Madeira por Espessura")
    st.dataframe(df_madeira)

    # --- Itens extras ---
    if "extras" not in st.session_state:
        st.session_state.extras = pd.DataFrame(columns=["Item", "Quantidade", "Preço Unitário"])

    st.subheader("Outros Itens")
    with st.form("form_extra"):
        item = st.text_input("Nome do Item")
        qtd = st.number_input("Quantidade", min_value=1, step=1)
        preco_unit = st.number_input("Preço Unitário (R$)", min_value=0.0, step=0.1)
        add_extra = st.form_submit_button("Adicionar Item")
        if add_extra and item:
            st.session_state.extras.loc[len(st.session_state.extras)] = [item, qtd, preco_unit]

    st.write("Itens extras cadastrados:")
    st.dataframe(st.session_state.extras)

    # --- Salvar produto com imagem ---
    import plotly.io as pio
    import os

    if st.button("Salvar Produto com Imagem"):
        img_path = f"produto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        pio.write_image(fig, img_path, width=800, height=600)

        # Cadastro do produto
        cor_predominante = cor_frente
        st.session_state.produtos.loc[len(st.session_state.produtos)] = [
            "Armário Personalizado", "Chapa de Madeira", sum(area_por_espessura.values()), cor_predominante
        ]

        st.success(f"Produto salvo com imagem em {img_path}")
        st.image(img_path, caption="Pré-visualização do produto")
