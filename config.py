import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger('discord_bot')

def load_config():
    """
    Load configuration from environment variables.
    Returns a dictionary with configuration values.
    """
    # Load environment variables from .env file if it exists
    load_dotenv()
    
    # Configuration dictionary
    config = {
        'DISCORD_TOKEN': os.getenv('DISCORD_TOKEN'),
    }
    
    # Check if required configurations are present
    if not config['DISCORD_TOKEN']:
        logger.warning("DISCORD_TOKEN not found in environment variables.")
    
    return config
