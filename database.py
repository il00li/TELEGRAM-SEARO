"""
Database handler for the Telegram Bot
Improved with proper error handling and new notification features
"""
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_name='bot_database.db'):
        self.db_name = db_name
        self.init_database()

    def init_database(self):
        """Initialize database tables with improved schema"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    join_date TEXT,
                    last_activity TEXT,
                    is_banned INTEGER DEFAULT 0,
                    search_count INTEGER DEFAULT 0,
                    notification_sent INTEGER DEFAULT 0
                )
            ''')

            # Mandatory channels table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mandatory_channels (
                    channel_id TEXT PRIMARY KEY,
                    channel_username TEXT,
                    channel_title TEXT,
                    added_by INTEGER,
                    added_date TEXT,
                    is_active INTEGER DEFAULT 1
                )
            ''')

            # Search history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    query TEXT,
                    search_type TEXT,
                    timestamp TEXT,
                    results_count INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')

            # User sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    user_id INTEGER PRIMARY KEY,
                    current_query TEXT,
                    current_type TEXT,
                    current_results TEXT,
                    current_index INTEGER DEFAULT 0,
                    last_updated TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')

            # Notifications table (new)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    channel_id TEXT,
                    notification_type TEXT,
                    sent_date TEXT,
                    status TEXT DEFAULT 'sent',
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (channel_id) REFERENCES mandatory_channels (channel_id)
                )
            ''')

            # Bot statistics table (new)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bot_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    total_users INTEGER,
                    active_users INTEGER,
                    total_searches INTEGER,
                    total_channels INTEGER
                )
            ''')

            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing database: {e}")

    def check_connection(self):
        """Check database connection"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise e

    def add_user(self, user_id: int, username: str = "", first_name: str = "", last_name: str = ""):
        """Add or update user in database"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            # Check if user exists
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            exists = cursor.fetchone()

            if exists:
                # Update existing user
                cursor.execute('''
                    UPDATE users 
                    SET username = ?, first_name = ?, last_name = ?, last_activity = ?
                    WHERE user_id = ?
                ''', (username or "", first_name or "", last_name or "", datetime.now().isoformat(), user_id))
            else:
                # Insert new user
                cursor.execute('''
                    INSERT INTO users 
                    (user_id, username, first_name, last_name, join_date, last_activity, search_count)
                    VALUES (?, ?, ?, ?, ?, ?, 0)
                ''', (user_id, username or "", first_name or "", last_name or "", 
                      datetime.now().isoformat(), datetime.now().isoformat()))

            conn.commit()
            conn.close()
            logger.info(f"User {user_id} added/updated successfully")

        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")

    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user information"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT user_id, username, first_name, last_name, join_date, 
                       last_activity, is_banned, search_count, notification_sent
                FROM users WHERE user_id = ?
            ''', (user_id,))

            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    'user_id': row[0],
                    'username': row[1],
                    'first_name': row[2],
                    'last_name': row[3],
                    'join_date': row[4],
                    'last_activity': row[5],
                    'is_banned': bool(row[6]),
                    'search_count': row[7],
                    'notification_sent': bool(row[8])
                }
            return None

        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None

    def get_all_users(self) -> List[Dict]:
        """Get all users"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT user_id, username, first_name, last_name, join_date, 
                       last_activity, is_banned, search_count
                FROM users ORDER BY join_date DESC
            ''')

            rows = cursor.fetchall()
            conn.close()

            users = []
            for row in rows:
                users.append({
                    'user_id': row[0],
                    'username': row[1],
                    'first_name': row[2],
                    'last_name': row[3],
                    'join_date': row[4],
                    'last_activity': row[5],
                    'is_banned': bool(row[6]),
                    'search_count': row[7]
                })

            return users

        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []

    def ban_user(self, user_id: int):
        """Ban a user"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            cursor.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            logger.info(f"User {user_id} banned successfully")

        except Exception as e:
            logger.error(f"Error banning user {user_id}: {e}")

    def unban_user(self, user_id: int):
        """Unban a user"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            cursor.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            logger.info(f"User {user_id} unbanned successfully")

        except Exception as e:
            logger.error(f"Error unbanning user {user_id}: {e}")

    def is_user_banned(self, user_id: int) -> bool:
        """Check if user is banned"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            cursor.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            conn.close()

            return bool(result[0]) if result else False

        except Exception as e:
            logger.error(f"Error checking ban status for user {user_id}: {e}")
            return False

    def add_mandatory_channel(self, channel_id: str, channel_username: str, channel_title: str = "", added_by: int = 0):
        """Add mandatory channel"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO mandatory_channels 
                (channel_id, channel_username, channel_title, added_by, added_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (channel_id, channel_username, channel_title, added_by, datetime.now().isoformat()))

            conn.commit()
            conn.close()
            logger.info(f"Mandatory channel {channel_username} added successfully")

        except Exception as e:
            logger.error(f"Error adding mandatory channel {channel_username}: {e}")

    def get_mandatory_channels(self) -> List[Dict]:
        """Get all active mandatory channels"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT channel_id, channel_username, channel_title, added_by, added_date
                FROM mandatory_channels WHERE is_active = 1
            ''')

            rows = cursor.fetchall()
            conn.close()

            channels = []
            for row in rows:
                channels.append({
                    'channel_id': row[0],
                    'channel_username': row[1],
                    'channel_title': row[2],
                    'added_by': row[3],
                    'added_date': row[4]
                })

            return channels

        except Exception as e:
            logger.error(f"Error getting mandatory channels: {e}")
            return []

    def remove_mandatory_channel(self, channel_id: str):
        """Remove mandatory channel"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            cursor.execute("UPDATE mandatory_channels SET is_active = 0 WHERE channel_id = ?", (channel_id,))
            conn.commit()
            conn.close()
            logger.info(f"Mandatory channel {channel_id} removed successfully")

        except Exception as e:
            logger.error(f"Error removing mandatory channel {channel_id}: {e}")

    def add_notification(self, user_id: int, channel_id: str, notification_type: str):
        """Add notification record"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO notifications (user_id, channel_id, notification_type, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (user_id, channel_id, notification_type, datetime.now().isoformat()))

            conn.commit()
            conn.close()
            logger.info(f"Notification added for user {user_id}")

        except Exception as e:
            logger.error(f"Error adding notification: {e}")

    def add_search_history(self, user_id: int, query: str, search_type: str, results_count: int):
        """Add search to history"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            # Add to search history
            cursor.execute('''
                INSERT INTO search_history (user_id, query, search_type, timestamp, results_count)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, query, search_type, datetime.now().isoformat(), results_count))

            # Update user search count
            cursor.execute('''
                UPDATE users SET search_count = search_count + 1, last_activity = ?
                WHERE user_id = ?
            ''', (datetime.now().isoformat(), user_id))

            conn.commit()
            conn.close()
            logger.info(f"Search history added for user {user_id}")

        except Exception as e:
            logger.error(f"Error adding search history: {e}")

    def get_recent_searches(self, limit: int = 50) -> List[Dict]:
        """Get recent searches"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT sh.query, sh.search_type, sh.timestamp, sh.results_count,
                       u.first_name, u.username, u.user_id
                FROM search_history sh
                JOIN users u ON sh.user_id = u.user_id
                ORDER BY sh.timestamp DESC
                LIMIT ?
            ''', (limit,))

            rows = cursor.fetchall()
            conn.close()

            searches = []
            for row in rows:
                searches.append({
                    'query': row[0],
                    'search_type': row[1],
                    'timestamp': row[2],
                    'results_count': row[3],
                    'user_name': row[4],
                    'username': row[5],
                    'user_id': row[6]
                })

            return searches

        except Exception as e:
            logger.error(f"Error getting recent searches: {e}")
            return []

    def add_notification(self, user_id: int, channel_id: str, notification_type: str):
        """Add notification record"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO notifications (user_id, channel_id, notification_type, sent_date)
                VALUES (?, ?, ?, ?)
            ''', (user_id, channel_id, notification_type, datetime.now().isoformat()))

            # Mark user as notified
            cursor.execute('''
                UPDATE users SET notification_sent = 1 WHERE user_id = ?
            ''', (user_id,))

            conn.commit()
            conn.close()
            logger.info(f"Notification added for user {user_id}")

        except Exception as e:
            logger.error(f"Error adding notification: {e}")

    def get_bot_statistics(self) -> Dict:
        """Get bot statistics"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            # Total users
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]

            # Active users (searched in last 30 days)
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE last_activity > datetime('now', '-30 days')
            ''')
            active_users = cursor.fetchone()[0]

            # Total searches
            cursor.execute("SELECT COUNT(*) FROM search_history")
            total_searches = cursor.fetchone()[0]

            # Banned users
            cursor.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
            banned_users = cursor.fetchone()[0]

            # Active channels
            cursor.execute("SELECT COUNT(*) FROM mandatory_channels WHERE is_active = 1")
            active_channels = cursor.fetchone()[0]

            # Recent searches (last 24 hours)
            cursor.execute('''
                SELECT COUNT(*) FROM search_history 
                WHERE timestamp > datetime('now', '-1 day')
            ''')
            recent_searches = cursor.fetchone()[0]

            conn.close()

            return {
                'total_users': total_users,
                'active_users': active_users,
                'total_searches': total_searches,
                'banned_users': banned_users,
                'active_channels': active_channels,
                'recent_searches': recent_searches
            }

        except Exception as e:
            logger.error(f"Error getting bot statistics: {e}")
            return {
                'total_users': 0,
                'active_users': 0,
                'total_searches': 0,
                'banned_users': 0,
                'active_channels': 0,
                'recent_searches': 0
            }
