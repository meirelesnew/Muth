import telebot
import yfinance as yf
import numpy as np
import requests
import json
import os
import joblib
from sklearn.neural_network import MLPClassifier
from datetime import datetime
from google import genai

# CONFIGURAÇÕES — TOKENS OFICIAIS (CHAVE DO GEMINI ATIVADA)
TOKEN_TELEGRAM = "8919336807:AAGTB4aRo9IkWF02_gDx4MSHv0XiuDVjHIQ"
GEMINI_API_KEY = "AIzaSyAjugfqVYR2oIHQxLd8MFpZdkA18vIMIC8"

# Inicializando os robôs
bot = telebot.TeleBot(TOKEN_TELEGRAM)
ai_client = genai.Client(api_key=GEMINI_API_KEY)

ARQUIVO_MEMORIA = "muth_memory.pkl"
ARQUIVO_HISTORICO = "historico_muth.json"

print("=" * 50)
print("🧠 MUTH AI v5.2 — Modo Híbrido Conversacional Ativo!")
print("Google Gemini totalmente integrado com a Chave do Mestre Meireles.")
print("Aguardando comandos ou conversas livres no Telegram...")
print("=" * 50)

# 1. FUNÇÃO DE CLIMA
def pegar_clima(cidade):
    try:
        url = f"https://wttr.in/{cidade}?format=%t+%C+umidade:+%h"
        resposta = requests.get(url, timeout=5)
        return resposta.text.strip() if resposta.status_code == 200 else "Clima Indisponível"
    except:
        return "Clima Indisponível"

