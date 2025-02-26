import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from PIL import Image
import io

# Configuração da página
st.set_page_config(page_title="FISPA - Fiscalização e Pavimentação", layout="wide")

# Conexão com o banco de dados
conn = sqlite3.connect("sistema.db")
cursor = conn.cursor()

# Criar tabela no banco de dados se não existir
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

# Função para salvar imagem no banco com melhorias
def salvar_imagem(imagem):
    """Converte uma imagem em bytes com compressão."""
    buf = io.BytesIO()
    # Converter para RGB caso a imagem não seja RGB
    if imagem.mode != "RGB":
        imagem = imagem.convert("RGB")
    # Salvar a imagem em formato JPEG com qualidade 85 para reduzir tamanho
    imagem.save(buf, format="JPEG", quality=85)
    # Retornar bytes da imagem
    return buf.getvalue()

# Interface do Streamlit
st.title("FISPA - Fiscalização e Pavimentação")

# Menu de navegação
menu = st.sidebar.radio("Menu", ["Início", "Requerimento", "Dashboard", "Exportar CSV", "Status"])

# Tela Início
if menu == "Início":
    st.header("Bem-vindo ao Sistema FISPA!")
    st.image("coordenador.jpg", caption="Coordenador", width=600)
    st.write("Use o menu ao lado para navegar pelo sistema.")

# Tela Requerimento
elif menu == "Requerimento":
    
    st.header("Formulário de Requerimento")
    nome = st.text_input("Nome")
    cpf = st.text_input("CPF")
    telefone = st.text_input("Telefone")
    bairro = st.selectbox("Bairro", [
        "Aldeia da Paz", "Centro", "Parque das Rosas", "Vila União", "Outros"
    ])
    endereco = st.text_input("Endereço")
    comentario = st.text_area("Comentário")
    imagem_file = st.file_uploader("Imagem", type=["jpg", "jpeg", "png"])

    if st.button("Salvar"):
        if nome and cpf and telefone and bairro and endereco and imagem_file:
            imagem = Image.open(imagem_file)
            imagem_bytes = salvar_imagem(imagem)
            data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute('''
            INSERT INTO sistema (data, nome, cpf, telefone, bairro, endereco, comentario, imagem)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (data_atual, nome, cpf, telefone, bairro, endereco, comentario, imagem_bytes))
            conn.commit()
            st.success("Dados inseridos com sucesso!")
        else:
            st.error("Todos os campos devem ser preenchidos!")

# Tela Dashboard
elif menu == "Dashboard":
    st.header("Dashboard")

    # Gráfico de barras por status
    status_data = pd.read_sql_query("SELECT status, COUNT(*) as quantidade FROM sistema GROUP BY status", conn)
    st.bar_chart(status_data.set_index("status"))

    # Gráfico de pizza por bairro
    bairro_data = pd.read_sql_query("SELECT bairro, COUNT(*) as quantidade FROM sistema GROUP BY bairro", conn)
    st.write("Requerimentos por Bairro")
    st.dataframe(bairro_data)

# Tela Exportar CSV
elif menu == "Exportar CSV":
    st.header("Exportar Dados para CSV")
    data = pd.read_sql_query("SELECT * FROM sistema", conn)
    if not data.empty:
        csv = data.to_csv(index=False).encode('utf-8')
        st.download_button("Baixar CSV", data=csv, file_name="dados_fispa.csv", mime="text/csv")
    else:
        st.warning("Nenhum dado disponível para exportar.")

# Tela Status
elif menu == "Status":
    st.header("Atualizar Status")
    data = pd.read_sql_query("SELECT id, data, nome, bairro, status FROM sistema", conn)
    st.dataframe(data)

    id_atualizar = st.number_input("ID do registro a atualizar", min_value=1)
    novo_status = st.selectbox("Novo Status", ["Em Aberto", "Em Andamento", "Concluído"])

    if st.button("Atualizar Status"):
        cursor.execute("UPDATE sistema SET status = ? WHERE id = ?", (novo_status, id_atualizar))
        conn.commit()
        st.success("Status atualizado com sucesso!")
