import streamlit as st
import sqlite3
import pandas as pd
import re
from datetime import datetime
from PIL import Image
import io
import plotly.express as px


# Configuração da página
st.set_page_config(page_title="FISPA - Fiscalização e Pavimentação", layout="wide")

# Função para validar CPF
def validar_cpf(cpf):
    cpf = re.sub(r'\D', '', cpf)  # Remove caracteres não numéricos
    return len(cpf) == 11 and cpf.isdigit()

# Função para salvar imagem no banco
def salvar_imagem(imagem):
    """Converte uma imagem em bytes para armazenamento no banco de dados."""
    buf = io.BytesIO()
    if imagem.mode != "RGB":
        imagem = imagem.convert("RGB")
    imagem.save(buf, format="JPEG", quality=85)
    return buf.getvalue()

# Conectar ao banco de dados
def conectar_banco():
    return sqlite3.connect("sistema.db", check_same_thread=False)

# Criar a tabela no banco de dados
conn = conectar_banco()
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS sistema (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT NOT NULL,
    nome TEXT NOT NULL,
    cpf TEXT NOT NULL,
    telefone TEXT NOT NULL,
    bairro TEXT NOT NULL,
    endereco TEXT NOT NULL,
    comentario TEXT,
    imagem BLOB,
    status TEXT DEFAULT 'Em Aberto' CHECK(status IN ('Em Aberto', 'Em Andamento', 'Concluído'))
)
''')
conn.commit()
conn.close()

# Interface do Streamlit
st.title("FISPA - Fiscalização e Pavimentação")

# Menu de navegação
menu = st.sidebar.radio("Menu", ["Início", "Requerimento", "Dashboard", "Exportar CSV", "Status"])

# ================================Tela Início============================
if menu == "Início":
    st.header("Bem-vindo ao Sistema FISPA!")
    st.image("img/coordenador.jpg", caption="Coordenador", width=600)
    st.write("Use o menu ao lado para navegar pelo sistema.")

# ====================================Tela Requerimento=================================
elif menu == "Requerimento":
    st.header("Formulário de Requerimento")

    nome = st.text_input("Nome")
    cpf = st.text_input("CPF")
    telefone = st.text_input("Telefone")
    bairro = st.selectbox("Bairro", ["Aldeia da Paz", "Centro", "Parque das Rosas", "Vila União", "Outros"])
    endereco = st.text_input("Endereço")
    comentario = st.text_area("Comentário")
    imagem_file = st.file_uploader("Imagem", type=["jpg", "jpeg", "png"])

    if st.button("Salvar"):
        erro_msg = []

        # Validação dos campos obrigatórios
        if not nome:
            erro_msg.append("Nome é obrigatório")
        if not cpf or not validar_cpf(cpf):
            erro_msg.append("CPF inválido")
        if not telefone:
            erro_msg.append("Telefone é obrigatório")
        if not bairro:
            erro_msg.append("Bairro é obrigatório")
        if not endereco:
            erro_msg.append("Endereço é obrigatório")
        if not imagem_file:
            erro_msg.append("Imagem é obrigatória")

        # Exibir erro se algum campo estiver incorreto
        if erro_msg:
            st.error("⚠️ Erros encontrados:\n" + "\n".join(erro_msg))
        else:
            # Processar a imagem
            imagem = Image.open(imagem_file)
            imagem_bytes = salvar_imagem(imagem)

            # Inserir dados no banco de dados
            data_atual = datetime.now().strftime("%d/%m/%Y às %H:%M")
            conn = conectar_banco()
            cursor = conn.cursor()

            try:
                cursor.execute('''
                INSERT INTO sistema (data, nome, cpf, telefone, bairro, endereco, comentario, imagem)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (data_atual, nome, cpf, telefone, bairro, endereco, comentario, imagem_bytes))
                conn.commit()
                st.success("✅ Dados inseridos com sucesso!")
            except Exception as e:
                st.error(f"Erro ao salvar no banco de dados: {e}")
            finally:
                conn.close()


