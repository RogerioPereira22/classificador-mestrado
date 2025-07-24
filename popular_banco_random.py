import random
import hashlib
import mysql.connector
from faker import Faker

DB_HOST = 'bmk6y39nfvstjjc20lge-mysql.services.clever-cloud.com'
DB_USER = 'umwmt7j24hze8gae'
DB_PASSWORD = 'MfmVrFw5mnGapQQqMUi1'
DB_NAME = 'bmk6y39nfvstjjc20lge'

faker = Faker('pt_BR')

def get_conn():
    return mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )

def inserir_classes_movimento():
    conn = get_conn()
    cursor = conn.cursor()
    classes = [(1, 'Baixa'), (2, 'Média'), (3, 'Alta')]
    for id_, nome in classes:
        try:
            cursor.execute("INSERT INTO ClasseMovimento (id, nome) VALUES (%s, %s)", (id_, nome))
        except mysql.connector.Error:
            pass  # já existe, ignora erro
    conn.commit()
    cursor.close()
    conn.close()

def get_classe_movimento_ids():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM ClasseMovimento")
    ids = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return ids
def inserir_video(camera_id, caminho_s3):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Video (camera_id, caminho_s3, data_envio) VALUES (%s, %s, NOW())",
                   (camera_id, caminho_s3))
    conn.commit()
    cursor.close()
    conn.close()

def inserir_morador(nome, documento):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Morador (nome, documento) VALUES (%s, %s)", (nome, documento))
    conn.commit()
    id_morador = cursor.lastrowid
    cursor.close()
    conn.close()
    return id_morador
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def inserir_usuario(nome, email, senha, tipo, morador_id):
    conn = get_conn()
    cursor = conn.cursor()
    senha_hash = hash_password(senha)
    cursor.execute("INSERT INTO Usuario (nome, email, senha_hash, tipo, morador_id) VALUES (%s, %s, %s, %s, %s)",
                   (nome, email, senha_hash, tipo, morador_id))
    conn.commit()
    cursor.close()
    conn.close()
def inserir_localidade(morador_id, descricao, endereco):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Localidade (morador_id, descricao, endereco) VALUES (%s, %s, %s)",
                   (morador_id, descricao, endereco))
    conn.commit()
    id_localidade = cursor.lastrowid
    cursor.close()
    conn.close()
    return id_localidade

def inserir_comodo(localidade_id, nome):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Comodo (localidade_id, nome) VALUES (%s, %s)", (localidade_id, nome))
    conn.commit()
    id_comodo = cursor.lastrowid
    cursor.close()
    conn.close()
    return id_comodo

def inserir_camera(comodo_id, identificador, status='ligada'):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Camera (comodo_id, identificador, status) VALUES (%s, %s, %s)",
                   (comodo_id, identificador, status))
    conn.commit()
    id_camera = cursor.lastrowid
    cursor.close()
    conn.close()
    return id_camera
def inserir_alerta(camera_id, tipo, descricao):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Alerta (camera_id, tipo, descricao, data_hora) VALUES (%s, %s, %s, NOW())",
        (camera_id, tipo, descricao)
    )
    conn.commit()
    cursor.close()
    conn.close()
def inserir_metrica(camera_id, frame_num, tempo_medio, media_geral, tamanho_pacote, classe_movimento_id, perda_pacote, foi_reclassificado):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO FrameMetrica (camera_id, frame_num, tempo_medio, media_geral, tamanho_pacote, classe_movimento_id, perda_pacote, foi_reclassificado)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        camera_id, frame_num, tempo_medio, media_geral, tamanho_pacote,
        classe_movimento_id, perda_pacote, foi_reclassificado
    ))
    conn.commit()
    cursor.close()
    conn.close()
if __name__ == "__main__":
    inserir_classes_movimento()
    classe_movimento_ids = get_classe_movimento_ids()
    num_moradores = 100
    localidades_por_morador = (1, 2)
    comodos_por_localidade = (2, 4)
    cameras_por_comodo = (1, 2)
    frames_por_camera = 50

    for _ in range(num_moradores):
        nome = faker.name()
        documento = faker.cpf()
        morador_id = inserir_morador(nome, documento)
        email = faker.email()
        senha = "senha123"
        tipo = "morador"
        inserir_usuario(nome, email, senha, tipo, morador_id)
        print(f"Morador: {nome} (id={morador_id})")

        for _ in range(random.randint(*localidades_por_morador)):
            desc_localidade = faker.word().capitalize() + " " + faker.word().capitalize()
            endereco = faker.address()
            localidade_id = inserir_localidade(morador_id, desc_localidade, endereco)

            for _ in range(random.randint(*comodos_por_localidade)):
                nome_comodo = random.choice(['Sala', 'Quarto', 'Cozinha', 'Garagem', 'Banheiro', 'Varanda'])
                comodo_id = inserir_comodo(localidade_id, nome_comodo)

                for _ in range(random.randint(*cameras_por_comodo)):
                    mac = faker.mac_address()
                    status = random.choice(['ligada', 'desligada'])
                    camera_id = inserir_camera(comodo_id, mac, status)
                    
                    # Inserir video fake relacionado à camera
                    caminho_s3 = f"s3://bucket_fake/videos/{mac.replace(':','')}.mp4"
                    inserir_video(camera_id, caminho_s3)
                    
                    print(f"  Camera: {mac} em {nome_comodo} (id={camera_id})")
                    for frame in range(1, frames_por_camera+1):
                        tempo_medio = random.uniform(0.03, 0.07)
                        media_geral = random.uniform(90, 120)
                        tamanho_pacote = random.randint(800, 1200)
                        classe_movimento_id = random.choice(classe_movimento_ids)
                        perda_pacote = max(0, random.gauss(0.03, 0.03))  # média 3%
                        foi_reclassificado = False
                        inserir_metrica(camera_id, frame, tempo_medio, media_geral, tamanho_pacote, classe_movimento_id, perda_pacote, foi_reclassificado)

