import yfinance as yf
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
import json
import os
import requests
from datetime import datetime

# 1. CONFIGURAÇÕES
PROJECT_ID = "carteira-01"
API_KEY = "AIzaSyAJyTeir6U4_AnqDuBzuKQ0ODIiihgpz4c"
URL_FIRESTORE = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/previsoes_carteira?key={API_KEY}"

MINHA_CARTEIRA = ["ITSA4.SA", "EGIE3.SA", "KLBN4.SA", "TAEE11.SA", "BBSE3.SA", "BBAS3.SA", "WEGE3.SA", "MXRF11.SA", "GARE11.SA"]

# 2. CARREGAR INSIGHTS DO MESTRE
def obter_sentimento_mestre():
    if os.path.exists('insights.json'):
        with open('insights.json', 'r') as f:
            return json.load(f).get("sentimento_mestre", 0.5)
    return 0.5

peso_humano = obter_sentimento_mestre()
print(f"🧠 MUTH v3 - Sentimento do Mestre carregado: {peso_humano}")

# 3. LOOP DE PROVESSAMENTO
for ativo in MINHA_CARTEIRA:
    try:
        dados = yf.download(ativo, period="5y", interval="1d", progress=False, auto_adjust=True)
        if dados.empty: continue

        dados['Variacao'] = dados['Close'].pct_change()
        dados['Alvo'] = np.where(dados['Variacao'].shift(-1) > 0, 1, 0)
        dados = dados.dropna()

        X, y = [], []
        for i in range(len(dados) - 4):
            X.append(dados['Variacao'].iloc[i:i+4].values)
            y.append(dados['Alvo'].iloc[i+3])

        X, y = np.array(X), np.array(y)
        divisao = int(len(X) * 0.8)
        X_train, y_train = X[:divisao], y[:divisao]

        # Carrega memória existente ou cria uma do zero
        if os.path.exists('muth_memory.keras'):
            model = models.load_model('muth_memory.keras')
        else:
            model = models.Sequential([
                layers.Input(shape=(4,)),
                layers.Dense(64, activation='relu'),
                layers.Dense(32, activation='relu'),
                layers.Dense(1, activation='sigmoid')
            ])

        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        model.fit(X_train, y_train, epochs=5, batch_size=32, verbose=0)

        # Previsão
        ultimos_4_dias = dados['Variacao'].iloc[-4:].values.reshape(1, 4)
        previsao_ia = model.predict(ultimos_4_dias, verbose=0)[0][0]

        # GATILHO EVOLUTIVO AJUSTADO PELO MESTRE
        # Se você está pessimista (0.1), o gatilho sobe (exige mais certeza para comprar)
        gatilho = 0.53 + (0.5 - peso_humano) * 0.1
        sinal = "COMPRAR" if previsao_ia > gatilho else "AGUARDAR"
        chance_subir = round(float(previsao_ia) * 100, 2)

        # Envia para o Firebase
        payload = {
            "fields": {
                "ativo": {"stringValue": ativo.replace(".SA", "")},
                "data_analise": {"stringValue": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                "chance_subir": {"doubleValue": chance_subir},
                "sinal": {"stringValue": sinal}
            }
        }
        requests.post(URL_FIRESTORE, data=json.dumps(payload))
        print(f"✅ {ativo} atualizado com Gatilho de {gatilho:.2f} -> {sinal}")

        # Salva a evolução da memória
        model.save('muth_memory.keras')

    except Exception as e:
        print(f"❌ Erro em {ativo}: {e}")