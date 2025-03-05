
import asyncio
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# API Keys
TMDB_API_KEY = "bcadb817e29b815d64826bbf1c92b6ba"  # Get from https://www.themoviedb.org/settings/api
BOT_TOKEN = "6960970165:AAGXmlE6qInIVdS840zV40CqbG5i2fSqMSc"  # Get from BotFather

# Function to search for a movie on TMDb
async def search_movie(movie_name):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_name}"
    response = requests.get(url).json()

    if response["results"]:
        movie = response["results"][0]
        title = movie["title"]
        overview = movie["overview"]
        poster_path = f"https://image.tmdb.org/t/p/w500{movie['poster_path']}" if movie.get("poster_path") else "No poster available"
        return title, overview, poster_path

    return None, None, None

# Function to get movie torrents from YTS
async def get_yts_torrents(movie_name):
    url = f"https://yts.mx/api/v2/list_movies.json?query_term={movie_name}"
    response = requests.get(url).json()

    if response["data"]["movie_count"] > 0:
        movies = response["data"]["movies"]
        torrents = movies[0]["torrents"]
        torrent_links = "\n".join([f"{torrent['quality']} - [Download]({torrent['url']})" for torrent in torrents])
        return torrent_links

    return None

# Function to get movie torrents from 1337x
async def get_1337x_torrents(movie_name):
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
    return None

# Function to handle /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎬 Welcome! Send me a movie name, and I'll find details and download links for you.")

# Function to handle user messages (movie search + torrents)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    movie_name = update.message.text
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

# Main function to run the bot
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    await app.run_polling()

# Run the bot
if __name__ == "__main__":
    try:
        import nest_asyncio
        nest_asyncio.apply()
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped.")
