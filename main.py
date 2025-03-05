
import asyncio
import requests
import time
import logging
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import nest_asyncio

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# API Keys
TMDB_API_KEY = "bcadb817e29b815d64826bbf1c92b6ba"  # Get from https://www.themoviedb.org/settings/api
BOT_TOKEN = "6960970165:AAGXmlE6qInIVdS840zV40CqbG5i2fSqMSc"  # Get from BotFather

# Function to search for a movie on TMDb
async def search_movie(movie_name):
    try:
        url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_name}"
        response = requests.get(url).json()

        if response.get("results"):
            movie = response["results"][0]
            title = movie["title"]
            overview = movie.get("overview", "No overview available")
            poster_path = f"https://image.tmdb.org/t/p/w500{movie['poster_path']}" if movie.get("poster_path") else "No poster available"
            return title, overview, poster_path
    except Exception as e:
        logger.error(f"Error searching movie: {e}")
    
    return None, None, None

# Function to get movie torrents from YTS
async def get_yts_torrents(movie_name):
    try:
        url = f"https://yts.mx/api/v2/list_movies.json?query_term={movie_name}"
        response = requests.get(url).json()

        if response.get("data", {}).get("movie_count", 0) > 0:
            movies = response["data"]["movies"]
            torrents = movies[0]["torrents"]
            torrent_links = "\n".join([f"{torrent['quality']} - [Download]({torrent['url']})" for torrent in torrents])
            return torrent_links
    except Exception as e:
        logger.error(f"Error getting YTS torrents: {e}")
    
    return None

# Function to get movie torrents from 1337x
async def get_1337x_torrents(movie_name):
    try:
        search_url = f"https://www.1377x.to/search/{movie_name}/1/"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(search_url, headers=headers)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            results = soup.select("td.name a[href^='/torrent/']")

            torrents = []
            for link in results[:5]:  # Get top 5 results
                torrent_title = link.text
                torrent_page_url = "https://www.1377x.to" + link["href"]
                torrents.append(f"🔹 {torrent_title} - [Download]({torrent_page_url})")

            return "\n".join(torrents) if torrents else None
    except Exception as e:
        logger.error(f"Error getting 1337x torrents: {e}")
    
    return None

# Function to handle /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎬 Welcome! Send me a movie name, and I'll find details and download links for you.")

# Function to handle user messages (movie search + torrents)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        movie_name = update.message.text
        logger.info(f"Searching for movie: {movie_name}")
        
        title, overview, poster = await search_movie(movie_name)

        if title:
            yts_links = await get_yts_torrents(movie_name)
            x1337_links = await get_1337x_torrents(movie_name)

            torrent_message = "🔗 *Download Links:*\n"
            if yts_links:
                torrent_message += f"\n📥 *YTS Torrents:*\n{yts_links}"
            if x1337_links:
                torrent_message += f"\n📥 *1337x Torrents:*\n{x1337_links}"
            if not yts_links and not x1337_links:
                torrent_message += "❌ No torrents found."

            message = f"🎬 *{title}*\n\n📖 {overview}\n🖼 {poster}\n\n{torrent_message}"
            await update.message.reply_text(message, parse_mode="Markdown", disable_web_page_preview=False)
        else:
            await update.message.reply_text("❌ Movie not found.")
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text("❌ An error occurred while processing your request. Please try again later.")

# Main function to run the bot
async def main():
    try:
        app = Application.builder().token(BOT_TOKEN).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        logger.info("Bot is running...")
        await app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        return False
    return True

# Function to keep the bot running
async def keep_running():
    while True:
        try:
            logger.info("Starting bot...")
            success = await main()
            if not success:
                logger.error("Bot stopped unexpectedly. Restarting in 10 seconds...")
                await asyncio.sleep(10)
            else:
                break
        except Exception as e:
            logger.error(f"Unexpected error: {e}. Restarting in 10 seconds...")
            await asyncio.sleep(10)

# Run the bot
if __name__ == "__main__":
    try:
        nest_asyncio.apply()
        asyncio.run(keep_running())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"Critical error: {e}")
