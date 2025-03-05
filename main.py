
import asyncio
import requests
import time
import logging
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
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

# Function to search for movies on TMDb
async def search_movies(movie_name, page=1):
    try:
        url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_name}&page={page}"
        response = requests.get(url).json()

        movies = []
        if response.get("results"):
            results = response.get("results", [])
            
            # Prioritize exact or close matches to move to the top
            exact_matches = []
            similar_matches = []
            other_matches = []
            
            # Convert search term to lowercase for case-insensitive matching
            search_lower = movie_name.lower()
            
            for movie in results:
                title = movie["title"]
                title_lower = title.lower()
                
                if title_lower == search_lower:
                    # Exact match
                    exact_matches.append(movie)
                elif search_lower in title_lower or title_lower in search_lower:
                    # Similar match - one contains the other
                    similar_matches.append(movie)
                else:
                    # Other results
                    other_matches.append(movie)
            
            # Combine the lists with exact matches first
            sorted_results = exact_matches + similar_matches + other_matches
            
            # Process the sorted results
            for movie in sorted_results[:10]:  # Get top 10 results from page
                title = movie["title"]
                release_date = movie.get("release_date", "Unknown")
                year = release_date.split("-")[0] if release_date and "-" in release_date else "Unknown"
                rating = movie.get("vote_average", "N/A")
                movie_id = movie.get("id")
                movies.append({
                    "id": movie_id,
                    "title": title,
                    "year": year,
                    "rating": rating,
                    "overview": movie.get("overview", "No overview available"),
                    "poster_path": f"https://image.tmdb.org/t/p/w500{movie['poster_path']}" if movie.get("poster_path") else None
                })
            total_pages = response.get("total_pages", 1)
            return movies, total_pages
    except Exception as e:
        logger.error(f"Error searching movies: {e}")
    
    return [], 1

# Function to get movie details from TMDb
async def get_movie_details(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}"
        response = requests.get(url).json()
        
        title = response.get("title", "Unknown")
        overview = response.get("overview", "No overview available")
        poster_path = f"https://image.tmdb.org/t/p/w500{response['poster_path']}" if response.get("poster_path") else "No poster available"
        return title, overview, poster_path
    except Exception as e:
        logger.error(f"Error getting movie details: {e}")
    
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
async def get_1337x_torrents(movie_name, page=1):
    try:
        search_url = f"https://www.1377x.to/search/{movie_name}/{page}/"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(search_url, headers=headers)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            results = soup.select("td.name a[href^='/torrent/']")

            torrents = []
            for link in results[:10]:  # Get top 10 results
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

# Function to handle user messages (movie search)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        movie_name = update.message.text
        logger.info(f"Searching for movie: {movie_name}")
        
        # Let the user know we're searching
        await update.message.reply_text("🔍 Searching for movies... Please wait!")
        
        # Store the search query in the user_data
        context.user_data["search_query"] = movie_name
        
        # Get movies
        movies, total_pages = await search_movies(movie_name)
        
        if movies:
            # Create message with movie list
            message = "🎬 *Search Results:*\n\n"
            
            keyboard = []
            for i, movie in enumerate(movies):
                year_str = f" ({movie['year']})" if movie['year'] != "Unknown" else ""
                rating_str = f" ⭐ {movie['rating']}" if movie['rating'] != "N/A" else ""
                message += f"{i+1}. *{movie['title']}*{year_str}{rating_str}\n"
                
                # Add to keyboard
                keyboard.append([InlineKeyboardButton(
                    f"{i+1}. {movie['title']}{year_str}", 
                    callback_data=f"movie_{movie['id']}"
                )])
            
            # Add pagination buttons if more than one page
            nav_buttons = []
            if total_pages > 1:
                context.user_data["current_page"] = 1
                context.user_data["total_pages"] = total_pages
                nav_buttons.append(InlineKeyboardButton("◀️ Previous", callback_data="prev_page"))
                nav_buttons.append(InlineKeyboardButton(f"1/{total_pages}", callback_data="page_info"))
                nav_buttons.append(InlineKeyboardButton("Next ▶️", callback_data="next_page"))
                keyboard.append(nav_buttons)
                
            
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)
        else:
            await update.message.reply_text("❌ No movies found.")
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text("❌ An error occurred while processing your request. Please try again later.")

