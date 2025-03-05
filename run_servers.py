
import asyncio
import threading
import os
from flask_server import app
import nest_asyncio
import logging
from main import keep_running

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def run_flask():
    """Run the Flask web server"""
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

async def main():
    """Main function to run both servers"""
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    logger.info("Flask server started")
    
    # Run Telegram bot in main thread
    await keep_running()

if __name__ == "__main__":
    try:
        nest_asyncio.apply()
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Servers stopped by user.")
    except Exception as e:
        logger.error(f"Critical error: {e}")
