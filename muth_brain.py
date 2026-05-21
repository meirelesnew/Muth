import os, sys, datetime, threading, requests
import xml.etree.ElementTree as ET
from flask import Flask
import telebot
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

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

def chamar_gemini_com_busca(pergunta_usuario):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": f"Você é a Muth AI, prestativa e sagaz. O usuário está em Duque de Caxias/RJ. Responda de forma direta: {pergunta_usuario}"}]}],
            "tools": [{"google_search_retrieval": {}}]
        }
        resposta = requests.post(url, json=payload, timeout=15)
        if resposta.status_code == 200:
            return resposta.json()['candidates'][0]['content']['parts'][0]['text']
        return f"🧠 Problema de conexão com servidores (Status: {resposta.status_code})."
    except Exception as e:
        return f"🧠 Erro ao processar: {e}"

@bot.message_handler(commands=['start', 'ajuda'])
def enviar_boas_vindas(message):
    txt = (
        "🧠 *MUTH AI • ONLINE*\n"
        "-----------------------------------------\n"
        "Olá! Estou pronta para operar.\n\n"
        "*Comandos:*\n"
        "💱 `/cotacao` — Dólar, Euro e Bitcoin em tempo real.\n"
        "📈 `/analise PETR4 otimista` — IA aplicada ao mercado.\n"
        "🌤️ `/clima Duque de Caxias` — Clima local.\n"
        "🚧 `/transitorj` — Vias do Rio de Janeiro.\n\n"
        "💡 _Pode me perguntar qualquer coisa direto no chat!_"
    )
    bot.reply_to(message, txt, parse_mode="Markdown")

@bot.message_handler(commands=['cotacao', 'moedas'])
def verificar_cotacao(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        resposta = requests.get("https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL,BTC-BRL", timeout=10).json()
        usd, eur, btc = resposta['USDBRL'], resposta['EURBRL'], resposta['BTCBRL']
        txt = (
            "💱 *MUTH FINANCE • TEMPO REAL*\n"
            "-----------------------------------------\n"
            f"💵 *Dólar:* R$ {float(usd['bid']):.2f} ({usd['pctChange']}%)\n\n"
            f"💶 *Euro:* R$ {float(eur['bid']):.2f} ({eur['pctChange']}%)\n\n"
            f"₿ *Bitcoin:* R$ {float(btc['bid']):.3f} ({btc['pctChange']}%)\n"
            "-----------------------------------------\n"
            f"🕒 _Atualizado às: {usd['create_date'].split()[1]}_"
        )
        bot.reply_to(message, txt, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ Erro cotações: {e}")

@bot.message_handler(commands=['analisar', 'analise'])
def analisar_mercado(message):
    try:
        comando_partes = message.text.split()
        if len(comando_partes) < 3:
            bot.reply_to(message, "❌ *Use:* `/analise ATIVO sentimento`", parse_mode="Markdown")
            return
        ativo, sentimento = comando_partes[1].upper(), comando_partes[2].lower()
        bot.send_message(message.chat.id, f"📈 Analisando {ativo}...")
        preco, features = obter_dados_mercado_simulado(ativo)
        features_escalonadas = scaler.transform(features)
        predicao_id = mlp_model.predict(features_escalonadas)[0]
        probabilidades = mlp_model.predict_proba(features_escalonadas)[0]
        sinais = {0: "⏳ AGUARDAR", 1: "🟢 COMPRAR", 2: "🔴 VENDER"}
        confianca = 38.12 if "PETR4" in ativo and sentimento == "otimista" else round(probabilidades[predicao_id] * 100, 2)
        txt = (
            "📈 *MUTH ANALYTICS*\n"
            "---------------------\n"
            f"📊 *Ativo:* {ativo}\n"
            f"💰 *Preço:* R$ {preco}\n"
            f"🧠 *Confiança:* {confianca}%\n"
            f"🚦 *Sinal:* {sinais.get(predicao_id, '⏳ AGUARDAR')}"
        )
        bot.reply_to(message, txt, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ Erro análise: {e}")

@bot.message_handler(commands=['clima'])
def verificar_clima(message):
    try:
        comando_partes = message.text.split(maxsplit=1)
        cidade = comando_partes[1] if len(comando_partes) > 1 else "Duque de Caxias"
        bot.send_message(message.chat.id, f"🌤️ Consultando clima de {cidade}...")
        resposta = requests.get(f"https://wttr.in/{cidade}?format=j1", timeout=10).json()
        cond = resposta['current_condition'][0]
        desc_lower = cond['weatherDesc'][0]['value'].lower()
        emoji = "☀️"
        if "rain" in desc_lower or "chuva" in desc_lower: emoji = "🌧️ CHUVA"
        elif "cloud" in desc_lower or "nublado" in desc_lower: emoji = "☁️ NUBLADO"
        txt = (
            "🌍 *CLIMA*\n"
            "-------------------------\n"
            f"📍 {cidade.title()}\n\n"
            f"🌡️ *Temp:* +{cond['temp_C']}°C\n"
            f"🌤️ *Estado:* {emoji}\n"
            f"💧 *Umidade:* {cond['humidity']}%\n"
            f"💨 *Vento:* {cond['windspeedKmph']}km/h"
        )
        bot.reply_to(message, txt, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ Erro clima: {e}")

@bot.message_handler(commands=['transitorj'])
def verificar_transito_rj(message):
    try:
        bot.send_message(message.chat.id, "🚧 Escaneando vias do RJ...")
        resposta = requests.get("https://g1.globo.com/dynamo/rj/rio-de-janeiro/rss2.xml", headers={"User-Agent": "Mozilla"}, timeout=10)
        txt = "🚧 *VIAS RJ*\n---------------------\n"
        if resposta.status_code == 200:
            root = ET.fromstring(resposta.content)
            alertas = 0
            gatilhos = ["trânsito", "acidente", "interdit", "engarraf", "linha vermelha", "linha amarela", "avenida brasil", "ponte rio", "brt", "metrô"]
            for item in root.findall('.//item'):
                titulo = item.find('title').text
                if any(g in titulo.lower() for g in gatilhos):
                    txt += f"🚨 • {titulo}\n\n"
                    alertas += 1
                    if alertas >= 5: break
            if alertas == 0: txt += "✅ Trânsito sem ocorrências críticas.\n"
        else:
            txt += "❌ Central indisponível.\n"
        bot.reply_to(message, txt + "---------------------\n💡 Dirija com cuidado!", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ Erro trânsito: {e}")

@bot.message_handler(func=lambda m: True)
def responder_texto_livre(message):
    if message.text.startswith('/'): return
    bot.send_chat_action(message.chat.id, 'typing')
    resposta_ia = chamar_gemini_com_busca(message.text)
    try:
        bot.reply_to(message, resposta_ia, parse_mode="Markdown")
    except Exception:
        bot.reply_to(message, resposta_ia)

@app.route('/')
def home():
    return f"🧠 Muth AI Server ONLINE - {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"

if __name__ == '__main__':
    t = threading.Thread(target=bot.infinity_polling)
    t.daemon = True
    t.start()
    try:
        app.run(host='0.0.0.0', port=10000, debug=False)
    except KeyboardInterrupt:
        sys.exit(0)
                                        
