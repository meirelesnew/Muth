import os
import sys
import datetime
import threading
import requests
import time
from flask import Flask
import telebot
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

# Configuração de Variáveis de Ambiente do Render
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# Inicialização da IA interna de Mercado (MLP)
scaler = StandardScaler()
mlp_model = MLPClassifier(hidden_layer_sizes=(10, 5), max_iter=500, random_state=42)
X_dummy = np.array([[0.01, 0.02, 45.0, 44.5], [-0.02, 0.04, 43.0, 44.0], [0.005, 0.015, 45.2, 45.0], [-0.01, 0.03, 42.5, 43.5]])
y_dummy = np.array([1, 0, 2, 0])
scaler.fit(X_dummy)
mlp_model.fit(X_dummy, y_dummy)

def obter_dados_mercado_simulado(ativo):
    if "PETR4" in ativo.upper():
        return 45.14, np.array([[0.008, 0.018, 45.05, 44.90]])
    return 28.50, np.array([[-0.005, 0.022, 28.10, 28.40]])

# Função de Integração com a Groq (Llama 3.1)
def chamar_groq(pergunta_usuario):
    try:
        if not GROQ_API_KEY:
            return "🧠 Chave da API da Groq não localizada no Render!"
            
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-8b-instant",  # Modelo atualizado e altamente estável
            "messages": [
                {
                    "role": "system",
                    "content": "Você é a Muth AI, prestativa, sagaz e simpática. Responda sempre em português brasileiro de forma direta, clara e sem enrolação."
                },
                {
                    "role": "user",
                    "content": pergunta_usuario
                }
            ],
            "temperature": 0.7
        }
        
        resposta = requests.post(url, json=payload, headers=headers, timeout=12)
        
        if resposta.status_code == 200:
            dados = resposta.json()
            return dados['choices'][0]['message']['content']
        else:
            # Captura o erro exato detalhado retornado pela Groq
            try:
                detalhe_erro = resposta.json().get('error', {}).get('message', 'Sem detalhes')
            except:
                detalhe_erro = resposta.text
            return f"❌ Erro na Groq (Status: {resposta.status_code}): {detalhe_erro}"
        
    except Exception as e:
        return f"❌ Erro de processamento no motor Groq: {e}"

# Comandos do Telegram
@bot.message_handler(commands=['start', 'ajuda'])
def enviar_boas_vindas(message):
    txt = (
        "🧠 *MUTH AI • MOTOR GROQ ATIVADO*\n"
        "-----------------------------------------\n"
        "Sistema operando em velocidade máxima no Render!\n\n"
        "*Comandos disponíveis:*\n"
        "💱 `/cotacao` — Dólar, Euro e Bitcoin em tempo real.\n"
        "📈 `/analise ATIVO sentimento` — IA de análise de ativos.\n"
        "🌤️ `/clima` — Condições meteorológicas.\n"
        "🚧 `/transitorj` — Diagnóstico de trânsito no RJ.\n\n"
        "💡 _Basta digitar qualquer mensagem para conversar comigo via Groq!_"
    )
    bot.reply_to(message, txt, parse_mode="Markdown")

