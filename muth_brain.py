# ================================
# MOTOR DE BUSCA WEB (RESOLVE DADOS EM TEMPO REAL)
# ================================
def pesquisar_web(termo):
    """Busca resultados reais na internet limpando e tratando o termo"""
    try:
        # Limpa o termo de busca para remover comandos ou espaços inúteis
        termo_limpo = termo.replace("/clima", "").replace("/dolar", "").strip()
        
        with DDGS() as ddgs:
            # Força a conversão do gerador para lista e extrai os blocos de texto
            res_list = list(ddgs.text(termo_limpo, max_results=3))
            if res_list:
                resultados = [r['body'] for r in res_list if 'body' in r]
                return "\n".join(resultados)
    except Exception as e:
        print(f"Erro na busca DuckDuckGo: {e}")
    return ""

# ================================
# PROCESSADOR CENTRAL DE DECISÃO (ROTEADOR BLINDADO)
# ================================
def processar(msg): 
    # Remove espaços em branco extras e padroniza para minúsculo para a checagem
    t = msg.strip().lower()

    # Rota 1: Comando Matemático Direto
    if "fibonacci" in t or t.startswith("/fib"):
        return f"📊 Sequência Fibonacci:\n{fibonacci(10)}"

    # Rota 2: Machine Learning Local
    if any(x in t for x in ["petr4", "btc", "analise", "análise"]):
        preco, sinal = analisar_ml("PETR4")
        return f"🤖 MUTH ML ANALYSIS\nAtivo monitorado: PETR4\nPreço simulado: R$ {preco}\nSinal preditivo do modelo: {sinal}"

    # Rota 3: Consultas de Tempo Real (Dólar, Clima, Tempo, Notícias, etc)
    palavras_chave_tempo_real = ["clima", "tempo", "dolar", "dólar", "euro", "hoje", "noticia", "notícia", "/climarj"]
    if any(x in t for x in palavras_chave_tempo_real):
        dados_da_internet = pesquisar_web(msg)
        
        if dados_da_internet:
            sys_prompt = (
                "Você é a Muth AI, um assistente com acesso total à internet atualizada. "
                "Abaixo são fornecidos dados reais e recentes extraídos da web sobre a pergunta do usuário. "
                "Use ESSES DADOS para responder de forma exata, curta e direta. "
                "NUNCA diga que não tem acesso a tempo real ou que é apenas um modelo de linguagem, pois os dados estão logo abaixo. "
                "Responda de forma natural em português."
            )
            user_prompt = f"Pergunta do usuário: {msg}\n\n[DADOS REAIS DA INTERNET]:\n{dados_da_internet}"
            return perguntar_ia(sys_prompt, user_prompt)
        else:
            # Caso a busca falhe temporariamente por rede, usamos uma IA genérica mas sem desculpas formais
            sys_prompt_falha = "Você é a Muth AI. Responda à pergunta de forma direta, fazendo uma estimativa realista se necessário."
            return perguntar_ia(sys_prompt_falha, msg)
        
    # Rota 4: Conversas Gerais
    sys_prompt_geral = "Você é a Muth AI, um assistente inteligente, direto e muito prestativo. Responda de forma objetiva em português."
    return perguntar_ia(sys_prompt_geral, msg)
