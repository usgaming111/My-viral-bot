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

# --- FLASK SERVER (24/7 Running) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Running! @LateNight_Talks Protection Active."

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)

# --- HELPER: Subscription Check ---
async def check_subscription(user_id, context):
    not_joined = []
    for channel in MUST_JOIN_CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ['left', 'kicked', 'restricted']:
                not_joined.append(channel)
        except Exception as e:
            not_joined.append(channel) 
    return not_joined

# --- HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # Force Subscribe Check
    not_joined = await check_subscription(user_id, context)
    
    if not_joined:
        buttons = []
        for channel in not_joined:
            url = f"https://t.me/{channel.replace('@', '')}"
            buttons.append([InlineKeyboardButton(text="Join Channel", url=url)])
        
        buttons.append([InlineKeyboardButton(text="✅ Maine Join Kar Liya (Verify)", callback_data="check_join")])
        
        await update.message.reply_text(
            f"⚠️ **Access Denied!**\n\n"
            f"Bot use karne ke liye pehle hamara Channel join karein:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    # Welcome Message
    await update.message.reply_text(
        f"👋 **Hello {user.first_name}!**\n\n"
        f"✅ Verification Successful.\n"
        f"Ab aap mujhe koi bhi mobile number bhejein (Example: +91999xxxxx).\n"
        f"Main uski sim aur location bata dunga."
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    not_joined = await check_subscription(query.from_user.id, context)
    if not_joined:
        await query.message.reply_text("❌ Jhooth mat bolo! Pehle channel join karo.")
    else:
        await query.message.delete()
        await query.message.reply_text("✅ **Verified!** Ab number bhejein.")

async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Security Check
    not_joined = await check_subscription(user_id, context)
    if not_joined:
        await update.message.reply_text("❌ Aapne channel leave kar diya! Dobara join karein.")
        return

    text = update.message.text.strip()
    
    try:
        parsed_number = phonenumbers.parse(text, None)
        if not phonenumbers.is_valid_number(parsed_number):
            await update.message.reply_text("❌ Ye Number Valid Nahi Hai.")
            return

        carrier_name = carrier.name_for_number(parsed_number, "en")
        region = geocoder.description_for_number(parsed_number, "en")
        
        response = (
            f"🕵️‍♂️ **Number Info:**\n\n"
            f"📱 **Number:** `{text}`\n"
            f"📡 **Sim:** {carrier_name}\n"
            f"📍 **State:** {region}\n"
            f"🇮🇳 **Country:** India (+91)\n\n"
            f"🔥 Join: @LateNight_Talks"
        )
        await update.message.reply_text(response, parse_mode='Markdown')

    except Exception:
        await update.message.reply_text("⚠️ Kripya number sahi format mein likhein.\nExample: `+919876543210`")

def main():
    keep_alive()
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))
    
    application.run_polling()

if __name__ == '__main__':
    main()