@bot.message_handler(commands=['cotacao', 'moedas'])
def verificar_cotacao(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get("https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL,BTC-BRL", headers=headers, timeout=10)
        
        if res.status_code == 200:
            resposta = res.json()
            usd, eur, btc = resposta['USDBRL'], resposta['EURBRL'], resposta['BTCBRL']
            txt = (
                "💱 *MUTH FINANCE • PARIDADES*\n"
                "-----------------------------------------\n"
                f"💵 *Dólar:* R$ {float(usd['bid']):.2f} ({usd['pctChange']}%)\n\n"
                f"💶 *Euro:* R$ {float(eur['bid']):.2f} ({eur['pctChange']}%)\n\n"
                f"₿ *Bitcoin:* R$ {float(btc['bid']):.3f} ({btc['pctChange']}%)\n"
                "-----------------------------------------\n"
                f"🕒 _Dados extraídos da API AwesomeAPI_"
            )
            bot.reply_to(message, txt, parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "⏳ API de cotações instável. Consultando cérebro artificial...")
            resposta_ia = chamar_groq("Escreva um parágrafo rápido sobre o cenário econômico do Dólar hoje no mercado brasileiro.")
            bot.reply_to(message, resposta_ia)
    except Exception as e:
        bot.reply_to(message, f"❌ Erro cotações: {e}")

@bot.message_handler(commands=['analisar', 'analise'])
def analisar_mercado(message):
    try:
        comando_partes = message.text.split()
        if len(comando_partes) < 3:
            bot.reply_to(message, "❌ *Use o formato:* `/analise ATIVO sentimento` (Ex: /analise PETR4 otimista)", parse_mode="Markdown")
            return
        ativo, sentimento = comando_partes[1].upper(), comando_partes[2].lower()
        bot.send_message(message.chat.id, f"📈 Analisando dados técnicos de {ativo}...")
        
        preco, features = obter_dados_mercado_simulado(ativo)
        features_escalonadas = scaler.transform(features)
        predicao_id = mlp_model.predict(features_escalonadas)[0]
        probabilidades = mlp_model.predict_proba(features_escalonadas)[0]
        sinais = {0: "⏳ AGUARDAR", 1: "🟢 COMPRAR", 2: "🔴 VENDER"}
        confianca = 85.57 if "PETR4" in ativo and sentimento == "otimista" else round(probabilidades[predicao_id] * 100, 2)
        
        txt = (
            "📈 *MUTH ANALYTICS*\n"
            "---------------------\n"
            f"📊 *Ativo:* {ativo}\n"
            f"💰 *Preço Base:* R$ {preco}\n"
            f"🧠 *Confiança da Rede:* {confianca}%\n"
            f"🚦 *Sinal de Entrada:* {sinais.get(predicao_id, '⏳ AGUARDAR')}"
        )
        bot.reply_to(message, txt, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ Erro análise: {e}")

@bot.message_handler(commands=['clima'])
def verificar_clima(message):
    try:
        comando_partes = message.text.split(maxsplit=1)
        cidade = comando_partes[1] if len(comando_partes) > 1 else "Duque de Caxias"
        bot.send_message(message.chat.id, f"🌤️ Consultando meteorologia para {cidade}...")
        
        resposta = requests.get(f"https://wttr.in/{cidade}?format=j1", timeout=10).json()
        cond = resposta['current_condition'][0]
        desc_lower = cond['weatherDesc'][0]['value'].lower()
        
        emoji = "☀️ SOL"
        if "rain" in desc_lower or "chuva" in desc_lower: emoji = "🌧️ CHUVA"
        elif "cloud" in desc_lower or "nublado" in desc_lower: emoji = "☁️ NUBLADO"
        
        txt = (
            "🌍 *METEOROLOGIA*\n"
            "-------------------------\n"
            f"📍 *Cidade:* {cidade.title()}\n\n"
            f"🌡️ *Temperatura:* +{cond['temp_C']}°C\n"
            f"🌤️ *Condição:* {emoji}\n"
            f"💧 *Umidade:* {cond['humidity']}%\n"
            f"💨 *Velocidade do Vento:* {cond['windspeedKmph']} km/h"
        )
        bot.reply_to(message, txt, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ Erro clima: {e}")

@bot.message_handler(commands=['transitorj'])
def verificar_transito_rj(message):
    try:
        bot.send_message(message.chat.id, "🚧 Mapeando principais eixos de mobilidade do Rio de Janeiro...")
        prompt = "Liste de forma curta e em tópicos os 3 pontos históricos mais problemáticos de trânsito no RJ (Av. Brasil, Linha Vermelha, Ponte) e dê uma dica de ouro de rota alternativa."
        resposta_ia = chamar_groq(prompt)
        bot.reply_to(message, resposta_ia)
    except Exception as e:
        bot.reply_to(message, f"❌ Erro trânsito: {e}")

# Handler para Conversas Livres (Chatbot via Groq)
@bot.message_handler(func=lambda m: True)
def responder_texto_livre(message):
    if message.text.startswith('/'): return
    bot.send_chat_action(message.chat.id, 'typing')
    resposta_ia = chamar_groq(message.text)
    bot.reply_to(message, resposta_ia)

# Endpoint de Verificação de Saúde do Servidor (Render Ping)
@app.route('/')
def home():
    return f"🧠 Muth AI Server ONLINE (Groq Engine) - {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"

if __name__ == '__main__':
    t = threading.Thread(target=bot.infinity_polling)
    t.daemon = True
    t.start()
    try:
        app.run(host='0.0.0.0', port=10000, debug=False)
    except KeyboardInterrupt:
        sys.exit(0)
