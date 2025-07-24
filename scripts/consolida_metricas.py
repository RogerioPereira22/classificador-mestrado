import pandas as pd

df = pd.read_csv('trace.csv')

# Exemplo: calcular a média do tamanho dos pacotes e duração para cada janela de 10 frames
janela = 10
df['frame_id'] = df['frame_id'].astype(int)
df['tamanho'] = df['tamanho'].astype(int)
df['duracao'] = df['duracao'].astype(float)
df['janela'] = (df['frame_id'] - 1) // janela + 1

df_consol = df.groupby('janela').agg({
    'tamanho': 'mean',
    'duracao': 'mean'
}).reset_index()

df_consol.to_csv('consolidado.csv', index=False)
print("Métricas consolidadas em consolidado.csv")
