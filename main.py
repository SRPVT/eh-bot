# This file serves dual purposes:
# 1. Entry point for the Discord bot
# 2. Web server endpoint (app) for the gunicorn workflow

import logging
import time
import sys
import os
import threading
from bot import run_bot
from keep_alive import app, keep_alive

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('main')

def run_discord_bot_with_restart():
    """Run the Discord bot with automatic restart on crash"""
    max_retries = 5
    retry_count = 0
    
    while True:
        try:
            logger.info("Starting Discord bot...")
            run_bot()
        except Exception as e:
            retry_count += 1
            logger.error(f"Discord bot crashed: {str(e)}")
            
            if retry_count >= max_retries:
                logger.critical(f"Too many retries ({retry_count}). Performing full restart...")
                retry_count = 0
                try:
                    # Try to run the restart script
                    import subprocess
                    subprocess.Popen(["bash", "restart.sh"])
                    # Give it time to start restarting before we continue
                    time.sleep(5)
                except Exception as restart_error:
                    logger.error(f"Error running restart script: {restart_error}")
            
            logger.info(f"Restarting Discord bot in 10 seconds... (Attempt {retry_count})")
            time.sleep(10)
            continue

def create_heartbeat():
    """Create a heartbeat file to show the bot is alive"""
    while True:
        try:
            with open('.heartbeat', 'w') as f:
                f.write(str(time.time()))
            logger.debug("Heartbeat updated")
        except Exception as e:
            logger.error(f"Error writing heartbeat: {e}")
        time.sleep(60)  # Update every minute

if __name__ == "__main__":
    # Start the web server in a separate thread to keep the bot alive
    keep_alive()
    
    # Start heartbeat thread
    heartbeat_thread = threading.Thread(target=create_heartbeat)
    heartbeat_thread.daemon = True
    heartbeat_thread.start()
    
    # Run the Discord bot with automatic restarts
    run_discord_bot_with_restart()
