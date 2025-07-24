import streamlit as st
import mysql.connector
import pandas as pd
import boto3
import hashlib
import io
# CONFIGURAÇÕES
DB_HOST = 'bmk6y39nfvstjjc20lge-mysql.services.clever-cloud.com'
DB_USER = 'umwmt7j24hze8gae'
DB_PASSWORD = 'MfmVrFw5mnGapQQqMUi1'
DB_NAME = 'bmk6y39nfvstjjc20lge'
AWS_ACCESS_KEY_ID = 'SUA_ACCESS_KEY'
AWS_SECRET_ACCESS_KEY = 'SUA_SECRET_KEY'
S3_BUCKET = 'rogerio-tcc-videos'

# ========== Funções utilitárias ==========

def get_conn():
    return mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def autentica_usuario(email, senha):
    conn = get_conn()
    cursor = conn.cursor()
    senha_hash = hash_password(senha)
    cursor.execute(
        "SELECT id, nome, tipo, morador_id FROM Usuario WHERE email=%s AND senha_hash=%s",
        (email, senha_hash)
    )
    usuario = cursor.fetchone()
    cursor.close()
    conn.close()
    return usuario  # (id, nome, tipo, morador_id) ou None

def cadastrar_usuario(nome, email, senha, tipo, morador_id=None):
    conn = get_conn()
    cursor = conn.cursor()
    senha_hash = hash_password(senha)
    cursor.execute(
        "INSERT INTO Usuario (nome, email, senha_hash, tipo, morador_id) VALUES (%s, %s, %s, %s, %s)",
        (nome, email, senha_hash, tipo, morador_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

# Cadastro básico
def cadastrar_morador(nome, documento):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Morador (nome, documento) VALUES (%s, %s)", (nome, documento))
    conn.commit()
    cursor.close()
    conn.close()

def cadastrar_localidade(morador_id, descricao, endereco):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Localidade (morador_id, descricao, endereco) VALUES (%s, %s, %s)", (morador_id, descricao, endereco))
    conn.commit()
    cursor.close()
    conn.close()

def cadastrar_comodo(localidade_id, nome):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Comodo (localidade_id, nome) VALUES (%s, %s)", (localidade_id, nome))
    conn.commit()
    cursor.close()
    conn.close()

def cadastrar_camera(comodo_id, identificador, status='ligada'):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Camera (comodo_id, identificador, status) VALUES (%s, %s, %s)", (comodo_id, identificador, status))
    conn.commit()
    cursor.close()
    conn.close()

def get_opcoes(tabela, campos, where=None):
    conn = get_conn()
    cursor = conn.cursor()
    query = f"SELECT {campos} FROM {tabela}" + (f" WHERE {where}" if where else "")
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

def get_cameras_com_localidade(morador_id=None):
    conn = get_conn()
    cursor = conn.cursor()
    if morador_id:
        cursor.execute("""
            SELECT ca.id, ca.identificador, co.nome, l.descricao
            FROM Camera ca
            JOIN Comodo co ON ca.comodo_id = co.id
            JOIN Localidade l ON co.localidade_id = l.id
            WHERE l.morador_id = %s
        """, (morador_id,))
    else:
        cursor.execute("""
            SELECT ca.id, ca.identificador, co.nome, l.descricao
            FROM Camera ca
            JOIN Comodo co ON ca.comodo_id = co.id
            JOIN Localidade l ON co.localidade_id = l.id
        """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows  # (camera_id, identificador, nome_comodo, localidade)

def get_camera_id(identificador):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM Camera WHERE identificador = %s", (identificador,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None

def processar_metrica(uploaded_file, camera_identificador):
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        camera_id = get_camera_id(camera_identificador)
        if not camera_id:
            st.error(f"Câmera {camera_identificador} não cadastrada!")
            return
        conn = get_conn()
        cursor = conn.cursor()
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO FrameMetrica (camera_id, frame_num, tempo_medio, media_geral, tamanho_pacote, classe_movimento_id, perda_pacote, foi_reclassificado)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                camera_id, int(row.get('frame_num', 1)), float(row.get('tempo_medio', 0)),
                float(row.get('media_geral', 0)), int(row.get('tamanho_pacote', 0)),
                int(row.get('classe_movimento_id', 1)), float(row.get('perda_pacote', 0)), False
            ))
        conn.commit()
        cursor.close()
        conn.close()
        st.success('Arquivo processado e métricas cadastradas!')
def registrar_video_no_banco(camera_id, caminho_s3):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Video (camera_id, caminho_s3) VALUES (%s, %s)",
        (camera_id, caminho_s3)
    )
    conn.commit()
    cursor.close()
    conn.close()
