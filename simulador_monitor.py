import random
import time
import mysql.connector

# Funções do banco (use suas credenciais)
DB_HOST = 'bmk6y39nfvstjjc20lge-mysql.services.clever-cloud.com'
DB_USER = 'umwmt7j24hze8gae'
DB_PASSWORD = 'MfmVrFw5mnGapQQqMUi1'
DB_NAME = 'bmk6y39nfvstjjc20lge'

def get_conn():
    return mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )

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

def simular_metricas_cameras(num_moradores=3, cameras_por_morador=2, frames_por_camera=1000):
    # IDs reais: busque do banco! Aqui, para exemplo, IDs sintéticos:
    camera_ids = []
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM Camera")
    camera_ids = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    if not camera_ids:
        print('Cadastre câmeras no sistema!')
        return
    for camera_id in camera_ids:
        perda_base = random.uniform(0.01, 0.2)  # Perda média variando entre câmeras
        for frame in range(1, frames_por_camera+1):
            tempo_medio = random.uniform(0.03, 0.06)
            media_geral = random.uniform(80, 120)
            tamanho_pacote = random.randint(800, 1000)
            perda_pacote = max(0, random.gauss(perda_base, 0.03))
            classe_movimento_id = random.choice([1, 2, 3])
            foi_reclassificado = False
            inserir_metrica(camera_id, frame, tempo_medio, media_geral, tamanho_pacote, classe_movimento_id, perda_pacote, foi_reclassificado)
        print(f"Métricas simuladas para câmera {camera_id}")

def monitorar_perda(limiar_perda=0.1, janela_frames=100):
    conn = get_conn()
    cursor = conn.cursor()
    # Pega as últimas métricas de cada câmera:
    cursor.execute("""
        SELECT camera_id, MAX(frame_num) FROM FrameMetrica GROUP BY camera_id
    """)
    cameras_frames = cursor.fetchall()
    for camera_id, max_frame in cameras_frames:
        cursor.execute("""
            SELECT AVG(perda_pacote) FROM FrameMetrica
            WHERE camera_id=%s AND frame_num > %s
        """, (camera_id, max_frame-janela_frames))
        avg_perda = cursor.fetchone()[0] or 0
        if avg_perda > limiar_perda:
            registrar_alerta(camera_id, 'PERDA_PACOTE', f'Perda média de {avg_perda:.2%} acima do limiar')
            print(f"[ALERTA] Câmera {camera_id} com perda {avg_perda:.2%}")
    cursor.close()
    conn.close()



if __name__ == "__main__":
    # Simule dados para todas as câmeras
    simular_metricas_cameras()
    # Monitore e gere alertas
    monitorar_perda(limiar_perda=0.08, janela_frames=100)
