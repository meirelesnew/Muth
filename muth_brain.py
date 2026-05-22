import os
import sys
import datetime
import threading
import requests
import time
import base64
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

# Função de Integração de Texto (Llama 3.1)
def chamar_groq(pergunta_usuario):
    try:
        if not GROQ_API_KEY:
            return "🧠 Chave da API da Groq não localizada no Render!"
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": "Você é a Muth AI, prestativa, sagaz e simpática. Responda sempre em português brasileiro de forma direta, clara e sem enrolação."},
                {"role": "user", "content": pergunta_usuario}
            ],
            "temperature": 0.7
        }
        resposta = requests.post(url, json=payload, headers=headers, timeout=12)
        if resposta.status_code == 200:
            return resposta.json()['choices'][0]['message']['content']
        return f"❌ Erro na Groq (Status: {resposta.status_code})"
    except Exception as e:
        return f"❌ Erro de processamento: {e}"

# NOVA FUNÇÃO: Motor de Visão Computacional (Llama 3.2 Vision)
def chamar_groq_visao(base64_image, prompt_texto):
    try:
        if not GROQ_API_KEY:
            return "🧠 Chave da API da Groq não localizada!"
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.2-11b-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_texto},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            "temperature": 0.2
        }
        resposta = requests.post(url, json=payload, headers=headers, timeout=15)
        if resposta.status_code == 200:
            return resposta.json()['choices'][0]['message']['content']
        return f"❌ Erro no processamento da imagem (Status: {resposta.status_code})"
    except Exception as e:
        return f"❌ Erro no motor de visão: {e}"

# Comandos do Telegram
@bot.message_handler(commands=['start', 'ajuda'])
def enviar_boas_vindas(message):
    txt = (
        "🧠 *MUTH AI • MÓDULO VISÃO ATIVADO*\n"
        "-----------------------------------------\n"
        "Agora eu consigo ler imagens e documentos!\n\n"
        "*Comandos de texto:*\n"
        "💱 `/cotacao` — Cotações de moedas.\n"
        "📈 `/analise ATIVO sentimento` — Análise de ações.\n"
        "🌤️ `/clima Bairro` — Clima atual.\n"
        "🚧 `/transito Local` — Rotas e trânsito histórico.\n"
        "📦 `/rastreio CODIGO` — Rastreamento Correios.\n\n"
        "📷 *Módulo de Fotos:* Basta me enviar a foto de qualquer nota fiscal, comprovante ou texto que eu farei a leitura analítica para você automaticamente!"
    )
    bot.reply_to(message, txt, parse_mode="Markdown")