def consultar_videos(morador_id=None):
    conn = get_conn()
    cursor = conn.cursor()
    if morador_id:
        query = """
            SELECT v.id, v.caminho_s3, v.data_envio, ca.identificador, co.nome, l.descricao
            FROM Video v
            JOIN Camera ca ON v.camera_id = ca.id
            JOIN Comodo co ON ca.comodo_id = co.id
            JOIN Localidade l ON co.localidade_id = l.id
            WHERE l.morador_id = %s
            ORDER BY v.data_envio DESC
        """
        cursor.execute(query, (morador_id,))
    else:
        query = """
            SELECT v.id, v.caminho_s3, v.data_envio, ca.identificador, co.nome, l.descricao
            FROM Video v
            JOIN Camera ca ON v.camera_id = ca.id
            JOIN Comodo co ON ca.comodo_id = co.id
            JOIN Localidade l ON co.localidade_id = l.id
            ORDER BY v.data_envio DESC
        """
        cursor.execute(query)
    df = pd.DataFrame(cursor.fetchall(), columns=['ID', 'S3 Path', 'Data Envio', 'Câmera', 'Cômodo', 'Localidade'])
    cursor.close()
    conn.close()
    return df

def upload_video_s3(file, s3_path):
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    s3.upload_fileobj(file, S3_BUCKET, s3_path)
    return f"s3://{S3_BUCKET}/{s3_path}"
def registrar_alerta(camera_id, tipo, descricao):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Alerta (camera_id, tipo, descricao) VALUES (%s, %s, %s)",
        (camera_id, tipo, descricao)
    )
    conn.commit()
    cursor.close()
    conn.close()
def consultar_metricas(morador_id=None, camera_id=None):
    conn = get_conn()
    cursor = conn.cursor()
    query = """
        SELECT fm.id, fm.camera_id, fm.frame_num, fm.tempo_medio, fm.media_geral,
               fm.tamanho_pacote, fm.classe_movimento_id, fm.perda_pacote, fm.foi_reclassificado,
               ca.identificador, co.nome as comodo, l.descricao as localidade, m.nome as morador
        FROM FrameMetrica fm
        JOIN Camera ca ON fm.camera_id = ca.id
        JOIN Comodo co ON ca.comodo_id = co.id
        JOIN Localidade l ON co.localidade_id = l.id
        JOIN Morador m ON l.morador_id = m.id
    """
    filtros = []
    params = []
    if morador_id:
        filtros.append("l.morador_id = %s")
        params.append(morador_id)
    if camera_id:
        filtros.append("ca.id = %s")
        params.append(camera_id)
    if filtros:
        query += " WHERE " + " AND ".join(filtros)
    query += " ORDER BY fm.id DESC"
    cursor.execute(query, tuple(params))
    df = pd.DataFrame(cursor.fetchall(), columns=[
        'ID', 'Camera_ID', 'Frame', 'Tempo Médio', 'Média Geral', 'Tamanho Pacote',
        'Classe Movimento', 'Perda Pacote', 'Foi Reclassificado',
        'Identificador', 'Cômodo', 'Localidade', 'Morador'
    ])
    cursor.close()
    conn.close()
    return df
    
