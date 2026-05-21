# =========================================================
# CONFIGURAÇÕES DE CRIPTOGRAFIA E CHAVES (PRODUÇÃO SEGURA)
# =========================================================
# O código agora lê as chaves direto da memória protegida do Render
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Inicialização dos Serviços principais
bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)