@bot.message_handler(commands=['cotacao', 'moedas'])
def verificar_cotacao(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get("https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL,BTC-BRL", headers=headers, timeout=10)
        if res.status_code == 200:
            resposta = res.json()
            usd, eur, btc = resposta['USDBRL'], resposta['EURBRL'], resposta['BTCBRL']
            txt = (
                "💱 *MUTH FINANCE • PARIDADES*\n"
                "-----------------------------------------\n"
                f"💵 *Dólar:* R$ {float(usd['bid']):.2f} ({usd['pctChange']}%)\n"
                f"💶 *Euro:* R$ {float(eur['bid']):.2f} ({eur['pctChange']}%)\n"
                f"₿ *Bitcoin:* R$ {float(btc['bid']):.3f} ({btc['pctChange']}%)\n"
            )
            bot.reply_to(message, txt, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ Erro cotações: {e}")

@bot.message_handler(commands=['analisar', 'analise'])
def analisar_mercado(message):
    try:
        comando_partes = message.text.split()
        if len(comando_partes) < 3:
            bot.reply_to(message, "❌ Use: `/analise ATIVO sentimento`", parse_mode="Markdown")
            return
        ativo, sentimento = comando_partes[1].upper(), comando_partes[2].lower()
        preco, features = obter_dados_mercado_simulado(ativo)
        features_escalonadas = scaler.transform(features)
        predicao_id = mlp_model.predict(features_escalonadas)[0]
        sinais = {0: "⏳ AGUARDAR", 1: "🟢 COMPRAR", 2: "🔴 VENDER"}
        txt = f"📈 *MUTH ANALYTICS*\n📊 *Ativo:* {ativo}\n💰 *Preço:* R$ {preco}\n🚦 *Sinal:* {sinais.get(predicao_id)}"
        bot.reply_to(message, txt, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ Erro análise: {e}")

@bot.message_handler(commands=['clima'])
def verificar_clima(message):
    try:
        comando_partes = message.text.split(maxsplit=1)
        cidade = comando_partes[1] if len(comando_partes) > 1 else "Duque de Caxias"
        resposta = requests.get(f"https://wttr.in/{cidade}?format=j1", timeout=10).json()
        cond = resposta['current_condition'][0]
        txt = f"🌍 *METEOROLOGIA*\n📍 *Cidade:* {cidade.title()}\n🌡️ *Temp:* +{cond['temp_C']}°C\n💧 *Umidade:* {cond['humidity']}%"
        bot.reply_to(message, txt, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ Erro clima: {e}")

@bot.message_handler(commands=['transito'])
def verificar_transito_customizado(message):
    try:
        comando_partes = message.text.split(maxsplit=1)
        if len(comando_partes) < 2:
            bot.reply_to(message, "🚧 Use: `/transito Linha Amarela`", parse_mode="Markdown")
            return
        local_especifico = comando_partes[1]
        prompt = f"Análise geográfica e gargalos históricos de trânsito em: {local_especifico}, Rio de Janeiro. Sugira rotas reais."
        bot.reply_to(message, chamar_groq(prompt))
    except Exception as e:
        bot.reply_to(message, f"❌ Erro trânsito: {e}")

@bot.message_handler(commands=['rastreio', 'rastrear'])
def verificar_rastreio(message):
    try:
        comando_partes = message.text.split()
        if len(comando_partes) < 2:
            bot.reply_to(message, "📦 Use: `/rastreio CODIGO`", parse_mode="Markdown")
            return
        codigo_objeto = comando_partes[1].upper()
        url = f"https://api.linketrack.com/v1/track/json?user=teste&token=1fed60e6e761614742a7ea473070445d4c827c62b48e025810b42f21054bdf1d&codigo={codigo_objeto}"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            eventos = res.json().get('eventos', [])
            if not eventos:
                bot.reply_to(message, "📦 Objeto não postado ainda.")
                return
            ultimo = eventos[0]
            txt = f"📦 *RASTREIO*\n🚦 *Status:* {ultimo.get('status')}\n📅 *Data:* {ultimo.get('data')}\n📍 *Local:* {ultimo.get('local')}"
            bot.reply_to(message, txt, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, "🌐 Sistema de rastreamento temporariamente instável.")

# NOVO HANDLER: Captura e processamento de Fotos
@bot.message_handler(content_types=['photo'])
def analisar_imagem_recebida(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        aviso = bot.reply_to(message, "📸 *Foto recebida!* Convertendo dados e escaneando o documento com visão artificial...", parse_mode="Markdown")
        
        # Baixa o arquivo de imagem enviado pelo usuário
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Converte os bytes da imagem para uma string Base64 técnica
        base64_image = base64.b64encode(downloaded_file).decode('utf-8')
        
        prompt = (
            "Você é a Muth AI. Analise detalhadamente a imagem fornecida. Ela é uma Nota Fiscal / Cupom Fiscal. "
            "Extraia os seguintes dados organizados em formato de lista estilizada com negritos:\n"
            "1. Nome do Estabelecimento e CNPJ (se visível)\n"
            "2. Data e Hora da compra\n"
            "3. Lista de itens comprados (com quantidade e preço de cada um)\n"
            "4. Valor Total pago e forma de pagamento.\n"
            "Seja extremamente precisa na transcrição dos valores numéricos."
        )
        
        resultado_analise = chamar_groq_visao(base64_image, prompt)
        
        # Apaga a mensagem temporária de "escaneando" e envia a resposta real
        bot.delete_message(message.chat.id, aviso.message_id)
        bot.reply_to(message, resultado_analise)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Falha crítica no escaneamento visual: {e}")

# Handler para Conversas Livres
@bot.message_handler(func=lambda m: True)
def responder_texto_livre(message):
    if message.text.startswith('/'): return
    bot.send_chat_action(message.chat.id, 'typing')
    bot.reply_to(message, chamar_groq(message.text))

@app.route('/')
def home():
    return f"🧠 Muth AI Vision Server ONLINE - {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"

if __name__ == '__main__':
    t = threading.Thread(target=bot.infinity_polling)
    t.daemon = True
    t.start()
    app.run(host='0.0.0.0', port=10000, debug=False)
    
