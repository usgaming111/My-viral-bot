# My-viral-bot
import logging
import os
import phonenumbers
from phonenumbers import geocoder, carrier
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- CONFIGURATION ---
TOKEN = '8400980761:AAHVe3YftHvTTFItagl8fY-rNT7FfARxtOs' 
MUST_JOIN_CHANNELS = ['@LateNight_Talks'] 

# --- SERVER ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Alive"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)

# --- SUBSCRIPTION CHECK ---
async def check_subscription(user_id, context):
    not_joined = []
    for channel in MUST_JOIN_CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ['left', 'kicked', 'restricted']:
                not_joined.append(channel)
        except:
            # Agar error aaye (jaise bot admin nahi hai), toh safe side ke liye allow kar do
            # taaki user phase nahi.
            pass
    return not_joined

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    not_joined = await check_subscription(user.id, context)
    
    if not_joined:
        buttons = []
        for channel in not_joined:
            url = f"https://t.me/{channel.replace('@', '')}"
            buttons.append([InlineKeyboardButton(text="Join Channel", url=url)])
        buttons.append([InlineKeyboardButton(text="✅ Verify", callback_data="check_join")])
        
        await update.message.reply_text(
            "⚠️ Bot use karne ke liye pehle Channel join karein:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        await update.message.reply_text("✅ Verified! Ab number bhejein (+91...)")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    not_joined = await check_subscription(query.from_user.id, context)
    if not_joined:
        await query.message.reply_text("❌ Pehle Join karo!")
    else:
        await query.message.delete()
        await query.message.reply_text("✅ Verified! Number bhejein.")

async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    not_joined = await check_subscription(user_id, context)
    if not_joined:
        await update.message.reply_text("❌ Channel leave mat karo! Dobara join karo.")
        return

    text = update.message.text.strip()
    
    try:
        # Number Parse Karna
        parsed_number = phonenumbers.parse(text, None)
        if not phonenumbers.is_valid_number(parsed_number):
            await update.message.reply_text("❌ Number Sahi Nahi Hai. (+91 lagana zaroori hai)")
            return

        # Details Nikalna
        carrier_name = carrier.name_for_number(parsed_number, "en")
        region = geocoder.description_for_number(parsed_number, "en")
        
        # Simple Message (Bina Markdown ke taaki crash na ho)
        response = (
            f"📱 Number: {text}\n"
            f"📡 Sim: {carrier_name}\n"
            f"📍 State: {region}\n"
            f"🇮🇳 Country: India\n\n"
            f"🔥 Join: @LateNight_Talks"
        )
        await update.message.reply_text(response)

    except Exception as e:
        # Error print karega taaki humein pata chale kya hua
        print(f"Error: {e}") 
        await update.message.reply_text("⚠️ Number format galat hai. Example: +919999999999")

def main():
    keep_alive()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))
    application.run_polling()

if __name__ == '__main__':
    main()
    