def consultar_alertas(morador_id=None):
    conn = get_conn()
    cursor = conn.cursor()
    if morador_id:
        query = """
            SELECT al.data_hora, al.tipo, al.descricao, ca.identificador, co.nome, l.descricao
            FROM Alerta al
            JOIN Camera ca ON al.camera_id = ca.id
            JOIN Comodo co ON ca.comodo_id = co.id
            JOIN Localidade l ON co.localidade_id = l.id
            WHERE l.morador_id = %s
            ORDER BY al.data_hora DESC
        """
        cursor.execute(query, (morador_id,))
    else:
        query = """
            SELECT al.data_hora, al.tipo, al.descricao, ca.identificador, co.nome, l.descricao
            FROM Alerta al
            JOIN Camera ca ON al.camera_id = ca.id
            JOIN Comodo co ON ca.comodo_id = co.id
            JOIN Localidade l ON co.localidade_id = l.id
            ORDER BY al.data_hora DESC
        """
        cursor.execute(query)
    df = pd.DataFrame(cursor.fetchall(), columns=['Data', 'Tipo', 'Descrição', 'Câmera', 'Cômodo', 'Localidade'])
    cursor.close()
    conn.close()
    return df
def monitorar_perda(morador_id=None, limiar_perda=0.1, janela_frames=100):
    conn = get_conn()
    cursor = conn.cursor()
    query = f"""
        SELECT camera_id, AVG(perda_pacote) as perda_media
        FROM FrameMetrica
        WHERE frame_num > (SELECT MAX(frame_num)-{janela_frames} FROM FrameMetrica)
        {"AND camera_id IN (SELECT ca.id FROM Camera ca JOIN Comodo co ON ca.comodo_id=co.id JOIN Localidade l ON co.localidade_id=l.id WHERE l.morador_id=%s)" if morador_id else ""}
        GROUP BY camera_id
    """
    cursor.execute(query, (morador_id,) if morador_id else ())
    results = cursor.fetchall()
    for camera_id, perda in results:
        if perda > limiar_perda:
            # Alerta + solicitar upload ao usuário
            registrar_alerta(camera_id, 'PERDA_PACOTE', f'Perda de pacote alta: {perda:.2%}')
            # Aqui você pode acionar upload automático ou solicitar permissão ao usuário (ver abaixo)
    cursor.close()
    conn.close()
def atualizar_classes_metricas(df):
    conn = get_conn()
    cursor = conn.cursor()
    atualizados = 0
    for _, row in df.iterrows():
        id_metrica = int(row['ID'])  # Coluna do CSV com o id da FrameMetrica
        nova_classe = int(row['NovaClasse'])  # Nova classe predicha
        cursor.execute(
            "UPDATE FrameMetrica SET classe_movimento_id=%s, foi_reclassificado=1 WHERE id=%s",
            (nova_classe, id_metrica)
        )
        atualizados += 1
    conn.commit()
    cursor.close()
    conn.close()
    return atualizados
 
def download_df(df, label="Exportar CSV"):
    csv = df.to_csv(index=False).encode()
    st.download_button(
        label=label,
        data=csv,
        file_name='dados.csv',
        mime='text/csv',
    )
