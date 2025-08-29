import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import requests
import os

TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ADMIN_ID = 1306579102  

# Webhook के लिए जरूरी
PORT = int(os.environ.get('PORT', '8443'))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # आपका पिछला code यहाँ रहेगा...
    if context.args:
        file_code = context.args[0]
        # Supabase API endpoint
        api_url = f"{SUPABASE_URL}/rest/v1/files_data"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        params = {
            "select": "file_id,title",
            "file_code": f"eq.{file_code}"
        }
        
        try:
            response = requests.get(api_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data and len(data) > 0:
                file_id = data[0]['file_id']
                file_title = data[0].get('title', "Movieshub.org")
                
                caption_text = f"**{file_title}**\n\nHere is your requested file! Thank you for visiting https://movieshub.in.net/"
                
                await context.bot.send_video(
                    chat_id=update.effective_chat.id,
                    video=file_id,
                    caption=caption_text,
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(f"Invalid code: {file_code}")
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching data from Supabase: {e}")
            await update.message.reply_text("An error occurred. Please try again later.")

    else:
        await update.message.reply_text(
    "🎉 Welcome to MoviesHub Bot! 🎉\n\n"
    "Sabse pehle aapko apni movie yaha se search karni hogi 👇\n"
    "🌐 Website: https://movieshub.in.net/\n\n"
    "Waha jaake jab aap \"Download\" button pe click karoge,\n"
    "tab aapko yahi bot aapka movie download karne me help karega. ✅\n\n"
    "Enjoy! 🍿"
        )

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        video_file_id = update.message.video.file_id
        await update.message.reply_text(video_file_id)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("I am a downloader bot. To get a file, use the /start command with a valid file code.")

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.VIDEO & ~filters.COMMAND, handle_video))
    
    # यह नई line polling की जगह webhook के लिए है
    application.run_webhook(listen="0.0.0.0",
                            port=PORT,
                            url_path=TOKEN,
                            webhook_url=WEBHOOK_URL + '/' + TOKEN)

if __name__ == '__main__':
    main()

