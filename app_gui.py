import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime
import math
import os

st.set_page_config(page_title="Orçamento Marcenaria", layout="centered")
st.title("🌳 Sistema de Orçamento para Marcenaria")

# ==========================================================
# Inicialização de Estados
# ==========================================================
if "chapas" not in st.session_state:
    st.session_state.chapas = pd.DataFrame(columns=["Cor", "Espessura (m)", "Largura (m)", "Altura (m)", "Preço (R$)"])

if "produtos" not in st.session_state:
    st.session_state.produtos = pd.DataFrame(columns=["Produto", "Área Total (m²)", "Chapas Usadas", "Imagem"])

if "extras" not in st.session_state:
    st.session_state.extras = pd.DataFrame(columns=["Item", "Quantidade", "Preço Unitário (R$)"])

# ==========================================================
# Tabs
# ==========================================================
tab1, tab2, tab3 = st.tabs(["📦 Cadastro de Chapas", "💪 Montagem de Produtos", "💰 Orçamento Final"])

# ==========================================================
# Aba 1: Cadastro de Chapas
# ==========================================================
with tab1:
    st.header("Cadastro de Chapas de Madeira")

    with st.form("form_chapa"):
        cor = st.text_input("Cor da Chapa", value="Madeira")
        espessura = st.number_input("Espessura (m)", min_value=0.01, max_value=0.1, step=0.01, value=0.02)
        largura = st.number_input("Largura da Chapa (m)", min_value=0.5, max_value=3.0, step=0.1, value=1.6)
        altura = st.number_input("Altura da Chapa (m)", min_value=0.5, max_value=3.0, step=0.1, value=2.2)
        preco = st.number_input("Preço da Chapa (R$)", min_value=0.0, step=1.0, value=180.0)
        submitted = st.form_submit_button("Adicionar Chapa")
        if submitted:
            nova_chapa = {"Cor": cor, "Espessura (m)": espessura, "Largura (m)": largura, "Altura (m)": altura, "Preço (R$)": preco}
            st.session_state.chapas.loc[len(st.session_state.chapas)] = nova_chapa
            st.success("Chapa adicionada com sucesso!")

    st.write("### Chapas cadastradas")
    st.dataframe(st.session_state.chapas)

