# ================================
# MUTH AI - BOT HÍBRIDO COMPLETO
# Versão Resiliente e Tolerante a Falhas de Rede
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
from googlesearch import search 

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
# API DE ECONOMIA
# ================================
def obter_cotacao_dolar():
    try:
        r = requests.get("https://economia.awesomeapi.com.br/last/USD-BRL", timeout=5)
        if r.status_code == 200:
            dados = r.json()
            bid = dados["USDBRL"]["bid"]
            return f"💵 Cotação do Dólar Comercial agora: R$ {float(bid):.2f}"
    except Exception as e:
        print(f"Erro na API de Moedas: {e}")
    return None

# ================================
# FERRAMENTA DE BUSCA GOOGLE
# ================================
def buscar_na_internet(termo):
    try:
        resultados = []
        for r in search(termo, num_results=2, lang="pt", advanced=True):
            resultados.append(f"Título: {r.title}\nResumo: {r.description}")
        return "\n\n".join(resultados)
    except:
        return ""

# ================================
# IA GROQ (Rápida para uso geral e contingência)
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
                {"role": "system", "content": "Você é a Muth AI. Responda em português de maneira direta e inteligente."},
                {"role": "user", "content": pergunta}
            ],
            "temperature": 0.7
        }
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json()['choices'][0]['message']['content']
        return f"Não consegui processar a resposta agora (Groq Status {r.status_code})."
    except Exception as e:
        return f"Desculpe, encontrei um problema técnico de conexão. Tente novamente em instantes."

# ================================
# IA OPENROUTER - QWEN
# ================================
def chamar_openrouter(pergunta):
    if not OPENROUTER_API_KEY:
        print("Chave do OpenRouter ausente! Redirecionando direto para a Groq...")
        return chamar_groq(pergunta)
        
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "qwen/qwen3-next-80b-a3b-instruct:free", 
            "messages": [
                {"role": "system", "content": "Você é a Muth AI. Responda de forma direta e resumida em português."},
                {"role": "user", "content": pergunta}
            ],
            "temperature": 0.6
        }
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if r.status_code == 200:
            return r.json()['choices'][0]['message']['content']
            
        print(f"OpenRouter retornou erro {r.status_code}. Acionando Groq...")
        return chamar_groq(pergunta)
        
    except Exception:
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
# MOTOR HÍBRIDO
# ================================
def motor(texto): 
    t = texto.lower()

    if "fibonacci" in t or "/fib" in t:
        return "FIBO"

    if any(x in t for x in ["petr4", "btc"]):
        return "MERCADO"

    if "analise" in t:
        return "ML"

    if any(x in t for x in ["dolar", "dólar"]):
        return "APIDOLAR"

    if any(x in t for x in ["clima", "tempo", "transito", "trânsito", "hoje", "noticia", "notícia"]):
        return "BUSCA_WEB"

    return "GROQ"

# ================================
# PROCESSADOR CENTRAL
# ================================
def processar(msg): 
    tipo = motor(msg)

    if tipo == "FIBO":
        return f"📊 Fibonacci:\n{fibonacci(10)}"

    if tipo == "MERCADO" or tipo == "ML":
        preco, sinal = analisar_ml("PETR4")
        return f"🤖 ML ANALYSIS\nPreço: {preco}\nSinal: {sinal}"

    if tipo == "APIDOLAR":
        cotacao = obter_cotacao_dolar()
        if cotacao:
            return cotacao
        # Fallback definitivo: Se a API de moedas falhar, a IA responde o valor estimado
        return chamar_groq("Me dê uma estimativa do valor atual do dólar comercial em reais e explique que a API direta falhou.")

    if tipo == "BUSCA_WEB":
        contexto_internet = buscar_na_internet(msg)
        if contexto_internet:
            prompt_turbinado = (
                f"O usuário perguntou: '{msg}'.\n"
                f"Considere essas informações em tempo real encontradas na web para formular sua resposta:\n\n"
                f"{contexto_internet}"
            )
            return chamar_openrouter(prompt_turbinado)
        else:
            return chamar_groq(msg)

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
    
