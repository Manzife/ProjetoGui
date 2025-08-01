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
with tab2:
    st.header("Montagem de Móveis")
    st.subheader("📐 Caixa Retangular")

    # Dimensões do móvel
    altura = st.slider("Altura (cm)", 30, 250, 180) / 100
    largura = st.slider("Largura (cm)", 30, 250, 100) / 100
    profundidade = st.slider("Profundidade (cm)", 30, 100, 60) / 100

    st.write(f"Dimensões: {largura:.2f} x {profundidade:.2f} x {altura:.2f} m")

    # Escolha da chapa para cada face
    faces_opcoes = ["Fundo", "Lateral Esquerda", "Lateral Direita", "Topo", "Base", "Frente", "Traseira"]
    faces_selecionadas = st.multiselect("Faces que o móvel terá", faces_opcoes, default=["Base","Lateral Esquerda","Lateral Direita","Traseira","Topo"])

    chapas_cadastradas = st.session_state.chapas
    if chapas_cadastradas.empty:
        st.warning("⚠️ Cadastre chapas na Aba 1 antes de montar produtos.")
    else:
        chapa_por_face = {}
        for face in faces_selecionadas:
            chapa_por_face[face] = st.selectbox(
                f"Chapa para {face}",
                options=chapas_cadastradas.index,
                format_func=lambda i: f"{chapas_cadastradas.loc[i,'Cor']} - {chapas_cadastradas.loc[i,'Espessura (m)']}m"
            )

        # Cálculo de consumo de chapas
        consumo = []
        faces_areas = {
            "Fundo": largura * profundidade,
            "Topo": largura * profundidade,
            "Base": largura * profundidade,
            "Lateral Esquerda": altura * profundidade,
            "Lateral Direita": altura * profundidade,
            "Frente": altura * largura,
            "Traseira": altura * largura
        }

        for face in faces_selecionadas:
            idx = chapa_por_face[face]
            chapa = chapas_cadastradas.loc[idx]
            area_face = faces_areas[face]
            area_chapa = chapa["Largura (m)"] * chapa["Altura (m)"]
            qtd_chapas = math.ceil(area_face / area_chapa)

            consumo.append({
                "Face": face,
                "Cor": chapa["Cor"],
                "Espessura (m)": chapa["Espessura (m)"],
                "Área da Face (m²)": area_face,
                "Área Chapa (m²)": area_chapa,
                "Qtd Chapas": qtd_chapas,
                "Custo Total (R$)": qtd_chapas * chapa["Preço (R$)"]
            })

        df_consumo = pd.DataFrame(consumo)
        st.write("### Consumo de Chapas")
        st.dataframe(df_consumo)

        # Visualização 3D simplificada (como blocos)
        def face_mesh(x_range, y_range, z_range, color_hex):
            x = [x_range[0], x_range[1], x_range[1], x_range[0], x_range[0], x_range[1], x_range[1], x_range[0]]
            y = [y_range[0], y_range[0], y_range[1], y_range[1], y_range[0], y_range[0], y_range[1], y_range[1]]
            z = [z_range[0], z_range[0], z_range[0], z_range[0], z_range[1], z_range[1], z_range[1], z_range[1]]
            return go.Mesh3d(x=x, y=y, z=z, color=color_hex, opacity=1.0, flatshading=True)

        faces = []
        for face in faces_selecionadas:
            cor = chapas_cadastradas.loc[chapa_por_face[face], "Cor"]
            color_map = {
                "Madeira": "#a0522d",
                "Branco": "#F0F0F0",
                "Preto": "#111111",
                "Cinza": "#888888"
            }
            color_hex = color_map.get(cor, "#a0522d")

            if face == "Base":
                faces.append(face_mesh([0, largura], [0, profundidade], [0, 0.02], color_hex))
            elif face == "Topo":
                faces.append(face_mesh([0, largura], [0, profundidade], [altura-0.02, altura], color_hex))
            elif face == "Fundo":
                faces.append(face_mesh([0, largura], [0, 0.02], [0, altura], color_hex))
            elif face == "Lateral Esquerda":
                faces.append(face_mesh([0, 0.02], [0, profundidade], [0, altura], color_hex))
            elif face == "Lateral Direita":
                faces.append(face_mesh([largura-0.02, largura], [0, profundidade], [0, altura], color_hex))
            elif face == "Frente":
                faces.append(face_mesh([0, largura], [profundidade-0.02, profundidade], [0, altura], color_hex))
            elif face == "Traseira":
                faces.append(face_mesh([0, largura], [0, 0.02], [0, altura], color_hex))

        fig = go.Figure(data=faces)
        fig.update_layout(scene=dict(aspectmode="data"), margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig, use_container_width=True)

        # Salvar produto
        if st.button("Salvar Produto com Imagem"):
            img_path = f"produto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            pio.write_image(fig, img_path, width=800, height=600)

            st.session_state.produtos.loc[len(st.session_state.produtos)] = [
                "Móvel Personalizado",
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
