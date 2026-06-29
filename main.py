import streamlit as st
import pandas as pd
from azure.storage.blob import BlobServiceClient
import os
import pymssql
import uuid
import json
from dotenv import load_dotenv

load_dotenv()
# Configurações do Azure Blob Storage e SQL Server
blobConnectionString = os.getenv("BLOB_CONNECTION_STRING")
blobContainerName = os.getenv("BLOB_CONTAINER_NAME")
blobAccountName = os.getenv("BLOB_ACCOUNT_NAME")

SQL_SERVER = os.getenv("SQL_SERVER")
SQL_DATABASE = os.getenv("SQL_DATABASE")
SQL_USER = os.getenv("SQL_USER")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")


st.title("Cadastro de Produtos")

# Formulário de cadastro de produtos
product_name = st.text_input("Nome do Produto")
product_price = st.number_input("Preço do Produto", min_value=0.0, step=0.01, format="%.2f")
product_description = st.text_area("Descrição do Produto")
product_image = st.file_uploader("Imagem do Produto", type=["jpg", "jpeg", "png"])


if st.button("Cadastrar Produto"):
    if product_name and product_price and product_description and product_image:
        # sobe a imagem para o Azure Blob Storage
        blob_service_client = BlobServiceClient.from_connection_string(blobConnectionString)
        container_client = blob_service_client.get_container_client(blobContainerName)
        blob_name = f"{uuid.uuid4()}.jpg"
        blob_client = container_client.get_blob_client(blob_name)
        
        blob_client.upload_blob(product_image, overwrite=True)
        image_url = f"https://{blobAccountName}.blob.core.windows.net/{blobContainerName}/{blob_name}"
        
        # coloca os dados do produto no banco de dados SQL Server
        conn = pymssql.connect(server=SQL_SERVER, user=SQL_USER, password=SQL_PASSWORD, database=SQL_DATABASE)
        cursor = conn.cursor()
        
        insert_query = """
            INSERT INTO Produtos (nome, preco, descricao, imagem_url)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_query, (product_name, product_price, product_description, image_url))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        st.success("Produto cadastrado com sucesso!")
    else:
        st.error("Por favor, preencha todos os campos e faça o upload da imagem.")

#botão para listar produtos cadastrados e trazer os dados do banco de dados SQL Server
list_products = st.button("Listar Produtos")


if list_products:
    conn = pymssql.connect(server=SQL_SERVER, user=SQL_USER, password=SQL_PASSWORD, database=SQL_DATABASE)
    cursor = conn.cursor()
    
    select_query = "SELECT nome, preco, descricao, imagem_url FROM Produtos"
    cursor.execute(select_query)
    
    products = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    if products:
        # 1. Definimos quantos produtos queremos por linha (3 é o padrão perfeito para Desktop)
        num_cols = 3
        
        # 2. Fatiamos a lista total de produtos em "pacotes" de 3 em 3
        for i in range(0, len(products), num_cols):
            cols = st.columns(num_cols)
            produtos_da_linha = products[i : i + num_cols]
            
            for j, product in enumerate(produtos_da_linha):
                with cols[j]:
                    # 3. Bônus de UI: cria um "card" com borda ao redor de cada produto!
                    with st.container(border=True):
                        st.subheader(product[0])
                        st.write(f"**Preço:** R$ {product[1]:.2f}")
                        st.write(f"{product[2]}")
                        
                        # Trocamos largura fixa por "ocupe 100% da coluna"
                        st.image(product[3], use_container_width=True)
    else:
        st.info("Nenhum produto cadastrado.")

delete_product = st.button("Deletar Produto")

# Substituímos o botão por um container expansível
with st.expander("🗑️ Deletar um Produto"):
    product_id_to_delete = st.number_input("ID do Produto a ser deletado", min_value=1, step=1, value=None)
    
    if st.button("Confirmar Deleção"):
        if product_id_to_delete:
            conn = pymssql.connect(server=SQL_SERVER, user=SQL_USER, password=SQL_PASSWORD, database=SQL_DATABASE)
            cursor = conn.cursor()
            
            delete_query = "DELETE FROM Produtos WHERE id = %s"
            cursor.execute(delete_query, (product_id_to_delete,))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            st.success(f"Produto de ID {product_id_to_delete} deletado com sucesso!")
        else:
            st.error("Por favor, insira o ID do produto a ser deletado.")