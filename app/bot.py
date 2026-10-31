import asyncio, logging
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from .config import BOT_TOKEN, ADMIN_CHAT_ID, APPROVED, REPORT_INTERVAL_HOURS, SCAN_INTERVAL_SECONDS
from .market import universe, analyze, fear_greed, globals_data

logging.basicConfig(level=logging.INFO)
log=logging.getLogger("crypto_hunter")
active_plans={}  # Starter placeholder; persistent trade storage is required for production.

def permitted(update):
    return not ADMIN_CHAT_ID or str(update.effective_chat.id)==ADMIN_CHAT_ID

async def start(update:Update, context:ContextTypes.DEFAULT_TYPE):
    if permitted(update):
        await update.message.reply_text("💎 Crypto Hunter AI VIP جاهز. الأوامر: /myid /report /scan /policy /status")

async def myid(update:Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Chat ID: {update.effective_chat.id}")

async def policy(update:Update, context:ContextTypes.DEFAULT_TYPE):
    if permitted(update):
        await update.message.reply_text("Spot فقط. لا رافعة ولا Futures ولا Margin ولا Short. العملات غير المعتمدة تبقى PENDING ولا تصدر لها إشارات. هذه سياسة تقنية وليست فتوى شرعية.")

async def status(update:Update, context:ContextTypes.DEFAULT_TYPE):
    if permitted(update):
        await update.message.reply_text(f"تقرير كل {REPORT_INTERVAL_HOURS} ساعة. تحليل 30m وتأكيد 4h. لا تنفيذ صفقات.")

async def report_text():
    cap,vol,dom=await globals_data()
    fg,label=await fear_greed()
    return (f"📊 تقرير سوق الكريبتو\nالقيمة السوقية: ${cap:,.0f}\nحجم التداول 24h: ${vol:,.0f}"
            f"\nهيمنة BTC: {dom:.2f}%\nالخوف والطمع: {fg}/100 — {label}"
            f"\nالوقت: {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}")

async def report(update:Update, context:ContextTypes.DEFAULT_TYPE):
    if permitted(update):
        try: await update.message.reply_text(await report_text())
        except Exception as e: await update.message.reply_text(f"تعذر جلب التقرير: {e}")

async def scan(update:Update, context:ContextTypes.DEFAULT_TYPE):
    if not permitted(update): return
    msg=await update.message.reply_text("جارٍ تحليل العملات المتاحة...")
    try:
        ex,pairs=await universe()
        lines=["🔎 نتائج تحليل 30m مع تأكيد 4h:"]
        for coin,symbol in pairs:
            try:
                a=await asyncio.to_thread(analyze,ex,symbol)
                status="مسموح تقنياً بعد إدراجك في قائمة الاعتماد" if symbol.upper() in APPROVED else "PENDING — لا إشارة"
                lines.append(f"{symbol} | ${a['price']:.8g} | 30m {a['trend30']} | 4h {a['trend4h']} | RSI {a['rsi']:.1f} | Volume {a['volume_ratio']:.2f}x | تقييم {a['score']}/5 | {status}")
            except Exception as e: log.warning("تعذر تحليل %s: %s",symbol,e)
        text="\n".join(lines)
        for i in range(0,len(text),3800): await msg.reply_text(text[i:i+3800])
    except Exception as e: await msg.edit_text(f"تعذر إكمال التحليل: {e}")

async def scheduled_report(context:ContextTypes.DEFAULT_TYPE):
    if not ADMIN_CHAT_ID: return
    try: await context.bot.send_message(chat_id=int(ADMIN_CHAT_ID),text=await report_text())
    except Exception: log.exception("report delivery failed")

async def price_watch(context:ContextTypes.DEFAULT_TYPE):
    # Actual trade plans must be created from a validated signal engine and persisted.
    # No fake signals are generated in this starter.
    return

def main():
    if not BOT_TOKEN: raise SystemExit("أضف TELEGRAM_BOT_TOKEN في أسرار الاستضافة.")
    app=Application.builder().token(BOT_TOKEN).build()
    for cmd,fn in [("start",start),("myid",myid),("policy",policy),("status",status),("report",report),("scan",scan)]:
        app.add_handler(CommandHandler(cmd,fn))
    if app.job_queue:
        app.job_queue.run_repeating(scheduled_report,interval=REPORT_INTERVAL_HOURS*3600,first=15)
        app.job_queue.run_repeating(price_watch,interval=SCAN_INTERVAL_SECONDS,first=30)
    app.run_polling()

if __name__=="__main__": main()