# ===================Tela Dashboard===========================================
elif menu == "Dashboard":
    st.header("📊 Dashboard Interativo")

    # 🔹 Gráfico de Barras - Quantidade de Requerimentos por Status
    st.subheader("📌 Quantidade de Requerimentos por Status")
    conn = conectar_banco()
    status_data = pd.read_sql_query("SELECT status, COUNT(*) as quantidade FROM sistema GROUP BY status", conn)
    conn.close()

    # Definição de cores para cada status
    status_colors = {
        "Em Aberto": "red",
        "Em Andamento": "orange",
        "Concluído": "green"
    }
    
    # Criar gráfico de barras verticais com cores personalizadas
    fig_status = px.bar(
        status_data, 
        x="status", 
        y="quantidade", 
        color="status",
        color_discrete_map=status_colors,
        text="quantidade",
        title="Distribuição de Status dos Requerimentos"
    )
    fig_status.update_layout(xaxis_title="Status", yaxis_title="Quantidade")
    st.plotly_chart(fig_status)

    # 🔹 Gráfico de Barras Horizontais - Requerimentos por Bairro
    st.subheader("🏠 Requerimentos por Bairro")
    conn = conectar_banco()
    bairro_data = pd.read_sql_query("SELECT bairro, COUNT(*) as quantidade FROM sistema GROUP BY bairro", conn)
    conn.close()

    fig_bairro = px.bar(
        bairro_data, 
        x="quantidade", 
        y="bairro", 
        orientation="h", 
        text="quantidade",
        color="quantidade",
        color_continuous_scale="blues",
        title="Quantidade de Requerimentos por Bairro"
    )
    fig_bairro.update_layout(xaxis_title="Quantidade", yaxis_title="Bairro")
    st.plotly_chart(fig_bairro)

    # 🔹 Ranking de Usuários que Mais Contribuíram
    st.subheader("🏆 Top 10 Usuários que Mais Enviaram Requerimentos")
    conn = conectar_banco()
    ranking_data = pd.read_sql_query("""
        SELECT nome, cpf, COUNT(*) as total_requerimentos 
        FROM sistema 
        GROUP BY cpf
        ORDER BY total_requerimentos DESC 
        LIMIT 10
    """, conn)
    conn.close()

    # Exibir tabela do ranking
    st.dataframe(ranking_data)

    # Criar gráfico de ranking
    fig_ranking = px.bar(
        ranking_data, 
        x="total_requerimentos", 
        y="nome", 
        orientation="h", 
        text="total_requerimentos",
        title="Top 10 Usuários com Mais Requerimentos",
        color="total_requerimentos",
        color_continuous_scale="oranges"
    )
    fig_ranking.update_layout(xaxis_title="Número de Requerimentos", yaxis_title="Usuário")
    st.plotly_chart(fig_ranking)

# Tela Status
elif menu == "Status":
    st.header("Atualizar Status")

    conn = conectar_banco()
    data = pd.read_sql_query("SELECT id, data, nome, bairro, status FROM sistema", conn)
    conn.close()

    if not data.empty:
        st.dataframe(data)
        ids_disponiveis = data["id"].tolist()
        id_atualizar = st.selectbox("Selecione o ID para atualizar", ids_disponiveis) if ids_disponiveis else None
        novo_status = st.selectbox("Novo Status", ["Em Aberto", "Em Andamento", "Concluído"])

        if id_atualizar and st.button("Atualizar Status"):
            conn = conectar_banco()
            cursor = conn.cursor()
            cursor.execute("UPDATE sistema SET status = ? WHERE id = ?", (novo_status, id_atualizar))
            conn.commit()
            conn.close()
            st.success("✅ Status atualizado com sucesso!")
    else:
        st.warning("Nenhum registro encontrado.")
