import telebot
import yfinance as yf
import numpy as np
import requests
import json
import os
import joblib
from sklearn.neural_network import MLPClassifier
from datetime import datetime

# Token oficial da Muth
TOKEN_TELEGRAM = "8919336807:AAGTB4aRo9IkWF02_gDx4MSHv0XiuDVjHIQ"
bot = telebot.TeleBot(TOKEN_TELEGRAM)

ARQUIVO_MEMORIA = "muth_memory.pkl"
ARQUIVO_HISTORICO = "historico_muth.json"

print("=" * 50)
print("🧠 MUTH AI v4.3 — Memória Evolutiva Combinada Ativa!")
print("Aguardando interações no Telegram...")
print("=" * 50)

# 1. FUNÇÃO DE CLIMA
def pegar_clima(cidade):
    try:
        url = f"https://wttr.in/{cidade}?format=%t+%C+umidade:+%h"
        resposta = requests.get(url, timeout=5)
        return resposta.text.strip() if resposta.status_code == 200 else "Clima Indisponível"
    except:
        return "Clima Indisponível"

# 2. CARREGAR HISTÓRICO DE EXPERIÊNCIAS
def carregar_historico():
    if os.path.exists(ARQUIVO_HISTORICO):
        with open(ARQUIVO_HISTORICO, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def salvar_historico(historico):
    with open(ARQUIVO_HISTORICO, 'w', encoding='utf-8') as f:
        json.dump(historico, f, indent=2, ensure_ascii=False)

# RESPOSTA AO COMANDO /START
@bot.message_handler(commands=['start', 'help'])
def enviar_boas_vindas(message):
    boas_vindas = (
        "🧠 *Muth AI Online e Pronta!*\n\n"
        "✍️ *Comandos:*\n"
        "• `/clima NOME DA CIDADE`\n"
        "• `/analisar ATIVO SENTIMENTO` (Ex: `/analisar PETR4 otimista` ou `/analisar BTC-USD neutro`)"
    )
    bot.reply_to(message, boas_vindas, parse_mode="Markdown")

# COMANDO: /clima
@bot.message_handler(commands=['clima'])
def comando_clima(message):
    argumentos = message.text.split(maxsplit=1)
    cidade = argumentos[1] if len(argumentos) > 1 else "Duque de Caxias"
    
    bot.send_message(message.chat.id, f"🌤️ Muth consultando e registrando clima para: *{cidade}*...", parse_mode="Markdown")
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

    bot.reply_to(message, f"🌍 *CLIMA REGISTRADO NA MEMÓRIA*\n• Local: {cidade_formatada}\n• Dados: {info_clima}\n\n💡 _Minha base de dados agora tem {len(historico)} registros de experiência!_", parse_mode="Markdown")

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

        # Ajuste inteligente de Ticker (Criptos vs B3)
        if "-" in ativo or "." in ativo:
            ticker = ativo  
        else:
            ticker = f"{ativo}.SA"  

        dados = yf.download(ticker, period="2y", interval="1d", progress=False, auto_adjust=True)
        
        if dados.empty:
            bot.reply_to(message, f"❌ Não encontrei dados para `{ativo}` no Yahoo Finance. Verifique a escrita.")
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

        # Atualiza o arquivo local para a sua página web!
        conteudo_js = f"""// Gerado automaticamente pela Muth via Telegram
const dadosMuth = {{
    ativo: "{ativo}",
    decisao: "{sinal}",
    confianca: "{confianca_percentual}%",
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
            f"💻 _Painel Web atualizado localmente!_\n"
            f"📚 *Evolução da Muth:* Eu já processei *{len(historico)}* situações!"
        )
        bot.reply_to(message, resposta, parse_mode="Markdown")

    except Exception as e:
        bot.reply_to(message, f"❌ Erro no cérebro: {e}")

bot.polling()