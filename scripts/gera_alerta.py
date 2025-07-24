import mysql.connector

def gera_alerta(camera_id, tipo, descricao):
    conn = mysql.connector.connect(user='root', password='SENHA', host='localhost', database='projeto')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Alerta (camera_id, tipo, descricao) VALUES (%s, %s, %s)",
        (camera_id, tipo, descricao)
    )
    conn.commit()
    cursor.close()
    conn.close()
    print("Alerta registrado.")

# Exemplo de uso
if __name__ == "__main__":
    gera_alerta(1, 'PERDA_PACOTE', 'Perda acima de 10% detectada na janela 2')