# 2. CARREGAR/SALVAR HISTÓRICO
def carregar_historico():
    if os.path.exists(ARQUIVO_HISTORICO):
        with open(ARQUIVO_HISTORICO, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def salvar_historico(historico):
    with open(ARQUIVO_HISTORICO, 'w', encoding='utf-8') as f:
        json.dump(historico, f, indent=2, ensure_ascii=False)

# COMANDO: /start
@bot.message_handler(commands=['start', 'help'])
def enviar_boas_vindas(message):
    boas_vindas = (
        "🧠 *Muth AI v5.2 — Modo Conversacional Ativo!*\n\n"
        "Agora eu possuo uma rede neural de mercado local E o cérebro do Google Gemini combinados!\n\n"
        "✍️ *Comandos Estruturados:*\n"
        "• `/clima CIDADE` — Registra o clima atual.\n"
        "• `/analisar ATIVO SENTIMENTO` — Treina minha rede neural.\n\n"
        "💬 *Conversa Livre:*\n"
        "• Pode me enviar qualquer pergunta ou mensagem direta no chat (como perguntas sobre trânsito, programação ou investimentos) que eu responderei usando o Gemini!"
    )
    bot.reply_to(message, boas_vindas, parse_mode="Markdown")

# COMANDO: /clima (Linha 72 corrigida sem operador morsa)
@bot.message_handler(commands=['clima'])
def comando_clima(message):
    argumentos = message.text.split(maxsplit=1)
    cidade = argumentos[1] if len(argumentos) > 1 else "Duque de Caxias"
    
    bot.send_message(message.chat.id, f"🌤️ Muth consultando clima para: *{cidade}*...", parse_mode="Markdown")
    info_clima = pegar_clima(cidade)
    
    cidade_formatada = cidade.title()
    historico = carregar_historico()
    historico.append({
        "tipo": "pesquisa_clima",
        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "local": cidade_formatada,
        "dados": info_clima
    })
    salvar_historico(historico)

    bot.reply_to(message, f"🌍 *CLIMA REGISTRADO NA MEMÓRIA*\n• Local: {cidade_formatada}\n• Dados: {info_clima}", parse_mode="Markdown")

# COMANDO: /analisar
@bot.message_handler(commands=['analisar'])
def iniciar_analise(message):
    try:
        argumentos = message.text.split()
        if len(argumentos) < 3:
            bot.reply_to(message, "✍️ Mestre, use: `/analisar ATIVO SENTIMENTO`", parse_mode="Markdown")
            return

        ativo = argumentos[1].upper()
        sentimento_texto = argumentos[2].lower()
        sentimento = 0.8 if sentimento_texto in ["otimista", "bom", "alta"] else (0.2 if sentimento_texto in ["pessimista", "ruim", "queda"] else 0.5)

        bot.send_message(message.chat.id, f"🧠 Muth processando... Carregando rede neural e adaptando ao ativo {ativo}.")

        if "-" in ativo or "." in ativo:
            ticker = ativo  
        else:
            ticker = f"{ativo}.SA"  

        dados = yf.download(ticker, period="2y", interval="1d", progress=False, auto_adjust=True)
        
        if dados.empty:
            bot.reply_to(message, f"❌ Não encontrei dados para `{ativo}` no Yahoo Finance.")
            return

        dados['Retorno'] = dados['Close'].pct_change()
        dados['Alvo'] = np.where(dados['Retorno'].shift(-1) > 0, 1, 0)
        dados = dados.dropna()

        X, y = [], []
        for i in range(len(dados) - 4):
            X.append(dados['Retorno'].iloc[i:i+4].values)
            y.append(dados['Alvo'].iloc[i+3])
        X, y = np.array(X), np.array(y)

        if os.path.exists(ARQUIVO_MEMORIA):
            model = joblib.load(ARQUIVO_MEMORIA)
        else:
            model = MLPClassifier(hidden_layer_sizes=(32, 16), max_iter=10, warm_start=True, random_state=42)

        model.max_iter += 5
        model.fit(X, y)
        joblib.dump(model, ARQUIVO_MEMORIA)

        ultimos_dias = dados['Retorno'].iloc[-4:].values.reshape(1, 4)
        previsao = model.predict_proba(ultimos_dias)[0][1]

        gatilho_exigido = 0.52 + (0.5 - sentimento) * 0.1
        sinal = "COMPRAR 🚀" if previsao > gatilho_exigido else "AGUARDAR ⏳"
        confianca_percentual = round(float(previsao) * 100, 1)

        historico = carregar_historico()
        historico.append({
            "tipo": "analise_mercado",
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ativo": ativo,
            "sentimento_mestre": sentimento_texto,
            "previsao_ia": round(float(previsao), 4),
            "decisao": sinal
        })
        salvar_historico(historico)

        conteudo_js = f"""// Gerado automaticamente pela Muth via Telegram
const dadosMuth = {{
    ativo: "{ativo}",
    ticker: "{ativo}",
    decisao: "{sinal}",
    sinal: "{sinal}",
    decisao_ia: "{sinal}",
    confianca: "{confianca_percentual}%",
    porcentagem: "{confianca_percentual}%",
    ultimaAtualizacao: "{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
}};
"""
        with open("dados_muth.js", "w", encoding="utf-8") as f:
            f.write(conteudo_js)

        resposta = (
            f"🔮 *RELATÓRIO NEURAL EVOLUTIVO*\n"
            f"-----------------------------------------\n"
            f"🎯 *Ativo:* {ativo}\n"
            f"📈 *Confiança Acumulada:* {confianca_percentual}%\n"
            f"🚨 *Decisão:* *{sinal}*\n"
            f"-----------------------------------------\n"
            f"💻 _Painel Web sincronizado!_\n"
            f"📚 *Evolução da Muth:* Eu já processei *{len(historico)}* situações!"
        )
        bot.reply_to(message, resposta, parse_mode="Markdown")

    except Exception as e:
        bot.reply_to(message, f"❌ Erro no cérebro: {e}")

# 🚀 MANIPULADOR CONVERSACIONAL COM GOOGLE GEMINI
@bot.message_handler(func=lambda message: True)
def conversar_com_gemini(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        horario_atual = datetime.now().strftime("%H:%M")
        
        prompt_muth = (
            f"Você é a Muth AI, uma Inteligência Artificial Solo e Independente focada em investimentos, "
            f"criada pelo mestre Meireles. Responda de forma direta, inteligente, com emojis. "
            f"Instrução de contexto: O horário atual no sistema do mestre é {horario_atual}. Se ele perguntar sobre "
            f"trânsito, responda que você não possui mapas em tempo real por ser focada em dados neurais e finanças, "
            f"mas faça um comentário inteligente sobre a tendência de fluxo com base no horário informado ({horario_atual}). "
            f"Pergunta do mestre: {message.text}"
        )
        
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_muth,
        )
        
        bot.reply_to(message, response.text)
        
    except Exception as e:
        bot.reply_to(message, f"🤖 Tentei pensar usando o Gemini, mas deu um erro: {e}")

bot.polling()