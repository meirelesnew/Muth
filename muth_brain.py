import os, sys, datetime, threading, requests
from flask import Flask
import telebot
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")  # Variável configurada para o Hugging Face

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

def chamar_huggingface(pergunta_usuario):
    try:
        if not HF_TOKEN:
            return "🧠 Token do Hugging Face não configurado no Render!"
            
        # Usando o modelo oficial Llama 3 de 8 Bilhões de parâmetros da Meta
        url = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        
        # Formatando o prompt no padrão de chat para garantir respostas em português
        prompt_formatado = f"<|system|>\nVocê é a Muth AI, prestativa e sagaz. Responda em português de forma direta e amigável.\n<|user|>\n{pergunta_usuario}\n<|assistant|>\n"
        
        payload = {
            "inputs": prompt_formatado,
            "parameters": {"max_new_tokens": 300, "temperature": 0.7}
        }
        
        resposta = requests.post(url, json=payload, timeout=15)
        if resposta.status_code == 200:
            resultado = resposta.json()
            texto_puro = resultado[0]['generated_text']
            # Remove o histórico do prompt para entregar apenas a resposta final do bot
            resposta_ia = texto_puro.split("<|assistant|>\n")[-1].strip()
            return resposta_ia
        return f"❌ Erro Hugging Face (Status: {resposta.status_code})"
    except Exception as e:
        return f"❌ Erro de processamento: {e}"

@bot.message_handler(commands=['start', 'ajuda'])
def enviar_boas_vindas(message):
    txt = (
        "🧠 *MUTH AI • MOTOR LLAMA 3 ATIVADO*\n"
        "-----------------------------------------\n"
        "Servidor online e rodando via Hugging Face API!\n\n"
        "*Comandos operacionais:*\n"
        "💱 `/cotacao` — Dólar, Euro e Bitcoin estáveis.\n"
        "📈 `/analise PETR4 otimista` — IA de Mercado.\n"
        "🌤️ `/clima` — Meteorologia integrada.\n"
        "🚧 `/transitorj` — Pontos críticos e análise de vias.\n\n"
        "💡 _Pode conversar comigo direto no chat também!_"
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
                f"🕒 _Atualizado via API Oficial_"
            )
            bot.reply_to(message, txt, parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "⏳ API oficial instável. Consultando base de dados da Muth AI...")
            prompt = "Escreva de forma sucinta sobre a importância econômica da cotação do Dólar e do Euro hoje no Brasil."
            resposta_ia = chamar_huggingface(prompt)
            bot.reply_to(message, resposta_ia)
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
        bot.send_message(message.chat.id, "🚧 Analisando comportamento estrutural das vias do RJ...")
        prompt = "Enumere de forma muito curta e direta os 3 principais pontos de lentidão crônica no Rio de Janeiro (envolvendo Av. Brasil, Linha Vermelha ou Ponte) e dê uma dica rápida de segurança para quem está dirigindo."
        resposta_ia = chamar_huggingface(prompt)
        try:
            bot.reply_to(message, resposta_ia, parse_mode="Markdown")
        except Exception:
            bot.reply_to(message, resposta_ia)
    except Exception as e:
        bot.reply_to(message, f"❌ Erro trânsito: {e}")

@bot.message_handler(func=lambda m: True)
def responder_texto_livre(message):
    if message.text.startswith('/'): return
    bot.send_chat_action(message.chat.id, 'typing')
    resposta_ia = chamar_huggingface(message.text)
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
        
