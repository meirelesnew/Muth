import yfinance as yf
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
import json
import os
from datetime import datetime

# 1. LER CONFIGURAÇÃO DE ENSINO
def carregar_config():
    if os.path.exists('insights.json'):
        with open('insights.json', 'r') as f:
            cfg = json.load(f)
            return cfg.get("ativo_para_analise", "BTC-USD"), cfg.get("sentimento_mestre", 0.5)
    return "BTC-USD", 0.5

ativo, sentimento = carregar_config()
print(f"🧠 MUTH INDEPENDENTE — Alvo: {ativo} | Sentimento: {sentimento}")

# 2. TREINAMENTO DA REDE NEURAL DO ZERO
try:
    # Baixa os dados históricos
    dados = yf.download(ativo, period="3y", interval="1d", progress=False, auto_adjust=True)
    if dados.empty:
        print("❌ Ativo não encontrado.")
        exit()

    dados['Retorno'] = dados['Close'].pct_change()
    dados['Alvo'] = np.where(dados['Retorno'].shift(-1) > 0, 1, 0)
    dados = dados.dropna()

    # Estrutura de dados temporais (janela de 4 dias)
    X, y = [], []
    for i in range(len(dados) - 4):
        X.append(dados['Retorno'].iloc[i:i+4].values)
        y.append(dados['Alvo'].iloc[i+3])
    X, y = np.array(X), np.array(y)

    # Criando Arquitetura Neural do Zero
    model = models.Sequential([
        layers.Input(shape=(4,)),
        layers.Dense(32, activation='relu'),
        layers.Dense(16, activation='relu'),
        layers.Dense(1, activation='sigmoid')
    ])
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    model.fit(X, y, epochs=10, batch_size=16, verbose=0)

    # Predição para o próximo movimento
    ultimos_dias = dados['Retorno'].iloc[-4:].values.reshape(1, 4)
    previsao = model.predict(ultimos_dias, verbose=0)[0][0]

    # Dinâmica de Decisão baseada no seu input humano
    criterio = 0.52 + (0.5 - sentimento) * 0.1
    sinal = "COMPRAR 🚀" if previsao > criterio else "AGUARDAR ⏳"
    confianca = round(float(previsao) * 100, 1)

    # 3. SALVAR RESULTADO PARA A LANDING PAGE
    resultado = {
        "ativo": ativo,
        "sinal": sinal,
        "confianca": f"{confianca}%",
        "criterio": round(criterio, 2),
        "atualizado": datetime.now().strftime("%d/%m/%Y %H:%M")
    }

    # Salva como um arquivo JavaScript para a página ler sem precisar de banco de dados!
    with open('dados_muth.js', 'w', encoding='utf-8') as f:
        f.write(f"const dadosMuth = {json.dumps(resultado, ensure_ascii=False)};")
    
    print(f"✅ Análise concluída com sucesso! Resultado salvo para a Web.")

except Exception as e:
    print(f"❌ Erro: {e}")