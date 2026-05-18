import yfinance as yf
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
import json
import os
import requests
from datetime import datetime

# 1. CARREGAR CONFIGURAÇÕES DO MESTRE (ATIVO + SENTIMENTO)
def carregar_configuracoes():
    if os.path.exists('insights.json'):
        with open('insights.json', 'r') as f:
            config = json.load(f)
            return {
                "ativo": config.get("ativo_para_analise", "PETR4"),
                "sentimento": config.get("sentimento_mestre", 0.5)
            }
    return {"ativo": "PETR4", "sentimento": 0.5}

config_mestre = carregar_configuracoes()
ativo_escolhido = config_mestre["ativo"]
peso_humano = config_mestre["sentimento"]

# Adiciona o sufixo da bolsa brasileira se for apenas o código, mas permite ativos globais
ticker = ativo_escolhido if "." in ativo_escolhido else f"{ativo_escolhido}.SA"

print(f"🧠 MUTH v3 [MODO INDEPENDENTE]")
print(f"🎯 Ativo alvo atual: {ativo_escolhido}")
print(f"💡 Sentimento do Mestre: {peso_humano}")

# 2. PROCESSAMENTO DO ATIVO ÚNICO
try:
    print(f"📊 Baixando dados históricos para {ticker}...")
    dados = yf.download(ticker, period="5y", interval="1d", progress=False, auto_adjust=True)
    
    if dados.empty:
        print(f"❌ Erro: Não foi possível encontrar dados para o ativo '{ticker}'. Verifique o código.")
        exit()

    # Engenharia de recursos básica da Muth
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

    # Carrega memória persistente da Muth ou inicia uma nova mente
    if os.path.exists('muth_memory.keras'):
        model = models.load_model('muth_memory.keras')
        print("💾 Memória de longo prazo carregada com sucesso!")
    else:
        model = models.Sequential([
            layers.Input(shape=(4,)),
            layers.Dense(64, activation='relu'),
            layers.Dense(32, activation='relu'),
            layers.Dense(1, activation='sigmoid')
        ])
        print("🌱 Nova rede neural inicializada para este projeto.")

    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    model.fit(X_train, y_train, epochs=5, batch_size=32, verbose=0)

    # Previsão atual
    ultimos_4_dias = dados['Variacao'].iloc[-4:].values.reshape(1, 4)
    previsao_ia = model.predict(ultimos_4_dias, verbose=0)[0][0]

    # Ajuste de critério baseado no ensino humano
    gatilho = 0.53 + (0.5 - peso_humano) * 0.1
    sinal = "COMPRAR" if previsao_ia > gatilho else "AGUARDAR"
    chance_subir = round(float(previsao_ia) * 100, 2)

    print(f"\n=============================================")
    print(f"🔮 RESULTADO DA ANÁLISE MUTH")
    print(f"---------------------------------------------")
    print(f"Ativo Analisado: {ativo_escolhido}")
    print(f"Confiança de Alta: {chance_subir}% (Gatilho exigido: {gatilho:.2f})")
    print(f"Decisão da IA: {sinal}")
    print(f"=============================================")

    # Salva a evolução do modelo para a próxima execução
    model.save('muth_memory.keras')
    print("💾 Memória atualizada e salva localmente.")

except Exception as e:
    print(f"❌ Erro crítico na execução do cérebro: {e}")