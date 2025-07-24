import pandas as pd
import joblib

df = pd.read_csv('consolidado.csv')
modelo = joblib.load('meu_modelo.pkl')  # Substitua pelo seu arquivo de modelo

# Supondo que seu modelo usa as colunas 'tamanho' e 'duracao'
df['classe_predita'] = modelo.predict(df[['tamanho', 'duracao']])

df.to_csv('consolidado_classificado.csv', index=False)
print("Arquivo consolidado_classificado.csv com as classes preditas.")
