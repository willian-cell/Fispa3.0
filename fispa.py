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
    bairro = st.selectbox("Bairro", [
        "Aldeia da Paz", "Área Rural de Santo Antônio do Descoberto", "Beira Rio", "Beira Rio II", "Centro",
        "Conjunto Habitacional Conceição Gomes Rabelo", "Fazenda Capoeirinha", "Jardim Ana Beatriz I",
        "Jardim Ana Beatriz II", "Jardim de Alá", "Mansões Bittencourt", "Meu Lote Minha Casa",
        "Parque das Rosas", "Parque Estrela Dalva XI", "Parque Estrela Dalva XI-A", "Parque Estrela Dalva XII",
        "Parque Estrela Dalva XIII", "Parque Estrela Dalva XIV", "Parque Estrela Dalva XV", "Parque Estrela Dalva XVI",
        "Parque Estrela Dalva XVII", "Parque Santo Antônio", "Residencial Mangueiras", "Setor de Indústria",
        "Vila Betel", "Vila Cortes", "Vila Esperança", "Vila Maria Auxiliadora", "Vila Montes Claros",
        "Vila Montes Claros II", "Vila Paraíso I", "Vila Paraíso II", "Vila Paraíso III", "Vila Parque",
        "Vila Raio de Luz", "Vila São Luiz", "Vila São Luiz II", "Vila União", "Outros"
    ])
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
    status_data = pd.read_sql_query("SELECT status, COUNT(*) as Quantidade FROM sistema GROUP BY status", conn)
    bairro_data = pd.read_sql_query("SELECT bairro, COUNT(*) as Quantidade FROM sistema GROUP BY bairro", conn)
    ranking_data = pd.read_sql_query("""
        SELECT nome, COUNT(*) as total_requerimentos 
        FROM sistema 
        GROUP BY nome
        ORDER BY total_requerimentos DESC 
        LIMIT 10
    """, conn)
    conn.close()

    # 🔹 Gráfico de Barras - Quantidade de Requerimentos por Status
    st.subheader("📌 Quantidade de Requerimentos por Status")
    conn = conectar_banco()
    status_data = pd.read_sql_query("SELECT status, COUNT(*) as Quantidade FROM sistema GROUP BY status", conn)
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
        y="Quantidade", 
        color="status",
        color_discrete_map=status_colors,
        text="Quantidade",
        title="Distribuição de Status dos Requerimentos"
    )
    fig_status.update_layout(xaxis_title="Status", yaxis_title="Quantidade")
    st.plotly_chart(fig_status)

    st.subheader("🏠 Requerimentos por Bairro")
    fig_bairro = px.bar(bairro_data, x="Quantidade", y="bairro", text="Quantidade", title="Requerimentos por Bairro")
    st.plotly_chart(fig_bairro)

    st.subheader("🏆 Top 10 Usuários")
    st.dataframe(ranking_data)
    fig_ranking = px.bar(ranking_data, x="total_requerimentos", y="nome", text="total_requerimentos", title="Usuários com Mais Requerimentos")
    st.plotly_chart(fig_ranking)

# ============================== Tela Baixar Dados ==============================
elif menu == "Baixar Dados":
    st.header("📥 Baixar Dados")

    conn = conectar_banco()
    query = "SELECT id, data, nome, cpf, telefone, bairro, endereco, comentario, status FROM sistema"
    data = pd.read_sql_query(query, conn)
    conn.close()

    if not data.empty:
        # 🔹 Renomeando colunas para melhor legibilidade
        data.rename(columns={
            "id": "ID",
            "data": "Data do Requerimento",
            "nome": "Nome do Requerente",
            "cpf": "CPF",
            "telefone": "Telefone",
            "bairro": "Bairro",
            "endereco": "Endereço",
            "comentario": "Comentário",
            "status": "Status"
        }, inplace=True)

        # 🔹 Ordenando os dados por ID (do mais recente para o mais antigo)
        data = data.sort_values(by="ID", ascending=False)

        # 🔹 Convertendo para CSV formatado (separador ; para Excel)
        csv = data.to_csv(index=False, sep=";", encoding="utf-8").encode("utf-8")

        # 🔹 Botão para download
        st.download_button(
            label="📥 Baixar CSV Formatado",
            data=csv,
            file_name="dados_fispa.csv",
            mime="text/csv"
        )
    else:
        st.warning("⚠️ Nenhum dado disponível para download.")

# ============================== Tela Status ADM ==============================
elif menu == "Status ADM":
    st.header("🔑 Painel Administrativo - Gerenciamento de Requerimentos")

    # Solicitação de senha para acesso
    senha = st.text_input("🔐 Insira a senha de acesso:", type="password")

    # Senha correta para acesso administrativo
    senha_correta = "adm777"

    if senha == senha_correta:
        st.success("✅ Acesso autorizado!")
        
        # Conectar ao banco e buscar dados
        conn = conectar_banco()
        query = "SELECT id, data, nome, bairro, status, imagem FROM sistema"
        data = pd.read_sql_query(query, conn)
        conn.close()

        if not data.empty:
            # Ocultar a coluna de imagem na exibição da tabela
            data_display = data.drop(columns=["imagem"], errors="ignore")
            st.subheader("📋 Requerimentos Cadastrados")
            st.dataframe(data_display)

            # Selecionar um ID para visualização detalhada
            id_selecionado = st.selectbox(
                "🔍 Selecione um requerimento para detalhes:", 
                [""] + data["id"].astype(str).tolist()
            )

            if id_selecionado:
                id_selecionado = int(id_selecionado)  # Converter para inteiro

                # Filtrar o requerimento correspondente ao ID selecionado
                requerimento = data.query("id == @id_selecionado").copy()

                if not requerimento.empty:
                    requerimento = requerimento.iloc[0]  # Obter a primeira linha correspondente

                    # Exibir detalhes do requerimento
                    with st.expander(f"📄 Detalhes do Requerimento #{id_selecionado}", expanded=True):
                        st.write(f"🗓 **Data:** {requerimento['data']}")
                        st.write(f"👤 **Nome:** {requerimento['nome']}")
                        st.write(f"🏠 **Bairro:** {requerimento['bairro']}")
                        st.write(f"📌 **Status:** {requerimento['status']}")

                        # Exibir imagem associada ao requerimento, se disponível
                        if requerimento["imagem"]:
                            st.image(io.BytesIO(requerimento["imagem"]), caption=f"📷 Imagem do Requerimento #{id_selecionado}")
                        else:
                            st.warning("⚠️ Nenhuma imagem disponível para este requerimento.")

                    # Seção para atualização do status
                    novo_status = st.selectbox("📍 Atualizar Status:", ["Em Aberto", "Em Andamento", "Concluído"])

                    if st.button("✅ Confirmar Atualização"):
                        conn = conectar_banco()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE sistema SET status = ? WHERE id = ?", (novo_status, id_selecionado))
                        conn.commit()
                        conn.close()
                        st.success(f"✅ Status do Requerimento #{id_selecionado} atualizado para '{novo_status}'!")
                        st.rerun()
                else:
                    st.warning(f"⚠️ Nenhum requerimento encontrado para o ID {id_selecionado}.")
        else:
            st.warning("⚠️ Nenhum requerimento cadastrado no sistema.")
    else:
        st.error("🔒 Acesso negado! Senha incorreta.")
