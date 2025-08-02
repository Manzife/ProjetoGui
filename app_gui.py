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
# Inicialização de Estados e Insumos Padrão
# ==========================================================
# -------------------------
# Inicialização de Estados
# -------------------------
if "chapas" not in st.session_state:
    st.session_state.chapas = pd.DataFrame(columns=[
        "Cor", "Espessura (m)", "Largura (m)", "Altura (m)", "Preço (R$)", "Usa Retalhos"
    ])

if "produtos" not in st.session_state:
    st.session_state.produtos = pd.DataFrame(columns=["Produto", "Área Total (m²)", "Chapas Usadas", "Imagem"])

if "extras" not in st.session_state:
    st.session_state.extras = pd.DataFrame(columns=["Item", "Quantidade", "Preço Unitário (R$)"])

# Adiciona insumos padrão se não houver chapas
if st.session_state.chapas.empty:
    espessuras_padrao = [0.006, 0.015, 0.018, 0.025]  # 6mm, 15mm, 18mm, 25mm
    cores_padrao = [
        {"cor": "Branco", "usa_ret": True, "preco": 200.0},
        {"cor": "Colorida", "usa_ret": False, "preco": 250.0}
    ]

    for cor_info in cores_padrao:
        for esp in espessuras_padrao:
            st.session_state.chapas.loc[len(st.session_state.chapas)] = {
                "Cor": cor_info["cor"],
                "Espessura (m)": esp,
                "Largura (m)": 1.6,
                "Altura (m)": 2.2,
                "Preço (R$)": cor_info["preco"],
                "Usa Retalhos": cor_info["usa_ret"]
            }
# ==========================================================
# Tabs
# ==========================================================
tab1, tab2, tab3 = st.tabs(["📦 Cadastro de Chapas", "💪 Montagem de Produtos", "💰 Orçamento Final"])

# ==========================================================
# Aba 1: Cadastro de Chapas com Espessuras e Retalhos
# ==========================================================
with tab1:
    st.header("Cadastro de Chapas de Madeira")

    espessuras_padrao = [0.006, 0.015, 0.018, 0.025]  # 6mm, 15mm, 18mm, 25mm
    labels_padrao = [f"{int(e*1000)} mm" for e in espessuras_padrao]

    with st.form("form_chapa"):
        cor = st.text_input("Cor da Chapa", value="Branco")

        # --- Espessura com opção personalizada ---
        escolha_esp = st.selectbox("Espessura da Chapa", labels_padrao + ["Outra..."], index=1)
        if escolha_esp == "Outra...":
            espessura = st.number_input("Informe nova espessura (em metros)", min_value=0.001, max_value=0.1, step=0.001)
        else:
            idx = labels_padrao.index(escolha_esp)
            espessura = espessuras_padrao[idx]

        largura = st.number_input("Largura da Chapa (m)", min_value=0.5, max_value=3.0, step=0.1, value=1.6)
        altura = st.number_input("Altura da Chapa (m)", min_value=0.5, max_value=3.0, step=0.1, value=2.2)
        preco = st.number_input("Preço da Chapa (R$)", min_value=0.0, step=1.0, value=200.0)

        # --- Novo seletor para uso de retalhos ---
        usa_ret = st.selectbox("Usa Retalhos?", ["Sim", "Não"], index=0)

        submitted = st.form_submit_button("Adicionar Chapa")
        if submitted:
            nova_chapa = {
                "Cor": cor,
                "Espessura (m)": espessura,
                "Largura (m)": largura,
                "Altura (m)": altura,
                "Preço (R$)": preco,
                "Usa Retalhos": True if usa_ret == "Sim" else False
            }
            st.session_state.chapas.loc[len(st.session_state.chapas)] = nova_chapa
            st.success("Chapa adicionada com sucesso!")

    # --- Visualizar insumos cadastrados ---
    st.write("### Chapas cadastradas")
    if not st.session_state.chapas.empty:
        df_exibir = st.session_state.chapas.copy()
        df_exibir["Espessura"] = (df_exibir["Espessura (m)"]*1000).round(0).astype(int).astype(str) + " mm"
        df_exibir["Usa Retalhos"] = df_exibir["Usa Retalhos"].apply(lambda x: "Sim" if x else "Não")
        st.dataframe(df_exibir[["Cor","Espessura","Largura (m)","Altura (m)","Preço (R$)","Usa Retalhos"]])

