import os
import asyncio
import yt_dlp
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext

# Telegram Bot Token
BOT_TOKEN = "6960970165:AAGXmlE6qInIVdS840zV40CqbG5i2fSqMSc"

# Function to search for movies
async def search_movie(movie_name):
    # Implement search logic here (Scraping, API, Torrent search, etc.)
    # Dummy response for now
    return [
        {"title": "Example Movie", "url": "https://example.com/download.mp4"}
    ]

# Function to handle /start command
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "🎬 Send a movie name to search and download!"
    )

# Function to handle user messages (movie search)
async def handle_message(update: Update, context: CallbackContext):
    movie_name = update.message.text.strip()
    results = await search_movie(movie_name)

    if not results:
        await update.message.reply_text("❌ No results found!")
        return

    buttons = [
        [InlineKeyboardButton(movie["title"], callback_data=f"movie_{idx}")]
        for idx, movie in enumerate(results)
    ]

    context.user_data["movies"] = results

    await update.message.reply_text(
        "🔍 Select the correct movie:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# Function to handle movie selection
async def movie_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    index = int(query.data.split("_")[1])
    movies = context.user_data.get("movies", [])

    if 0 <= index < len(movies):
        movie = movies[index]
        await query.edit_message_text(f"🎥 Download: {movie['url']}")
    else:
        await query.edit_message_text("❌ Invalid selection!")

# Main function to run the bot
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(movie_callback))

    print("Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
