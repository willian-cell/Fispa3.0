import streamlit as st
import sqlite3
import pandas as pd
import re
import io
from datetime import datetime
from PIL import Image
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

# Função para conectar ao banco de dados
def conectar_banco():
    return sqlite3.connect("sistema.db", check_same_thread=False)

# Criar tabela no banco de dados (se não existir)
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
menu = st.sidebar.radio("Menu", ["Início", "Requerimento", "Dashboard", "Status ADM", "Baixar Dados"])

# =============================== Tela Início ==============================
if menu == "Início":
    st.header("Bem-vindo ao Sistema FISPA!")
    st.image("img/coordenador.jpg", caption="Coordenador", width=600)
    st.write("Use o menu ao lado para navegar pelo sistema.")

# ============================== Tela Requerimento ==============================
elif menu == "Requerimento":
    st.header("📌 Formulário de Requerimento")

    nome = st.text_input("Nome")
    cpf = st.text_input("CPF")
    telefone = st.text_input("Telefone")
    bairro = st.selectbox("Bairro", ["Aldeia da Paz", "Centro", "Parque das Rosas", "Vila União", "Outros"])
    endereco = st.text_input("Endereço")
    comentario = st.text_area("Comentário")
    imagem_file = st.file_uploader("Imagem", type=["jpg", "jpeg", "png"])

    if st.button("Salvar"):
        erro_msg = []

        if not nome:
            erro_msg.append("Nome é obrigatório.")
        if not cpf or not validar_cpf(cpf):
            erro_msg.append("CPF inválido.")
        if not telefone:
            erro_msg.append("Telefone é obrigatório.")
        if not endereco:
            erro_msg.append("Endereço é obrigatório.")
        if not imagem_file:
            erro_msg.append("Imagem é obrigatória.")

        if erro_msg:
            st.error("⚠️ Erros encontrados:\n" + "\n".join(erro_msg))
        else:
            imagem = Image.open(imagem_file)
            imagem_bytes = salvar_imagem(imagem)

            data_atual = datetime.now().strftime("%d/%m/%Y às %H:%M")
            conn = conectar_banco()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sistema (data, nome, cpf, telefone, bairro, endereco, comentario, imagem)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (data_atual, nome, cpf, telefone, bairro, endereco, comentario, imagem_bytes))
            conn.commit()
            conn.close()
            st.success("✅ Requerimento salvo com sucesso!")

# ============================== Tela Dashboard ==============================
elif menu == "Dashboard":
    st.header("📊 Dashboard Interativo")

    conn = conectar_banco()
    status_data = pd.read_sql_query("SELECT status, COUNT(*) as quantidade FROM sistema GROUP BY status", conn)
    bairro_data = pd.read_sql_query("SELECT bairro, COUNT(*) as quantidade FROM sistema GROUP BY bairro", conn)
    ranking_data = pd.read_sql_query("""
        SELECT nome, COUNT(*) as total_requerimentos 
        FROM sistema 
        GROUP BY nome
        ORDER BY total_requerimentos DESC 
        LIMIT 10
    """, conn)
    conn.close()

    st.subheader("📌 Quantidade de Requerimentos por Status")
    fig_status = px.bar(status_data, x="status", y="quantidade", text="quantidade", title="Status dos Requerimentos")
    st.plotly_chart(fig_status)

    st.subheader("🏠 Requerimentos por Bairro")
    fig_bairro = px.bar(bairro_data, x="quantidade", y="bairro", text="quantidade", title="Requerimentos por Bairro")
    st.plotly_chart(fig_bairro)

    st.subheader("🏆 Top 10 Usuários")
    st.dataframe(ranking_data)
    fig_ranking = px.bar(ranking_data, x="total_requerimentos", y="nome", text="total_requerimentos", title="Usuários com Mais Requerimentos")
    st.plotly_chart(fig_ranking)

# ============================== Tela Baixar Dados ==============================
elif menu == "Baixar Dados":
    st.header("📥 Baixar Dados")

    conn = conectar_banco()
    data = pd.read_sql_query("SELECT * FROM sistema", conn)
    conn.close()

    if not data.empty:
        csv = data.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Baixar CSV", csv, "dados_fispa.csv", "text/csv")


# ============================== Tela Status ADM ==============================
elif menu == "Status ADM":
    senha = st.text_input("🔑 Digite a senha de acesso", type="password")

    if senha == "adm777":
        st.header("📌 Atualizar Status e Visualizar Imagem")

        # Conectar ao banco e buscar dados
        conn = conectar_banco()
        data = pd.read_sql_query("SELECT id, data, nome, bairro, status, imagem FROM sistema", conn)
        conn.close()

        if not data.empty:
            data_display = data.drop(columns=["imagem"])  # Ocultar imagens na tabela
            st.dataframe(data_display)  # Exibir tabela geral dos requerimentos

            # Selecionar um ID
            id_selecionado = st.selectbox("🔍 Selecione um ID para visualizar detalhes", [""] + data["id"].astype(str).tolist())

            # Verificar se um ID foi selecionado
            if id_selecionado:
                id_selecionado = int(id_selecionado)  # Converter para inteiro

                # Criar botão para mostrar detalhes do cadastro
                if st.button("📄 Mostrar Cadastro"):
                    # Filtrar os dados do requerimento selecionado
                    requerimento = data[data["id"] == id_selecionado].iloc[0]

                    # Exibir os detalhes do requerimento selecionado
                    st.subheader(f"📄 Detalhes do Requerimento #{id_selecionado}")
                    st.write(f"🗓 **Data:** {requerimento['data']}")
                    st.write(f"👤 **Nome:** {requerimento['nome']}")
                    st.write(f"🏠 **Bairro:** {requerimento['bairro']}")
                    st.write(f"📌 **Status:** {requerimento['status']}")

                    # Botão para mostrar a imagem
                    if st.button(f"📷 Mostrar Imagem do Requerimento"):
                        if requerimento["imagem"]:
                            st.image(io.BytesIO(requerimento["imagem"]), caption=f"Imagem do Requerimento #{id_selecionado}")
                        else:
                            st.warning("⚠️ Nenhuma imagem disponível para este requerimento.")

                    # Opção para atualizar o status do requerimento
                    novo_status = st.selectbox("📍 Novo Status", ["Em Aberto", "Em Andamento", "Concluído"])

                    if st.button("✅ Atualizar Status"):
                        conn = conectar_banco()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE sistema SET status = ? WHERE id = ?", (novo_status, id_selecionado))
                        conn.commit()
                        conn.close()
                        st.success(f"✅ Status do Requerimento #{id_selecionado} atualizado para '{novo_status}'!")
    else:
        st.error("🔒 Senha incorreta.")
