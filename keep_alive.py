import threading
import logging
from flask import Flask, render_template_string

# Configure logging
logger = logging.getLogger('keep_alive')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Create Flask app
app = Flask(__name__)

@app.route('/')
def home():
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Editor's Helper Discord Bot</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #1e1e1e;
                color: #f0f0f0;
            }
            .container {
                background-color: #2d2d2d;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            }
            h1 {
                color: #7289da;
                text-align: center;
            }
            .status {
                background-color: #3a3a3a;
                border-radius: 5px;
                padding: 10px;
                margin-top: 20px;
            }
            .commands {
                margin-top: 20px;
            }
            .command {
                background-color: #3a3a3a;
                border-radius: 5px;
                padding: 10px;
                margin-bottom: 10px;
            }
            .online {
                color: #43b581;
                font-weight: bold;
            }
            .footer {
                margin-top: 20px;
                text-align: center;
                font-size: 12px;
                color: #999;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎬 Editor's Helper Discord Bot</h1>
            
            <div class="status">
                <p>Bot Status: <span class="online">Online</span></p>
                <p>This page indicates that the Discord bot is currently running.</p>
            </div>
            
            <div class="commands">
                <h2>Available Commands</h2>
                
                <div class="command">
                    <h3>!help or !hi</h3>
                    <p>Get a simple greeting in your DMs</p>
                </div>
                
                <div class="command">
                    <h3>!list</h3>
                    <p>View all available commands</p>
                </div>
                
                <div class="command">
                    <h3>!files</h3>
                    <p>View available files</p>
                </div>
                
                <div class="command">
                    <h3>!software_list</h3>
                    <p>View all software-related commands</p>
                </div>
                
                <div class="command">
                    <h3>!presets</h3>
                    <p>View all color correction presets (.ffx files)</p>
                </div>
                
                <div class="command">
                    <h3>Software Commands</h3>
                    <p>!aecrack, !pscrack, !mecrack, !prcrack, !topazcrack</p>
                </div>
            </div>
            
            <div class="footer">
                <p>This bot serves as a helper for video editors, providing color correction presets and information.</p>
                <p>Created by bmr</p>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/ping')
def ping():
    return 'Pong! Bot is online.', 200
    
@app.route('/')
def index():
    """Make the root URL return a success for UptimeRobot"""
    return 'Discord bot is online! Ping endpoint working.', 200

@app.route('/restart')
def restart():
    import subprocess
    import threading
    
    def restart_bot():
        try:
            subprocess.run(['bash', 'restart.sh'])
            logger.info("Restart script executed")
        except Exception as e:
            logger.error(f"Error restarting bot: {str(e)}")
    
    # Run restart in background
    thread = threading.Thread(target=restart_bot)
    thread.daemon = True
    thread.start()
    
    return 'Restart initiated. Bot should restart shortly.', 200

@app.route('/healthcheck')
def healthcheck():
    """Advanced health check that verifies the bot is actually running
    by checking the heartbeat file"""
    import os
    import time
    
    try:
        # Check if heartbeat file exists and is recent
        if os.path.exists('.heartbeat'):
            with open('.heartbeat', 'r') as f:
                last_heartbeat = float(f.read().strip())
                
            # Check if heartbeat is more than 5 minutes old
            if time.time() - last_heartbeat > 300:
                logger.warning("Heartbeat file is too old, bot might be stuck")
                # Automatically trigger restart
                import subprocess
                thread = threading.Thread(target=lambda: subprocess.run(['bash', 'restart.sh']))
                thread.daemon = True
                thread.start()
                return 'Bot heartbeat stale - restarting', 200
            else:
                return 'Bot is healthy', 200
        else:
            logger.warning("No heartbeat file found, bot might not be running properly")
            return 'No heartbeat file found - bot may not be running properly', 503
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return f'Health check error: {str(e)}', 500

def run_webserver():
    """Run the Flask web server in a thread."""
    import os
    try:
        # Get port from environment or use default
        port = int(os.environ.get('PORT', 8080))
        logger.info(f"Starting web server on port {port}")
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        logger.error(f"Web server error: {str(e)}")
        # Restart web server if it crashes
        logger.info("Attempting to restart web server...")
        run_webserver()

def keep_alive():
    """
    Create and start a web server in a new thread.
    This ensures the Replit project stays "awake".
    """
    server_thread = threading.Thread(target=run_webserver)
    server_thread.daemon = True
    server_thread.start()
    logger.info("Keep alive server started")