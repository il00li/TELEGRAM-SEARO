"""
Flask Web Application with Telegram Bot Integration
Fixed for Render.com deployment with proper error handling
"""
import os
import logging
import json
from flask import Flask, request, render_template, jsonify, redirect, url_for, flash
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
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key_for_render")

# Initialize database and bot handler
db = Database()
bot_handler = TelegramBotHandler()

@app.route('/')
def home():
    """Home page with bot status and statistics"""
    try:
        stats = db.get_bot_statistics()
        return render_template('index.html', stats=stats)
    except Exception as e:
        logger.error(f"Error loading home page: {e}")
        return render_template('index.html', stats={
            'total_users': 0,
            'total_searches': 0,
            'active_channels': 0,
            'banned_users': 0
        })

@app.route('/admin')
def admin_panel():
    """Admin panel for bot management"""
    try:
        users = db.get_all_users()
        channels = db.get_mandatory_channels()
        recent_searches = db.get_recent_searches(limit=50)
        stats = db.get_bot_statistics()
        
        return render_template('admin.html', 
                             users=users, 
                             channels=channels, 
                             recent_searches=recent_searches,
                             stats=stats)
    except Exception as e:
        logger.error(f"Error loading admin panel: {e}")
        return render_template('admin.html', 
                             users=[], 
                             channels=[], 
                             recent_searches=[],
                             stats={})

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

@app.route('/api/ban_user/<int:user_id>', methods=['POST'])
def ban_user(user_id):
    """Ban a user via API"""
    try:
        db.ban_user(user_id)
        return jsonify({'success': True, 'message': f'User {user_id} banned successfully'})
    except Exception as e:
        logger.error(f"Error banning user {user_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/unban_user/<int:user_id>', methods=['POST'])
def unban_user(user_id):
    """Unban a user via API"""
    try:
        db.unban_user(user_id)
        return jsonify({'success': True, 'message': f'User {user_id} unbanned successfully'})
    except Exception as e:
        logger.error(f"Error unbanning user {user_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/broadcast', methods=['POST'])
def broadcast_message():
    """Broadcast message to all users"""
    try:
        message = None
        if request.json:
            message = request.json.get('message')
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400
        
        result = bot_handler.broadcast_message(message)
        return jsonify({
            'success': True, 
            'message': f'Broadcast sent to {result["sent"]} users, {result["failed"]} failed'
        })
    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Configure for Render deployment
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Flask server on port {port}")
    logger.info(f"Debug mode: {debug_mode}")
    
    # Initialize webhook
    try:
        webhook_url = os.environ.get('WEBHOOK_URL', 'https://telegram-oihp.onrender.com/webhook')
        bot_handler.set_webhook(webhook_url)
        logger.info(f"Webhook set to: {webhook_url}")
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}")
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
