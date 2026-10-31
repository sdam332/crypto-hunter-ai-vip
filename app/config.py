import os
from dotenv import load_dotenv
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "").strip()
REPORT_INTERVAL_HOURS = max(1, int(os.getenv("REPORT_INTERVAL_HOURS", "12")))
SCAN_INTERVAL_SECONDS = max(30, int(os.getenv("SCAN_INTERVAL_SECONDS", "60")))
TOP_N = min(30, max(1, int(os.getenv("TOP_N", "30"))))
QUOTE = os.getenv("QUOTE_CURRENCY", "USDT").upper()
APPROVED = {x.strip().upper() for x in os.getenv("SHARIAH_APPROVED_SYMBOLS", "").split(",") if x.strip()}
