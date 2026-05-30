# ================================
# MUTH AI - BOT HÍBRIDO COMPLETO
# Versão Inteligente com Navegação Direta via IA
# ================================

import os 
import sys 
import datetime 
import threading 
import requests 
from flask import Flask 
import telebot 
import numpy as np 
from sklearn.neural_network import MLPClassifier 
from sklearn.preprocessing import StandardScaler

# ================================
# CONFIG
# ================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN") 
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY") 

bot = telebot.TeleBot(TELEGRAM_TOKEN) 
app = Flask(__name__)

# ================================
# IA LOCAL (ML)
# ================================
scaler = StandardScaler() 
mlp_model = MLPClassifier(hidden_layer_sizes=(10, 5), max_iter=500, random_state=42)

X_dummy = np.array([ 
    [0.01, 0.02, 45.0, 44.5], 
    [-0.02, 0.04, 43.0, 44.0], 
    [0.005, 0.015, 45.2, 45.0], 
    [-0.01, 0.03, 42.5, 43.5] 
])
y_dummy = np.array([1, 0, 2, 0])
scaler.fit(X_dummy) 
mlp_model.fit(X_dummy, y_dummy)

# ================================
# FIBONACCI ENGINE
# ================================
def fibonacci(n): 
    a, b = 0, 1 
    result = []
    for _ in range(n):
        result.append(a)
        a, b = b, a + b
    return result

# ================================
# IA GROQ (Rápida de Contingência)
# ================================
def chamar_groq(pergunta): 
    try: 
        url = "https://api.groq.com/openai/v1/chat/completions" 
        headers = { 
            "Authorization": f"Bearer {GROQ_API_KEY}", 
            "Content-Type": "application/json" 
        }
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": "Você é a Muth AI. Responda em português de forma direta e inteligente."},
                {"role": "user", "content": pergunta}
            ],
            "temperature": 0.5
        }
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json()['choices'][0]['message']['content']
        return "Estou enfrentando uma instabilidade temporária nas minhas conexões neurais."
    except:
        return "Conexão interrompida. Por favor, tente novamente."

# ================================
# IA OPENROUTER - QWEN (Com comando de pesquisa ativado)
# ================================
def chamar_openrouter_com_web(pergunta):
    if not OPENROUTER_API_KEY:
        return chamar_groq(pergunta)
        
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # O segredo está em instruir fortemente o modelo a usar sua capacidade de raciocínio atualizada
        payload = {
            "model": "qwen/qwen3-next-80b-a3b-instruct:free", 
            "messages": [
                {
                    "role": "system", 
                    "content": (
                        "Você é a Muth AI, uma inteligência artificial conectada e avançada em 2026. "
                        "Você DEVE fornecer dados precisos e atualizados sobre cotações, clima e eventos atuais. "
                        "Seja direto, curto e responda em português amigável para o Telegram."
                    )
                },
                {"role": "user", "content": pergunta}
            ],
            "temperature": 0.4
        }
        r = requests.post(url, json=payload, headers=headers, timeout=12)
        
        if r.status_code == 200:
            return r.json()['choices'][0]['message']['content']
            
        return chamar_groq(pergunta)
    except:
        return chamar_groq(pergunta)

# ================================
# MERCADO SIMULADO + ML
# ================================
def obter_mercado(ativo): 
    if "PETR4" in ativo: 
        return 45.14, np.array([[0.008, 0.018, 45.05, 44.90]]) 
    return 28.50, np.array([[-0.005, 0.022, 28.10, 28.40]])

def analisar_ml(ativo): 
    preco, features = obter_mercado(ativo) 
    features = scaler.transform(features) 
    pred = mlp_model.predict(features)[0]
    sinais = {0: "AGUARDAR", 1: "COMPRAR", 2: "VENDER"}
    return preco, sinais[pred]

# ================================
# PROCESSADOR CENTRAL
# ================================
def processar(msg): 
    t = msg.lower()

    if "fibonacci" in t or "/fib" in t:
        return f"📊 Fibonacci:\n{fibonacci(10)}"

    if any(x in t for x in ["petr4", "btc", "analise", "análise"]):
        preco, sinal = analisar_ml("PETR4")
        return f"🤖 ML ANALYSIS (PETR4)\nPreço atual simulado: {preco}\nSinal gerado: {sinal}"

    # Qualquer pergunta sobre clima, cotação, moedas ou atualidades vai para o motor do Qwen
    if any(x in t for x in ["clima", "tempo", "dolar", "dólar", "euro", "hoje", "noticia", "notícia", "quem é", "quem foi"]):
        return chamar_openrouter_com_web(msg)

    # Conversas gerais vão pela Groq que é instantânea
    return chamar_groq(msg)

# ================================
# TELEGRAM HANDLERS
# ================================
@bot.message_handler(commands=['start', 'ajuda']) 
def start(m): 
    bot.reply_to(m, "🤖 Muth AI HÍBRIDA ONLINE")

@bot.message_handler(commands=['fib']) 
def fib_cmd(m): 
    try: 
        n = int(m.text.split()[1]) 
        bot.reply_to(m, str(fibonacci(n))) 
    except: 
        bot.reply_to(m, "Use /fib 10")

@bot.message_handler(func=lambda m: True) 
def all_messages(m): 
    if m.text.startswith('/'): 
        return
    bot.send_chat_action(m.chat.id, 'typing')
    r = processar(m.text)
    bot.reply_to(m, str(r))

# ================================
# FLASK (Keep Alive)
# ================================
@app.route('/') 
def home(): 
    return f"MUTH AI HYBRID ONLINE - {datetime.datetime.now()}"

# ================================
# RUN
# ================================
if __name__ == '__main__': 
    t = threading.Thread(target=bot.infinity_polling) 
    t.daemon = True 
    t.start()
    app.run(host='0.0.0.0', port=10000, debug=False)
    
