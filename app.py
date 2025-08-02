"""
Telegram Bot Application
Optimized for Render.com deployment with Telegram-only interface
"""
import os
import logging
import json
from flask import Flask, request, jsonify
from bot_handler import TelegramBotHandler
from database import Database

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "telegram_bot_secret_key_2025")

# Initialize database and bot handler
db = Database()
bot_handler = TelegramBotHandler()

@app.route('/')
def home():
    """Simple status page"""
    try:
        stats = db.get_bot_statistics()
        return jsonify({
            'status': 'running',
            'bot_name': 'Pixabay Search Bot',
            'admin_interface': 'Telegram only - use /admin command',
            'stats': stats
        })
    except Exception as e:
        logger.error(f"Error loading status: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle Telegram webhook requests"""
    try:
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = json.loads(json_string)
            
            # Process the update
            result = bot_handler.process_update(update)
            
            if result:
                return 'OK', 200
            else:
                return 'Error processing update', 500
        else:
            logger.warning("Invalid content type for webhook")
            return 'Invalid content type', 400
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return 'Invalid JSON', 400
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return 'Internal server error', 500

@app.route('/health')
def health_check():
    """Health check endpoint for Render"""
    try:
        # Check database connection
        db.check_connection()
        
        # Check bot status
        bot_status = bot_handler.check_bot_status()
        
        return jsonify({
            'status': 'healthy',
            'bot_status': bot_status,
            'database': 'connected'
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500



if __name__ == '__main__':
    # Configure for Render deployment
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Flask server on port {port}")
    logger.info(f"Debug mode: {debug_mode}")
    
    # Initialize webhook
    try:
        webhook_url = os.environ.get('WEBHOOK_URL', 'https://telegram-searo.onrender.com/webhook')
        bot_handler.set_webhook(webhook_url)
        logger.info(f"Webhook set to: {webhook_url}")
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}")
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
