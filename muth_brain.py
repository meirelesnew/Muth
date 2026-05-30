# ================================
# MUTH AI - BOT HÍBRIDO COMPLETO
# Versão Estabilizada para Python 3.14
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
from duckduckgo_search import DDGS  # Certificando importação correta

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
    """Busca resultados reais na internet limpando e tratando o termo"""
    try:
        termo_limpo = termo.replace("/clima", "").replace("/dolar", "").strip()
        if not termo_limpo:
            return ""
            
        with DDGS() as ddgs:
            res_list = list(ddgs.text(termo_limpo, max_results=3))
            if res_list:
                resultados = [r['body'] for r in res_list if 'body' in r]
                return "\n".join(resultados)
    except Exception as e:
        print(f"Erro na busca DuckDuckGo: {e}")
    return ""

# ================================
# MOTOR DE INTELIGÊNCIA ARTIFICIAL (LLM)
# ================================
def perguntar_ia(prompt_sistema, pergunta_usuario):
    """Chama a API do OpenRouter com fallback automático para Groq"""
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
    t = msg.strip().lower()

    if "fibonacci" in t or t.startswith("/fib"):
        return f"📊 Sequência Fibonacci:\n{fibonacci(10)}"

    if any(x in t for x in ["petr4", "btc", "analise", "análise"]):
        preco, sinal = analisar_ml("PETR4")
        return f"🤖 MUTH ML ANALYSIS\nAtivo monitorado: PETR4\nPreço simulado: R$ {preco}\nSinal preditivo do modelo: {sinal}"

    palavras_chave_tempo_real = ["clima", "tempo", "dolar", "dólar", "euro", "hoje", "noticia", "notícia", "climarj"]
    if any(x in t for x in palavras_chave_tempo_real):
        dados_da_internet = pesquisar_web(msg)
        
        if dados_da_internet:
            sys_prompt = (
                "Você é a Muth AI, um assistente com acesso total à internet atualizada. "
                "Abaixo são fornecidos dados reais e recentes extraídos da web sobre a pergunta do usuário. "
                "Use ESSES DADOS para responder de forma exata, curta e direta. "
                "NUNCA diga que não tem acesso a tempo real ou que é apenas um modelo de linguagem. Responda em português."
            )
            user_prompt = f"Pergunta do usuário: {msg}\n\n[DADOS REAIS DA INTERNET]:\n{dados_da_internet}"
            return perguntar_ia(sys_prompt, user_prompt)
        else:
            sys_prompt_falha = "Você é a Muth AI. Responda à pergunta de forma direta, fazendo uma estimativa realista se necessário."
            return perguntar_ia(sys_prompt_falha, msg)
        
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
    try:
        bot.send_chat_action(m.chat.id, 'typing')
        r = processar(m.text)
        bot.reply_to(m, str(r))
    except Exception as error:
        print(f"Erro ao processar mensagem do Telegram: {error}")

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
    # Iniciando polling seguro
    t = threading.Thread(target=bot.infinity_polling, kwargs={"skip_pending": True}) 
    t.daemon = True 
    t.start()
    
    # Render escuta estritamente na porta 10000 de forma padrão
    app.run(host='0.0.0.0', port=10000, debug=False)
    