# Function to handle callback queries (pagination and movie selection)
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        # Handle pagination
        if query.data == "next_page":
            current_page = context.user_data.get("current_page", 1)
            total_pages = context.user_data.get("total_pages", 1)
            
            if current_page < total_pages:
                context.user_data["current_page"] = current_page + 1
                await update_movies_list(query, context)
        
        elif query.data == "prev_page":
            current_page = context.user_data.get("current_page", 1)
            
            if current_page > 1:
                context.user_data["current_page"] = current_page - 1
                await update_movies_list(query, context)
        
        # Handle movie selection
        elif query.data.startswith("movie_"):
            movie_id = query.data.split("_")[1]
            await show_movie_details(query, context, movie_id)
            
        
    
    except Exception as e:
        logger.error(f"Error handling callback: {e}")
        await query.edit_message_text("❌ An error occurred while processing your request. Please try again later.")

# Function to update the movies list with pagination
async def update_movies_list(query, context):
    try:
        search_query = context.user_data.get("search_query", "")
        current_page = context.user_data.get("current_page", 1)
        
        # Get movies for the current page
        movies, total_pages = await search_movies(search_query, current_page)
        
        if movies:
            # Create message with movie list
            message = "🎬 *Search Results:*\n\n"
            
            keyboard = []
            for i, movie in enumerate(movies):
                year_str = f" ({movie['year']})" if movie['year'] != "Unknown" else ""
                rating_str = f" ⭐ {movie['rating']}" if movie['rating'] != "N/A" else ""
                message += f"{i+1}. *{movie['title']}*{year_str}{rating_str}\n"
                
                # Add to keyboard
                keyboard.append([InlineKeyboardButton(
                    f"{i+1}. {movie['title']}{year_str}", 
                    callback_data=f"movie_{movie['id']}"
                )])
            
            # Add pagination buttons
            nav_buttons = []
            nav_buttons.append(InlineKeyboardButton("◀️ Previous", callback_data="prev_page"))
            nav_buttons.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="page_info"))
            nav_buttons.append(InlineKeyboardButton("Next ▶️", callback_data="next_page"))
            keyboard.append(nav_buttons)
            
            
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, parse_mode="Markdown", reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error updating movies list: {e}")

# Function to show movie details and torrents
async def show_movie_details(query, context, movie_id):
    try:
        # Get movie details
        title, overview, poster = await get_movie_details(movie_id)
        
        if title:
            # Get torrents
            yts_links = await get_yts_torrents(title)
            x1337_links = await get_1337x_torrents(title)
            
            torrent_message = "🔗 *Download Links:*\n"
            if yts_links:
                torrent_message += f"\n📥 *YTS Torrents:*\n{yts_links}"
            if x1337_links:
                torrent_message += f"\n📥 *1337x Torrents:*\n{x1337_links}"
            if not yts_links and not x1337_links:
                torrent_message += "❌ No torrents found."
            
            # Create keyboard with back button
            keyboard = [
                [InlineKeyboardButton("◀️ Back to Results", callback_data="prev_page")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = f"🎬 *{title}*\n\n📖 {overview}\n🖼 {poster}\n\n{torrent_message}"
            await query.edit_message_text(message, parse_mode="Markdown", reply_markup=reply_markup, disable_web_page_preview=False)
        else:
            await query.edit_message_text("❌ Movie details not found.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Back", callback_data="prev_page")]]))
    except Exception as e:
        logger.error(f"Error showing movie details: {e}")
        await query.edit_message_text("❌ An error occurred while fetching movie details. Please try again.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Back", callback_data="prev_page")]]))

# Main function to run the bot
async def main():
    try:
        app = Application.builder().token(BOT_TOKEN).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.add_handler(CallbackQueryHandler(handle_callback))

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
