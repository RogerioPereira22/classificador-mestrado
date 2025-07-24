import pandas as pd
import mysql.connector

df = pd.read_csv('consolidado.csv')

# IDs fictícios para exemplo – troque pelo valor correto
CAMERA_ID = 1
CLASSE_ID = 1   # ou use None se não tiver

conn = mysql.connector.connect(user='root', password='SENHA', host='localhost', database='projeto')
cursor = conn.cursor()

for idx, row in df.iterrows():
    cursor.execute(
        """
        INSERT INTO FrameMetrica
        (camera_id, frame_num, tempo_medio, media_geral, tamanho_pacote, classe_movimento_id, perda_pacote, foi_reclassificado)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (CAMERA_ID, idx + 1, row['duracao'], row['tamanho'], row['tamanho'], CLASSE_ID, 0, False)
    )

conn.commit()
cursor.close()
conn.close()
print("Dados inseridos no banco.")
