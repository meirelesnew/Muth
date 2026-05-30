# ================================
# MUTH AI - BOT HÍBRIDO COMPLETO
# Versão 2026 - Livre de Erros de Build (Pure Python)
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
from duckduckgo_search import DDGS  # Biblioteca oficial ajustada para versão leve

# ================================
# CONFIGURAÇÕES DE AMBIENTE
# ================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN") 
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY") 

bot = telebot.TeleBot(TELEGRAM_TOKEN) 
app = Flask(__name__)

# ================================
# IA LOCAL (MACHINE LEARNING)
# ================================
scaler = StandardScaler() 
mlp_model = MLPClassifier(hidden_layer_sizes=(10, 5), max_iter=500, random_state=42)

# Dados simulados para o modelo não iniciar vazio
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
# MOTOR MATEMÁTICO (FIBONACCI)
# ================================
def fibonacci(n): 
    a, b = 0, 1 
    result = []
    for _ in range(n):
        result.append(a)
        a, b = b, a + b
    return result

# ================================
# MOTOR DE BUSCA WEB (RESOLVE DADOS EM TEMPO REAL)
# ================================
def pesquisar_web(termo):
    """Busca resultados reais na internet sem depender de pacotes Rust"""
    try:
        with DDGS() as ddgs:
            # Padrão compatível com a versão puramente Python (5.x)
            resultados = [r['body'] for r in list(ddgs.text(termo, max_results=3))]
            return "\n".join(resultados)
    except Exception as e:
        print(f"Erro na busca DuckDuckGo: {e}")
        return ""

# ================================
# MOTOR DE INTELIGÊNCIA ARTIFICIAL (LLM)
# ================================
def perguntar_ia(prompt_sistema, pergunta_usuario):
    """Chama a API do OpenRouter (Qwen) com fallback automático para Groq (Llama)"""
    # 1. Tentativa Principal: OpenRouter (Qwen)
    if OPENROUTER_API_KEY:
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "qwen/qwen3-next-80b-a3b-instruct:free", 
                "messages": [
                    {"role": "system", "content": prompt_sistema},
                    {"role": "user", "content": pergunta_usuario}
                ],
                "temperature": 0.4
            }
            r = requests.post(url, json=payload, headers=headers, timeout=12)
            if r.status_code == 200:
                return r.json()['choices'][0]['message']['content']
        except:
            pass

    # 2. Segunda Alternativa (Plano B): Groq (Llama 3.1)
    if GROQ_API_KEY:
        try:
            url = "https://api.groq.com/openai/v1/chat/completions" 
            headers = { 
                "Authorization": f"Bearer {GROQ_API_KEY}", 
                "Content-Type": "application/json" 
            }
            payload = {
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": prompt_sistema},
                    {"role": "user", "content": pergunta_usuario}
                ],
                "temperature": 0.4
            }
            r = requests.post(url, json=payload, headers=headers, timeout=10)
            if r.status_code == 200:
                return r.json()['choices'][0]['message']['content']
        except:
            pass
        
    return "Desculpe, meus sistemas de resposta rápida estão temporariamente instáveis."

# ================================
# PROCESSAMENTO DE MERCADO SIMULADO
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
# PROCESSADOR CENTRAL DE DECISÃO (ROTEADOR)
# ================================
def processar(msg): 
    t = msg.lower()

    # Rota 1: Comando Matemático Direto
    if "fibonacci" in t or "/fib" in t:
        return f"📊 Sequência Fibonacci:\n{fibonacci(10)}"

    # Rota 2: Machine Learning Local
    if any(x in t for x in ["petr4", "btc", "analise", "análise"]):
        preco, sinal = analisar_ml("PETR4")
        return f"🤖 MUTH ML ANALYSIS\nAtivo monitorado: PETR4\nPreço simulado: R$ {preco}\nSinal preditivo do modelo: {sinal}"

    # Rota 3: Consultas de Tempo Real (Dólar, Clima, Tempo, Notícias)
    if any(x in t for x in ["clima", "tempo", "dolar", "dólar", "euro", "hoje", "noticia", "notícia"]):
        dados_da_internet = pesquisar_web(msg)
        
        if dados_da_internet:
            sys_prompt = (
                "Você é a Muth AI. Você recebeu dados reais extraídos em tempo real da internet para responder ao usuário. "
                "Use as informações fornecidas para formular uma resposta exata, curta, direta e atualizada. "
                "Nunca diga que não tem acesso à internet, pois os dados te foram fornecidos abaixo. Responda em português."
            )
            user_prompt = f"Pergunta do usuário: {msg}\n\nDados reais coletados na internet agora:\n{dados_da_internet}"
            return perguntar_ia(sys_prompt, user_prompt)
        
    # Rota 4: Conversas Gerais / Suporte Comum
    sys_prompt_geral = "Você é a Muth AI, um assistente inteligente, direto e muito prestativo. Responda de forma objetiva em português."
    return perguntar_ia(sys_prompt_geral, msg)

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
# FLASK INTERFACE (KEEP-ALIVE NO RENDER)
# ================================
@app.route('/') 
def home(): 
    return f"MUTH AI HYBRID ONLINE - {datetime.datetime.now()}"

# ================================
# INICIALIZAÇÃO DA APLICAÇÃO
# ================================
if __name__ == '__main__': 
    # Thread separada para o Polling do Telegram não travar o Flask
    t = threading.Thread(target=bot.infinity_polling) 
    t.daemon = True 
    t.start()
    
    # Inicia o servidor Web na porta padrão exigida pelo Render
    app.run(host='0.0.0.0', port=10000, debug=False)
