# COMANDO: /analisar (Versão Atualizada: Corrige criptos e atualiza o site automaticamente)
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

        # AJUSTE INTELIGENTE DE TICKER (B3 vs Global)
        if "-" in ativo or "." in ativo:
            ticker = ativo  # Criptos (BTC-USD) ou moedas ficam puras
        else:
            ticker = f"{ativo}.SA"  # Ações brasileiras (PETR4, MXRF11) ganham .SA

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

        # 🔄 COMANDO MÁGICO: ATUALIZA O ARQUIVO DO SITE WEB LOCALMENTE
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
        bot.reply_to(message, f"❌ Erro: {e}")