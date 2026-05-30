# ================================
# MUTH AI - BOT HÍBRIDO COMPLETO
# Telegram + IA + ML + Fibonacci + APIs + Web Search
# ================================

import os 
import sys 
import datetime 
import threading 
import requests 
import base64 
from flask import Flask 
import telebot 
import numpy as np 
from sklearn.neural_network import MLPClassifier 
from sklearn.preprocessing import StandardScaler
from duckduckgo_search import DDGS  # Nova biblioteca para buscar na internet

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
# FERRAMENTA DE BUSCA WEB (GRATUITA)
# ================================
def buscar_na_internet(termo):
    try:
        with DDGS() as ddgs:
            # Puxa os 3 resultados mais recentes sobre o assunto
            resultados = [r["body"] for r in ddgs.text(termo, max_results=3)]
            return "\n".join(resultados)
    except Exception:
        return ""

# ================================
# IA GROQ (Rápida para uso geral)
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
                {"role": "system", "content": "Você é a Muth AI híbrida rápida."},
                {"role": "user", "content": pergunta}
            ],
            "temperature": 0.7
        }

        r = requests.post(url, json=payload, headers=headers, timeout=12)
        if r.status_code == 200:
            return r.json()['choices'][0]['message']['content']
        return "Erro IA Groq"

    except Exception as e:
        return str(e)

# ================================
# IA OPENROUTER - QWEN (Para formatar buscas em tempo real)
# ================================
def chamar_openrouter(pergunta):
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            # ID exato do Qwen3 Next Free do seu painel
            "model": "qwen/qwen3-next-80b-a3b-instruct:free", 
            "messages": [
                {"role": "system", "content": "Você é a Muth AI híbrida via Qwen. Responda de forma direta, clara e resumida em português para o Telegram."},
                {"role": "user", "content": pergunta}
            ],
            "temperature": 0.6
        }
        r = requests.post(url, json=payload, headers=headers, timeout=15)
        if r.status_code == 200:
            return r.json()['choices'][0]['message']['content']
        return f"Erro OpenRouter (Status {r.status_code})"
    except Exception as e:
        return str(e)

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

    sinais = {
        0: "AGUARDAR",
        1: "COMPRAR",
        2: "VENDER"
    }
    return preco, sinais[pred]

# ================================
# MOTOR HÍBRIDO (Inteligência de Decisão)
# ================================
def motor(texto): 
    t = texto.lower()

    if "fibonacci" in t or "/fib" in t:
        return "FIBO"

    if any(x in t for x in ["petr4", "btc"]):
        return "MERCADO"

    if "analise" in t:
        return "ML"

    # Se o usuário pedir trânsito, clima, dólar ou dados de hoje, ativa a busca web
    if any(x in t for x in ["clima", "tempo", "dolar", "dólar", "transito", "trânsito", "hoje", "noticia", "notícia"]):
        return "BUSCA_WEB"

    # Conversas padrões vão para a Groq
    return "GROQ"

# ================================
# PROCESSADOR CENTRAL
# ================================
def processar(msg): 
    tipo = motor(msg)

    if tipo == "FIBO":
        return f"📊 Fibonacci:\n{fibonacci(10)}"

    if tipo == "MERCADO":
        preco, sinal = analisar_ml("PETR4")
        return f"📈 PETR4\nPreço: {preco}\nSinal: {sinal}"

    if tipo == "ML":
        preco, sinal = analisar_ml("PETR4")
        return f"🤖 ML ANALYSIS\nPreço: {preco}\nSinal: {sinal}"

    if tipo == "BUSCA_WEB":
        # 1. Faz a raspagem rápida do Google/DuckDuckGo
        contexto_internet = buscar_na_internet(msg)
        if contexto_internet:
            # 2. Une a pergunta com os dados reais e manda pro Qwen formatar
            prompt_turbinado = (
                f"O usuário perguntou no Telegram: '{msg}'.\n"
                f"Considere essas informações em tempo real encontradas na web para responder:\n\n"
                f"{contexto_internet}"
            )
            return chamar_openrouter(prompt_turbinado)
        else:
            return "Não consegui acessar os dados da internet agora. Tente novamente em instantes."

    # Resposta rápida da Groq para saudações e assuntos gerais
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
# FLASK (Mantém o Render sabendo que o app está vivo)
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
    