# ==========================================================
# Aba 2: Montagem de Produtos
# ==========================================================
# --- Aba 2: Montagem de Produtos (chapas 3D reais) ---
with tab2:
    st.header("Montagem de Móveis")
    st.subheader("📐 Caixa Retangular")

    # Dimensões do móvel
    altura = st.slider("Altura (cm)", 30, 250, 180) / 100
    largura = st.slider("Largura (cm)", 30, 250, 100) / 100
    profundidade = st.slider("Profundidade (cm)", 30, 100, 60) / 100

    st.write(f"Dimensões: {largura:.2f} x {profundidade:.2f} x {altura:.2f} m")

    # Escolha das faces
    faces_opcoes = ["Base", "Topo", "Lateral Esquerda", "Lateral Direita", "Frente", "Traseira"]
    faces_selecionadas = st.multiselect(
        "Faces que o móvel terá",
        faces_opcoes,
        default=["Base", "Lateral Esquerda", "Lateral Direita", "Traseira", "Topo"]
    )

    # Verifica se há chapas cadastradas
    chapas_cadastradas = st.session_state.chapas
    if chapas_cadastradas.empty:
        st.warning("⚠️ Cadastre chapas na Aba 1 antes de montar produtos.")
    else:
        # Escolha de chapa para cada face
        chapa_por_face = {}
        for face in faces_selecionadas:
            chapa_por_face[face] = st.selectbox(
                f"Chapa para {face}",
                options=chapas_cadastradas.index,
                format_func=lambda i: f"{chapas_cadastradas.loc[i,'Cor']} - {chapas_cadastradas.loc[i,'Espessura (m)']}m"
            )

        # --- Função para criar chapa 3D ---
        def create_chapa(x, y, z, dx, dy, dz, color_hex):
            X = [x, x+dx, x+dx, x, x, x+dx, x+dx, x]
            Y = [y, y, y+dy, y+dy, y, y, y+dy, y+dy]
            Z = [z, z, z, z, z+dz, z+dz, z+dz, z+dz]
            I = [0,0,0,1,1,2,3,4,4,4,5,5]
            J = [1,2,4,2,5,3,0,5,6,7,6,1]
            K = [2,3,5,5,6,0,4,6,7,6,2,2]
            return go.Mesh3d(x=X, y=Y, z=Z, i=I, j=J, k=K, color=color_hex, opacity=1.0)

        # --- Criação das chapas e cálculo de consumo ---
        faces = []
        consumo = []
        color_map = {"Madeira": "#a0522d", "Branco": "#F0F0F0", "Preto": "#111111", "Cinza": "#888888"}

        for face in faces_selecionadas:
            idx = chapa_por_face[face]
            chapa = chapas_cadastradas.loc[idx]
            esp = float(chapa["Espessura (m)"])
            area_chapa = float(chapa["Largura (m)"]) * float(chapa["Altura (m)"])
            color_hex = color_map.get(chapa["Cor"], "#a0522d")

            # Dimensões da face
            if face in ["Base", "Topo"]:
                dx, dy, dz = largura, profundidade, esp
            elif face in ["Frente", "Traseira"]:
                dx, dy, dz = largura, esp, altura
            elif face in ["Lateral Esquerda", "Lateral Direita"]:
                dx, dy, dz = esp, profundidade, altura

            # Posição da face
            if face == "Base":
                x, y, z = 0, 0, 0
            elif face == "Topo":
                x, y, z = 0, 0, altura-esp
            elif face == "Frente":
                x, y, z = 0, profundidade-esp, 0
            elif face == "Traseira":
                x, y, z = 0, 0, 0
            elif face == "Lateral Esquerda":
                x, y, z = 0, 0, 0
            elif face == "Lateral Direita":
                x, y, z = largura-esp, 0, 0

            # Adiciona face ao 3D
            faces.append(create_chapa(x, y, z, dx, dy, dz, color_hex))

            # Consumo e custo
            area_face = dx * dy
            qtd_chapas = math.ceil(area_face / area_chapa)
            consumo.append({
                "Face": face,
                "Cor": chapa["Cor"],
                "Espessura (m)": esp,
                "Área da Face (m²)": round(area_face, 3),
                "Qtd Chapas": qtd_chapas,
                "Custo Total (R$)": qtd_chapas * chapa["Preço (R$)"]
            })

        # --- Visualização 3D do móvel ---
        fig = go.Figure(data=faces)
        fig.update_layout(scene=dict(aspectmode="data"), margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig, use_container_width=True)

        # --- Tabela de Consumo ---
        df_consumo = pd.DataFrame(consumo)
        st.write("### Consumo de Chapas")
        st.dataframe(df_consumo)

        # --- Salvar Produto com Imagem ---
        if st.button("Salvar Produto com Imagem"):
            img_path = f"produto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            pio.write_image(fig, img_path, width=800, height=600)

            st.session_state.produtos.loc[len(st.session_state.produtos)] = [
                "Móvel 3D Real",
                df_consumo["Área da Face (m²)"].sum(),
                df_consumo.to_dict(),
                img_path
            ]
            st.success("Produto salvo com sucesso!")
            st.image(img_path)

# ==========================================================
# Aba 3: Orçamento Final
# ==========================================================
with tab3:
    st.header("Orçamento Final")
    if not st.session_state.produtos.empty:
        st.write("Produtos já salvos:")
        st.dataframe(st.session_state.produtos[["Produto","Área Total (m²)","Imagem"]])
    else:
        st.info("Nenhum produto salvo ainda.")
