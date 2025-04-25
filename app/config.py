import os
from dotenv import load_dotenv

from promting import inicial_start_promt

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_MODEL = "gpt-4.1-mini"
SYSTEM_PROMPT = inicial_start_promt()