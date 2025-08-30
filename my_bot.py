import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import aiohttp
import requests # पिंग करने के लिए requests की ज़रूरत होगी
import os
import time
import threading # पिंग को बैकग्राउंड में चलाने के लिए
import uuid

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

# यह फ़ंक्शन हर 2 मिनट में बॉट के Webhook URL को पिंग करेगा
def pinger():
    while True:
        try:
            logging.info("Pinging the bot to keep it alive...")
            requests.get(WEBHOOK_URL + '/' + TOKEN)
        except Exception as e:
            logging.error(f"Error pinging the bot: {e}")
        
        # 2 मिनट (120 सेकंड) के लिए रुकें
        time.sleep(120)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        file_code = context.args[0]
        api_url = f"{SUPABASE_URL}/rest/v1/files_data"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        params = {
            "select": "file_id,title",
            "file_code": f"eq.{file_code}"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=headers, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()
            
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
                
        except aiohttp.ClientError as e:
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
        try:
            video_file_id = update.message.video.file_id
            
            # 1. वीडियो का कैप्शन (टाइटल) लें
            # अगर वीडियो में कैप्शन है तो उसे इस्तेमाल करें, वरना 'No Title' रखें।
            video_caption = update.message.caption if update.message.caption else "No Title"

            # 2. एक यूनिक कोड (UUID) जेनरेट करें
            file_code = str(uuid.uuid4())
            
            # 3. Supabase में डेटा सेव करें (अब टाइटल भी साथ में)
            api_url = f"{SUPABASE_URL}/rest/v1/files_data"
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            }
            data_to_save = {
                "file_id": video_file_id,
                "file_code": file_code,
                "title": video_caption  # यहां टाइटल जोड़ा गया है
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, headers=headers, json=data_to_save) as response:
                    response.raise_for_status()
            
            # 4. तीन अलग-अलग मैसेज भेजें
            # पहला मैसेज: फाइल ID
            await update.message.reply_text(f"**फाइल ID:**\n`{video_file_id}`", parse_mode='Markdown')
            
            # दूसरा मैसेज: डाउनलोड कोड
            await update.message.reply_text(f"**डाउनलोड कोड:**\n`{file_code}`", parse_mode='Markdown')

            # तीसरा मैसेज: डाउनलोड लिंक
            download_link = f"https://t.me/Movieshubfilesdlbot?start={file_code}"
            await update.message.reply_text(f"**डाउनलोड लिंक:**\n`{download_link}`", parse_mode='Markdown')
            
        except aiohttp.ClientError as e:
            logging.error(f"Error saving data to Supabase: {e}")
            await update.message.reply_text("Supabase में डेटा सेव करते समय कोई गड़बड़ी हो गई। कृपया फिर से कोशिश करें।")
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            await update.message.reply_text("कोई अनपेक्षित गड़बड़ी हो गई।")
            

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("I am a downloader bot. To get a file, use the /start command with a valid file code.")

def main():
    # पिंगर थ्रेड शुरू करें
    pinger_thread = threading.Thread(target=pinger, daemon=True)
    pinger_thread.start()

    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.VIDEO & ~filters.COMMAND, handle_video))
    
    application.run_webhook(listen="0.0.0.0",
                            port=PORT,
                            url_path=TOKEN,
                            webhook_url=WEBHOOK_URL + '/' + TOKEN)

if __name__ == '__main__':
    main()
    