# ==========================================================
# Aba 2: Montagem de Produtos com Retalhos
# ==========================================================
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

    # Escolher se quer visualizar em 3D
    ver_3d = st.checkbox("Visualizar móvel em 3D", value=True)

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
                format_func=lambda i: (
                    f"{chapas_cadastradas.loc[i,'Cor']} "
                    f"- {chapas_cadastradas.loc[i,'Espessura (m)']*1000:.0f}mm "
                    f"- Retalhos: {'Sim' if chapas_cadastradas.loc[i,'Usa Retalhos'] else 'Não'}"
                )
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
        color_map = {
            "Madeira": "#a0522d", "Branco": "#F0F0F0", "Preto": "#111111",
            "Cinza": "#888888", "Colorida": "#ff6f61"
        }

        for face in faces_selecionadas:
            idx = chapa_por_face[face]
            chapa = chapas_cadastradas.loc[idx]
            esp = float(chapa["Espessura (m)"])
            area_chapa = float(chapa["Largura (m)"]) * float(chapa["Altura (m)"])
            usa_retalhos = bool(chapa["Usa Retalhos"])
            color_hex = color_map.get(chapa["Cor"], "#a0522d")

            # Dimensões da chapa (dx,dy,dz) e posição (x,y,z)
            if face in ["Base", "Topo"]:
                dx, dy, dz = largura, profundidade, esp
            elif face in ["Frente", "Traseira"]:
                dx, dy, dz = largura, esp, altura
            elif face in ["Lateral Esquerda", "Lateral Direita"]:
                dx, dy, dz = esp, profundidade, altura

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

            # Cria face 3D se opção estiver ativa
            if ver_3d:
                faces.append(create_chapa(x, y, z, dx, dy, dz, color_hex))

            # --- Cálculo de consumo com regra de retalhos ---
            area_face = dx * dy
            qtd_chapas_real = area_face / area_chapa

            if usa_retalhos:
                # Cobra só pela área efetiva
                qtd_cobrada = round(qtd_chapas_real, 2)
                custo_total = area_face * (chapa["Preço (R$)"] / area_chapa)
            else:
                # Cobra chapa inteira
                qtd_cobrada = math.ceil(qtd_chapas_real)
                custo_total = qtd_cobrada * chapa["Preço (R$)"]

            consumo.append({
                "Face": face,
                "Cor": chapa["Cor"],
                "Espessura (m)": esp,
                "Área da Face (m²)": round(area_face, 3),
                "Qtd Chapas Real": round(qtd_chapas_real, 2),
                "Qtd Chapas Cobrada": qtd_cobrada,
                "Custo Total (R$)": round(custo_total, 2),
                "Usa Retalhos": "Sim" if usa_retalhos else "Não"
            })

        # --- Visualização 3D opcional ---
        if ver_3d and faces:
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
            if ver_3d and faces:
                pio.write_image(fig, img_path, width=800, height=600)
            else:
                img_path = None

            st.session_state.produtos.loc[len(st.session_state.produtos)] = [
                "Móvel 3D Real",
                df_consumo["Área da Face (m²)"].sum(),
                df_consumo.to_dict(),
                img_path
            ]
            st.success("Produto salvo com sucesso!")
            if img_path:
                st.image(img_path)
        
# ==========================================================
# Aba 3: Orçamento Final
# ==========================================================
with tab3:
    st.header("Orçamento Final")

    # Garante que a chave existe
    if "produtos" not in st.session_state:
        st.session_state.produtos = pd.DataFrame(columns=["Produto", "Área Total (m²)", "Chapas Usadas", "Imagem"])

    # Exibe produtos
    if not st.session_state.produtos.empty:
        st.write("Produtos já salvos:")
        st.dataframe(st.session_state.produtos[["Produto","Área Total (m²)","Imagem"]])
    else:
        st.info("Nenhum produto salvo ainda.")