def consulta_mapa_cameras():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ca.identificador, co.nome, l.descricao, m.nome
        FROM Camera ca
        JOIN Comodo co ON ca.comodo_id = co.id
        JOIN Localidade l ON co.localidade_id = l.id
        JOIN Morador m ON l.morador_id = m.id
    """)
    df = pd.DataFrame(cursor.fetchall(), columns=['Câmera', 'Cômodo', 'Localidade', 'Morador'])
    cursor.close()
    conn.close()
    return df

# ========== Interface Streamlit ==========

st.title('Mini-app Cadastro e Métricas de Câmeras')

if 'usuario' not in st.session_state:
    st.session_state['usuario'] = None

if st.session_state['usuario'] is None:
    tab_login, tab_cadastro = st.tabs(["Login", "Cadastro"])
    with tab_login:
        email = st.text_input("Email")
        senha = st.text_input("Senha", type='password')
        if st.button("Entrar"):
            usuario = autentica_usuario(email, senha)
            if usuario:
                st.session_state['usuario'] = usuario
                st.success(f"Bem-vindo, {usuario[1]}!")
                st.rerun()

            else:
                st.error("Usuário ou senha inválidos.")
    with tab_cadastro:
        nome = st.text_input("Nome (cadastro)")
        email_cad = st.text_input("Email (cadastro)")
        senha_cad = st.text_input("Senha (cadastro)", type='password')
        tipo = st.selectbox("Tipo", ["admin", "morador"])
        morador_id = None
        if tipo == "morador":
            moradores = get_opcoes('Morador', 'id, nome')
            if moradores:
                morador_escolhido = st.selectbox("Selecione seu cadastro de morador", moradores, format_func=lambda x: x[1])
                morador_id = morador_escolhido[0]
        if st.button("Cadastrar usuário"):
            cadastrar_usuario(nome, email_cad, senha_cad, tipo, morador_id)
            st.success("Usuário cadastrado! Faça login.")

else:
    usuario = st.session_state['usuario']
    tipo_usuario = usuario[2]  # 'admin' ou 'morador'
    morador_id = usuario[3]
    st.sidebar.write(f"Usuário: {usuario[1]} ({tipo_usuario})")
    if st.sidebar.button("Sair"):
        st.session_state['usuario'] = None
        st.rerun()


    if tipo_usuario == "admin":
        opcoes = ['Morador', 'Localidade', 'Cômodo', 'Câmera', 'Métrica', 'Upload vídeo', 'Vídeos enviados', 'Alertas','Exportar métricas de moradores','Atualizar Classificação']
    elif tipo_usuario == "morador":
        opcoes = ['Localidade', 'Cômodo', 'Câmera', 'Métrica', 'Upload vídeo', 'Vídeos enviados', 'Alertas']
    else:
        opcoes = []

    opcao = st.sidebar.selectbox('O que deseja fazer?', opcoes)
    
    if opcao == 'Morador' and tipo_usuario == "admin":
        nome = st.sidebar.text_input('Nome do morador')
        documento = st.sidebar.text_input('Documento')
        if st.sidebar.button('Cadastrar'):
            cadastrar_morador(nome, documento)
            st.success('Morador cadastrado!')
    elif opcao == 'Vídeos enviados':
        df_videos = consultar_videos(morador_id if tipo_usuario == "morador" else None)
        st.subheader('Vídeos enviados')
        st.dataframe(df_videos)
        download_df(df_videos, "Exportar vídeos CSV")
    elif opcao == 'Alertas':
        df_alertas = consultar_alertas(morador_id if tipo_usuario == "morador" else None)
        st.subheader('Dashboard de Alertas')
        st.dataframe(df_alertas)
        from datetime import datetime
        # Para cada alerta de PERDA_PACOTE, se for morador, permita upload
        for idx, row in df_alertas[df_alertas['Tipo'] == 'PERDA_PACOTE'].iterrows():
            st.warning(f"Alerta em {row['Câmera']} ({row['Localidade']}) às {row['Data']}: {row['Descrição']}")
            # Permissão de upload
            if tipo_usuario == "morador":
                up_key = f"file_{row['Câmera']}_{row['Data']}_{idx}"
                uploaded_video = st.file_uploader('Selecione vídeo MP4 para envio', type=['mp4'], key=up_key)
                if uploaded_video is not None and st.button(f'Enviar vídeo {idx}', key=f'send_{idx}'):
                    s3_key = f'videos/{row["Localidade"].replace(" ","_")}/{row["Câmera"].replace(":","")}/{datetime.now().strftime("%Y%m%d_%H%M%S")}_{uploaded_video.name}'
                    url_s3 = upload_video_s3(uploaded_video, s3_key)
                    st.success(f'Enviado para: {url_s3}')
            download_df(df_alertas, "Exportar alertas CSV")
    elif opcao == 'Localidade':
        if tipo_usuario == "admin":
            moradores = get_opcoes('Morador', 'id, nome')
            morador_opcao = st.sidebar.selectbox('Morador', moradores, format_func=lambda x: x[1])
            morador_id_local = morador_opcao[0]
        else:
            morador_id_local = morador_id
        descricao = st.sidebar.text_input('Descrição')
        endereco = st.sidebar.text_input('Endereço')
        if st.sidebar.button('Cadastrar'):
            cadastrar_localidade(morador_id_local, descricao, endereco)
            st.success('Localidade cadastrada!')

    elif opcao == 'Cômodo':
        if tipo_usuario == "admin":
            locais = get_opcoes('Localidade', 'id, descricao')
        else:
            locais = get_opcoes('Localidade', 'id, descricao', f'morador_id={morador_id}')
        local_opcao = st.sidebar.selectbox('Localidade', locais, format_func=lambda x: x[1])
        nome = st.sidebar.text_input('Nome do cômodo')
        if st.sidebar.button('Cadastrar'):
            cadastrar_comodo(local_opcao[0], nome)
            st.success('Cômodo cadastrado!')

    elif opcao == 'Câmera':
        if tipo_usuario == "admin":
            comodos = get_opcoes('Comodo', 'id, nome')
        else:
            comodos = get_opcoes('Comodo', 'id, nome',
                                 f'localidade_id IN (SELECT id FROM Localidade WHERE morador_id={morador_id})')
        comodo_opcao = st.sidebar.selectbox('Cômodo', comodos, format_func=lambda x: x[1])
        identificador = st.sidebar.text_input('Identificador (MAC/IP/Serial)')
        status = st.sidebar.selectbox('Status', ['ligada', 'desligada'])
        if st.sidebar.button('Cadastrar'):
            cadastrar_camera(comodo_opcao[0], identificador, status)
            st.success('Câmera cadastrada!')
    elif opcao == 'Atualizar Classificação':
        st.subheader("Atualizar classes de métricas (reclassificação por ML)")
        st.write("Faça upload de um arquivo CSV contendo as colunas **ID** e **NovaClasse**.")
        arquivo_csv = st.file_uploader("Selecione o arquivo CSV", type=["csv"])
        if arquivo_csv is not None:
            df = pd.read_csv(arquivo_csv)
            # Validação básica das colunas
            if 'ID' not in df.columns or 'NovaClasse' not in df.columns:
                st.error("O CSV deve conter as colunas 'ID' e 'NovaClasse'!")
            else:
                if st.button("Atualizar banco"):
                    n = atualizar_classes_metricas(df)
                    st.success(f"{n} métricas atualizadas com sucesso!")

    elif opcao == 'Métrica':
        st.subheader('Processar arquivo de métricas')
        camera_identificador = st.text_input('Identificador da câmera (MAC/IP/Serial)')
        uploaded_file = st.file_uploader('Selecione o arquivo de métricas (.csv)')
        if st.button('Processar'):
            processar_metrica(uploaded_file, camera_identificador)
    elif opcao == 'Exportar métricas de moradores':
        st.subheader("Exportar métricas de moradores")
        moradores = get_opcoes('Morador', 'id, nome')
        morador_escolhido = st.selectbox("Selecione um morador", moradores, format_func=lambda x: x[1])
        df_metricas = consultar_metricas(morador_id=morador_escolhido[0])
        st.dataframe(df_metricas)
        download_df(df_metricas, "Exportar métricas CSV")
    elif opcao == 'Upload vídeo':
        cameras = get_cameras_com_localidade(morador_id if tipo_usuario == "morador" else None)
        if not cameras:
            st.warning('Cadastre uma câmera antes de enviar vídeos!')
        else:
            camera_opcao = st.selectbox(
                'Selecione a câmera pelo MAC/IP (e veja a localização):',
                cameras,
                format_func=lambda x: f'{x[1]} (Cômodo: {x[2]}, Localidade: {x[3]})'
            )
            uploaded_video = st.file_uploader('Escolha um vídeo MP4 para enviar ao S3', type=['mp4'])
            if uploaded_video is not None:
                video_nome = uploaded_video.name
                localidade_pasta = camera_opcao[3].replace(' ', '_')
                mac_pasta = camera_opcao[1].replace(':', '').replace('-', '')
                s3_key = f'videos/{localidade_pasta}/{mac_pasta}/{video_nome}'
                if st.button('Enviar para S3'):
                    url_s3 = upload_video_s3(uploaded_video, s3_key)
                    st.success(f'Arquivo enviado para: {url_s3}')
                    registrar_video_no_banco(camera_opcao[0], s3_key)

    st.subheader('Mapa de Câmeras')
    df_mapa = consulta_mapa_cameras()
    st.dataframe(df_mapa)
