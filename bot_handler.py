"""
Telegram Bot Handler with improved error handling and notifications
Includes automatic notifications for new channel members
"""
import logging
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import requests
from database import Database
from pixabay_api import PixabayAPI

logger = logging.getLogger(__name__)

class TelegramBotHandler:
    def __init__(self):
        self.bot_token = os.environ.get("BOT_TOKEN", "8071576925:AAGgx_Jkuu-mRpjdMKiOQCDkkVQskXQYhQo")
        self.admin_id = int(os.environ.get("ADMIN_ID", "7251748706"))
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        self.db = Database()
        self.pixabay = PixabayAPI()
        
        # User sessions for navigation
        self.user_sessions = {}
        
        logger.info("TelegramBotHandler initialized")

    def send_request(self, method: str, data: Dict[str, Any]) -> Optional[Dict]:
        """Send request to Telegram API with error handling"""
        try:
            url = f"{self.base_url}/{method}"
            response = requests.post(url, json=data, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error sending request to Telegram API: {e}")
            return None

    def send_message(self, chat_id: int, text: str, reply_markup: Optional[Dict] = None) -> bool:
        """Send message to Telegram chat"""
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }
        
        if reply_markup:
            data['reply_markup'] = reply_markup
            
        result = self.send_request('sendMessage', data)
        return result is not None

    def send_photo(self, chat_id: int, photo_url: str, caption: str = "", reply_markup: Optional[Dict] = None) -> bool:
        """Send photo to Telegram chat"""
        data = {
            'chat_id': chat_id,
            'photo': photo_url,
            'caption': caption,
            'parse_mode': 'HTML'
        }
        
        if reply_markup:
            data['reply_markup'] = reply_markup
            
        result = self.send_request('sendPhoto', data)
        return result is not None

    def send_video(self, chat_id: int, video_url: str, caption: str = "", reply_markup: Optional[Dict] = None) -> bool:
        """Send video to Telegram chat"""
        data = {
            'chat_id': chat_id,
            'video': video_url,
            'caption': caption,
            'parse_mode': 'HTML'
        }
        
        if reply_markup:
            data['reply_markup'] = reply_markup
            
        result = self.send_request('sendVideo', data)
        return result is not None

    def send_audio(self, chat_id: int, audio_url: str, caption: str = "", reply_markup: Optional[Dict] = None) -> bool:
        """Send audio to Telegram chat"""
        data = {
            'chat_id': chat_id,
            'audio': audio_url,
            'caption': caption,
            'parse_mode': 'HTML'
        }
        
        if reply_markup:
            data['reply_markup'] = reply_markup
            
        result = self.send_request('sendAudio', data)
        return result is not None

    def check_user_subscription(self, user_id: int) -> bool:
        """Check if user is subscribed to all mandatory channels"""
        channels = self.db.get_mandatory_channels()
        
        for channel in channels:
            try:
                data = {
                    'chat_id': channel['channel_id'],
                    'user_id': user_id
                }
                
                result = self.send_request('getChatMember', data)
                
                if not result or not result.get('ok'):
                    return False
                    
                member_status = result['result']['status']
                if member_status in ['left', 'kicked', 'restricted']:
                    return False
                    
            except Exception as e:
                logger.error(f"Error checking subscription for channel {channel['channel_id']}: {e}")
                return False
                
        return True

    def create_subscription_keyboard(self) -> Dict:
        """Create keyboard for mandatory channel subscription"""
        channels = self.db.get_mandatory_channels()
        keyboard = []
        
        for channel in channels:
            button = {
                'text': f"📢 {channel['channel_username']}",
                'url': f"https://t.me/{channel['channel_username'].replace('@', '')}"
            }
            keyboard.append([button])
        
        keyboard.append([{
            'text': "✅ تحقق من الاشتراك",
            'callback_data': "check_subscription"
        }])
        
        return {'inline_keyboard': keyboard}

    def create_search_keyboard(self) -> Dict:
        """Create keyboard for search options"""
        keyboard = [
            [
                {'text': "🖼️ صور", 'callback_data': "search_images"},
                {'text': "🎥 فيديو", 'callback_data': "search_videos"}
            ],
            [
                {'text': "🎵 موسيقى", 'callback_data': "search_music"},
                {'text': "🎭 GIF", 'callback_data': "search_gifs"}
            ]
        ]
        return {'inline_keyboard': keyboard}

    def create_navigation_keyboard(self, user_id: int, search_type: str) -> Dict:
        """Create navigation keyboard for search results"""
        session = self.user_sessions.get(user_id, {})
        current_index = session.get('current_index', 0)
        total_results = len(session.get('current_results', []))
        
        keyboard = []
        
        # Navigation buttons
        nav_row = []
        if current_index > 0:
            nav_row.append({'text': "⬅️ السابق", 'callback_data': f"nav_prev_{search_type}"})
        
        nav_row.append({'text': f"{current_index + 1}/{total_results}", 'callback_data': "nav_info"})
        
        if current_index < total_results - 1:
            nav_row.append({'text': "➡️ التالي", 'callback_data': f"nav_next_{search_type}"})
        
        keyboard.append(nav_row)
        
        # Search again button
        keyboard.append([{'text': "🔍 بحث جديد", 'callback_data': "new_search"}])
        
        return {'inline_keyboard': keyboard}

    def notify_new_member(self, user_id: int, channel_info: Dict):
        """Send notification to admin about new channel member"""
        try:
            user_info = self.db.get_user(user_id)
            if not user_info:
                return
            
            message = f"""
🎉 <b>عضو جديد انضم للقناة!</b>

👤 <b>معلومات العضو:</b>
• الاسم: {user_info.get('first_name', 'غير محدد')} {user_info.get('last_name', '')}
• اسم المستخدم: @{user_info.get('username', 'غير متوفر')}
• معرف المستخدم: <code>{user_id}</code>

📢 <b>القناة:</b>
• {channel_info.get('channel_username', 'غير محدد')}

📅 <b>تاريخ الانضمام:</b>
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            self.send_message(self.admin_id, message)
            logger.info(f"Notification sent for new member {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending new member notification: {e}")

    def create_admin_keyboard(self) -> Dict:
        """Create admin panel keyboard"""
        keyboard = [
            [
                {'text': "📊 الإحصائيات", 'callback_data': "admin_stats"},
                {'text': "👥 المستخدمون", 'callback_data': "admin_users"}
            ],
            [
                {'text': "📢 القنوات الإجبارية", 'callback_data': "admin_channels"},
                {'text': "🔍 البحثات الأخيرة", 'callback_data': "admin_searches"}
            ],
            [
                {'text': "📣 إذاعة رسالة", 'callback_data': "admin_broadcast"},
                {'text': "⚙️ إعدادات البوت", 'callback_data': "admin_settings"}
            ],
            [
                {'text': "🔄 تحديث الإحصائيات", 'callback_data': "admin_refresh"}
            ]
        ]
        return {'inline_keyboard': keyboard}

    def create_user_management_keyboard(self, page: int = 1) -> Dict:
        """Create user management keyboard with pagination"""
        keyboard = [
            [
                {'text': "🚫 المحظورون", 'callback_data': "admin_banned_users"},
                {'text': "✅ النشطون", 'callback_data': "admin_active_users"}
            ],
            [
                {'text': "⬅️ السابق", 'callback_data': f"admin_users_page_{page-1}"},
                {'text': f"صفحة {page}", 'callback_data': "admin_page_info"},
                {'text': "➡️ التالي", 'callback_data': f"admin_users_page_{page+1}"}
            ],
            [
                {'text': "🔙 العودة للإدارة", 'callback_data': "admin_main"}
            ]
        ]
        return {'inline_keyboard': keyboard}

    def create_channel_management_keyboard(self) -> Dict:
        """Create channel management keyboard"""
        keyboard = [
            [
                {'text': "➕ إضافة قناة", 'callback_data': "admin_add_channel"},
                {'text': "🗑️ حذف قناة", 'callback_data': "admin_remove_channel"}
            ],
            [
                {'text': "📋 قائمة القنوات", 'callback_data': "admin_list_channels"}
            ],
            [
                {'text': "🔙 العودة للإدارة", 'callback_data': "admin_main"}
            ]
        ]
        return {'inline_keyboard': keyboard}

    def handle_admin_command(self, user_id: int, chat_id: int):
        """Handle /admin command - only for admin"""
        try:
            # Check if user is admin
            if user_id != self.admin_id:
                self.send_message(chat_id, "❌ غير مصرح لك بالوصول للوحة الإدارة.")
                return

            stats = self.db.get_bot_statistics()
            admin_message = f"""
🔧 <b>لوحة إدارة البوت</b>

📊 <b>إحصائيات سريعة:</b>
• 👥 إجمالي المستخدمين: {stats['total_users']}
• 🔍 إجمالي البحثات: {stats['total_searches']}
• 📢 القنوات النشطة: {stats['active_channels']}
• 🚫 المحظورون: {stats['banned_users']}

اختر العملية التي تريد تنفيذها:
"""
            keyboard = self.create_admin_keyboard()
            self.send_message(chat_id, admin_message, keyboard)

        except Exception as e:
            logger.error(f"Error handling admin command: {e}")
            self.send_message(chat_id, "❌ حدث خطأ في لوحة الإدارة.")

    def handle_start_command(self, user_id: int, chat_id: int, user_data: Dict):
        """Handle /start command"""
        try:
            # Add user to database
            self.db.add_user(
                user_id=user_id,
                username=user_data.get('username', ''),
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', '')
            )
            
            # Check subscription
            if not self.check_user_subscription(user_id):
                welcome_message = """
🤖 <b>مرحباً بك في بوت البحث في Pixabay!</b>

⚠️ <b>للاستفادة من البوت، يجب الاشتراك في القنوات التالية:</b>

👇 اضغط على أزرار القنوات للاشتراك، ثم اضغط "تحقق من الاشتراك"
"""
                keyboard = self.create_subscription_keyboard()
                self.send_message(chat_id, welcome_message, keyboard)
            else:
                welcome_message = """
🎉 <b>مرحباً بك في بوت البحث في Pixabay!</b>

🔍 <b>يمكنك البحث عن:</b>
• 🖼️ صور عالية الجودة
• 🎥 مقاطع فيديو
• 🎵 ملفات صوتية
• 🎭 صور متحركة GIF

اختر نوع البحث من الأزرار أدناه:
"""
                keyboard = self.create_search_keyboard()
                self.send_message(chat_id, welcome_message, keyboard)
                
        except Exception as e:
            logger.error(f"Error handling start command: {e}")
            self.send_message(chat_id, "❌ حدث خطأ أثناء بدء البوت. حاول مرة أخرى.")

    def handle_callback_query(self, callback_query: Dict):
        """Handle callback queries from inline keyboards"""
        try:
            user_id = callback_query['from']['id']
            chat_id = callback_query['message']['chat']['id']
            data = callback_query['data']
            
            # Check subscription for all callbacks except check_subscription
            if data != "check_subscription" and not self.check_user_subscription(user_id):
                message = "⚠️ يجب الاشتراك في جميع القنوات الإجبارية أولاً!"
                keyboard = self.create_subscription_keyboard()
                self.send_message(chat_id, message, keyboard)
                return
            
            if data == "check_subscription":
                if self.check_user_subscription(user_id):
                    # Check if notification already sent for this user
                    user_info = self.db.get_user(user_id)
                    if not user_info.get('notification_sent', False):
                        # Send notification about new member to admin
                        channels = self.db.get_mandatory_channels()
                        for channel in channels:
                            self.notify_new_member(user_id, channel)
                            # Record notification in database
                            self.db.add_notification(user_id, channel['channel_id'], 'new_member')
                    
                    message = """
✅ <b>رائع! تم التحقق من اشتراكك بنجاح</b>

🔍 <b>يمكنك الآن البحث عن:</b>
• 🖼️ صور عالية الجودة
• 🎥 مقاطع فيديو
• 🎵 ملفات صوتية
• 🎭 صور متحركة GIF

اختر نوع البحث:
"""
                    keyboard = self.create_search_keyboard()
                    self.send_message(chat_id, message, keyboard)
                else:
                    message = "❌ لم تكمل الاشتراك في جميع القنوات بعد. يرجى الاشتراك ثم المحاولة مرة أخرى."
                    keyboard = self.create_subscription_keyboard()
                    self.send_message(chat_id, message, keyboard)
            
            elif data.startswith("search_"):
                search_type = data.replace("search_", "")
                self.user_sessions[user_id] = {
                    'waiting_for_query': True,
                    'search_type': search_type
                }
                
                type_names = {
                    'images': '🖼️ الصور',
                    'videos': '🎥 الفيديو',
                    'music': '🎵 الموسيقى',
                    'gifs': '🎭 الصور المتحركة'
                }
                
                message = f"🔍 <b>البحث في {type_names.get(search_type, search_type)}</b>\n\nأرسل كلمة البحث:"
                self.send_message(chat_id, message)
            
            elif data.startswith("nav_"):
                self.handle_navigation(user_id, chat_id, data)
            
            elif data == "new_search":
                message = "🔍 <b>بحث جديد</b>\n\nاختر نوع البحث:"
                keyboard = self.create_search_keyboard()
                self.send_message(chat_id, message, keyboard)
            
            # Admin panel callbacks
            elif data.startswith("admin_"):
                self.handle_admin_callback(user_id, chat_id, data)
                
        except Exception as e:
            logger.error(f"Error handling callback query: {e}")

    def handle_admin_callback(self, user_id: int, chat_id: int, callback_data: str):
        """Handle admin panel callback queries"""
        try:
            # Check if user is admin
            if user_id != self.admin_id:
                self.send_message(chat_id, "❌ غير مصرح لك بالوصول للوحة الإدارة.")
                return

            if callback_data == "admin_main":
                self.handle_admin_command(user_id, chat_id)
                
            elif callback_data == "admin_stats":
                self.show_detailed_stats(chat_id)
                
            elif callback_data == "admin_users":
                self.show_users_management(chat_id)
                
            elif callback_data == "admin_channels":
                self.show_channels_management(chat_id)
                
            elif callback_data == "admin_searches":
                self.show_recent_searches(chat_id)
                
            elif callback_data == "admin_broadcast":
                self.start_broadcast_mode(user_id, chat_id)
                
            elif callback_data == "admin_settings":
                self.show_bot_settings(chat_id)
                
            elif callback_data == "admin_refresh":
                self.handle_admin_command(user_id, chat_id)
                
            elif callback_data.startswith("admin_ban_"):
                target_user_id = int(callback_data.replace("admin_ban_", ""))
                self.ban_user_admin(chat_id, target_user_id)
                
            elif callback_data.startswith("admin_unban_"):
                target_user_id = int(callback_data.replace("admin_unban_", ""))
                self.unban_user_admin(chat_id, target_user_id)
                
            elif callback_data == "admin_list_channels":
                self.list_mandatory_channels(chat_id)
                
            elif callback_data.startswith("broadcast_confirm_"):
                # Execute the broadcast
                session = self.user_sessions.get(user_id, {})
                broadcast_message = session.get('broadcast_message', '')
                if broadcast_message:
                    self.execute_broadcast(chat_id, broadcast_message)
                else:
                    self.send_message(chat_id, "❌ لا توجد رسالة للإذاعة.")
                    
            elif callback_data.startswith("remove_channel_"):
                channel_id = callback_data.replace("remove_channel_", "")
                self.remove_mandatory_channel(chat_id, channel_id)
                
        except Exception as e:
            logger.error(f"Error handling admin callback: {e}")
            self.send_message(chat_id, "❌ حدث خطأ في العملية الإدارية.")

    def remove_mandatory_channel(self, chat_id: int, channel_id: str):
        """Remove mandatory channel"""
        try:
            # Get channel info before removing
            channels = self.db.get_mandatory_channels()
            channel_info = None
            for ch in channels:
                if str(ch['channel_id']) == str(channel_id):
                    channel_info = ch
                    break
            
            if channel_info:
                self.db.remove_mandatory_channel(channel_id)
                message = f"✅ تم حذف القناة <b>{channel_info['channel_username']}</b> من القائمة الإجبارية بنجاح."
            else:
                message = "❌ لم يتم العثور على القناة."
                
            keyboard = {'inline_keyboard': [[{'text': "🔙 العودة لقائمة القنوات", 'callback_data': "admin_list_channels"}]]}
            self.send_message(chat_id, message, keyboard)
            
        except Exception as e:
            logger.error(f"Error removing mandatory channel: {e}")
            self.send_message(chat_id, "❌ حدث خطأ في حذف القناة.")

    def show_detailed_stats(self, chat_id: int):
        """Show detailed bot statistics"""
        try:
            stats = self.db.get_bot_statistics()
            recent_searches = self.db.get_recent_searches(limit=5)
            
            stats_message = f"""
📊 <b>إحصائيات البوت التفصيلية</b>

👥 <b>المستخدمون:</b>
• إجمالي المستخدمين: {stats['total_users']}
• المستخدمون النشطون: {stats['active_users']}
• المحظورون: {stats['banned_users']}

🔍 <b>البحثات:</b>
• إجمالي البحثات: {stats['total_searches']}
• البحثات الأخيرة (24 ساعة): {stats['recent_searches']}

📢 <b>القنوات:</b>
• القنوات النشطة: {stats['active_channels']}

🕐 <b>آخر 5 بحثات:</b>
"""
            
            for search in recent_searches[:5]:
                search_type_emoji = {
                    'images': '🖼️',
                    'videos': '🎥', 
                    'music': '🎵',
                    'gifs': '🎭'
                }.get(search['search_type'], '🔍')
                
                stats_message += f"• {search_type_emoji} {search['query']} - {search['user_name']}\n"
            
            keyboard = {'inline_keyboard': [[{'text': "🔙 العودة للإدارة", 'callback_data': "admin_main"}]]}
            self.send_message(chat_id, stats_message, keyboard)
            
        except Exception as e:
            logger.error(f"Error showing detailed stats: {e}")
            self.send_message(chat_id, "❌ حدث خطأ في عرض الإحصائيات.")

    def show_users_management(self, chat_id: int):
        """Show users management panel"""
        try:
            users = self.db.get_all_users()
            active_users = [u for u in users if not u['is_banned']]
            banned_users = [u for u in users if u['is_banned']]
            
            message = f"""
👥 <b>إدارة المستخدمين</b>

📊 <b>الإحصائيات:</b>
• إجمالي المستخدمين: {len(users)}
• المستخدمون النشطون: {len(active_users)}
• المحظورون: {len(banned_users)}

<b>آخر 10 مستخدمين:</b>
"""
            
            for user in users[:10]:
                status = "🚫 محظور" if user['is_banned'] else "✅ نشط"
                username = f"@{user['username']}" if user['username'] else "لا يوجد"
                message += f"• {user['first_name']} ({username}) - {status}\n"
                message += f"  البحثات: {user['search_count']} | ID: <code>{user['user_id']}</code>\n\n"
            
            keyboard = self.create_user_management_keyboard()
            self.send_message(chat_id, message[:4096], keyboard)  # Telegram message limit
            
        except Exception as e:
            logger.error(f"Error showing users management: {e}")
            self.send_message(chat_id, "❌ حدث خطأ في عرض المستخدمين.")

    def show_channels_management(self, chat_id: int):
        """Show channels management panel"""
        try:
            channels = self.db.get_mandatory_channels()
            
            message = f"""
📢 <b>إدارة القنوات الإجبارية</b>

📊 <b>عدد القنوات النشطة:</b> {len(channels)}

<b>قائمة القنوات:</b>
"""
            
            if channels:
                for i, channel in enumerate(channels, 1):
                    message += f"{i}. {channel['channel_username']}\n"
                    message += f"   ID: <code>{channel['channel_id']}</code>\n"
                    message += f"   تاريخ الإضافة: {channel['added_date'][:10]}\n\n"
            else:
                message += "لا توجد قنوات إجبارية مضافة حالياً.\n"
            
            keyboard = self.create_channel_management_keyboard()
            self.send_message(chat_id, message, keyboard)
            
        except Exception as e:
            logger.error(f"Error showing channels management: {e}")
            self.send_message(chat_id, "❌ حدث خطأ في عرض القنوات.")

    def show_recent_searches(self, chat_id: int):
        """Show recent searches"""
        try:
            searches = self.db.get_recent_searches(limit=20)
            
            message = """
🔍 <b>البحثات الأخيرة (آخر 20)</b>

"""
            
            if searches:
                for search in searches:
                    search_type_emoji = {
                        'images': '🖼️',
                        'videos': '🎥',
                        'music': '🎵', 
                        'gifs': '🎭'
                    }.get(search['search_type'], '🔍')
                    
                    username = f"@{search['username']}" if search['username'] else search['user_name']
                    message += f"{search_type_emoji} <b>{search['query']}</b>\n"
                    message += f"   👤 {username} | 📊 {search['results_count']} نتيجة\n"
                    message += f"   🕐 {search['timestamp'][:16]}\n\n"
            else:
                message += "لا توجد بحثات مسجلة حالياً.\n"
            
            keyboard = {'inline_keyboard': [[{'text': "🔙 العودة للإدارة", 'callback_data': "admin_main"}]]}
            self.send_message(chat_id, message[:4096], keyboard)
            
        except Exception as e:
            logger.error(f"Error showing recent searches: {e}")
            self.send_message(chat_id, "❌ حدث خطأ في عرض البحثات.")

    def start_broadcast_mode(self, user_id: int, chat_id: int):
        """Start broadcast message mode"""
        try:
            self.user_sessions[user_id] = {
                'mode': 'broadcast',
                'waiting_for_message': True
            }
            
            message = """
📣 <b>إذاعة رسالة</b>

أرسل الرسالة التي تريد إذاعتها لجميع مستخدمي البوت.

⚠️ <b>تنبيه:</b> ستصل الرسالة لجميع المستخدمين المسجلين في البوت.
"""
            
            keyboard = {'inline_keyboard': [[{'text': "❌ إلغاء", 'callback_data': "admin_main"}]]}
            self.send_message(chat_id, message, keyboard)
            
        except Exception as e:
            logger.error(f"Error starting broadcast mode: {e}")
            self.send_message(chat_id, "❌ حدث خطأ في بدء الإذاعة.")

    def show_bot_settings(self, chat_id: int):
        """Show bot settings panel"""
        try:
            # Test API connections
            pixabay_status = "✅ متصل" if self.pixabay.test_api_connection() else "❌ غير متصل"
            bot_status = "✅ متصل" if self.check_bot_status() == "online" else "❌ غير متصل"
            
            message = f"""
⚙️ <b>إعدادات البوت</b>

🔌 <b>حالة الاتصالات:</b>
• Bot API: {bot_status}
• Pixabay API: {pixabay_status}

🎛️ <b>الإعدادات الحالية:</b>
• معرف الإدارة: <code>{self.admin_id}</code>
• عدد النتائج لكل بحث: 20
• اللغة: العربية + الإنجليزية

📊 <b>معلومات النظام:</b>
• إصدار البوت: 2.0
• قاعدة البيانات: SQLite
• المنصة: Render.com
"""
            
            keyboard = {'inline_keyboard': [[{'text': "🔙 العودة للإدارة", 'callback_data': "admin_main"}]]}
            self.send_message(chat_id, message, keyboard)
            
        except Exception as e:
            logger.error(f"Error showing bot settings: {e}")
            self.send_message(chat_id, "❌ حدث خطأ في عرض الإعدادات.")

    def ban_user_admin(self, chat_id: int, target_user_id: int):
        """Ban user via admin panel"""
        try:
            self.db.ban_user(target_user_id)
            self.send_message(chat_id, f"✅ تم حظر المستخدم {target_user_id} بنجاح.")
            
        except Exception as e:
            logger.error(f"Error banning user: {e}")
            self.send_message(chat_id, "❌ حدث خطأ في حظر المستخدم.")

    def unban_user_admin(self, chat_id: int, target_user_id: int):
        """Unban user via admin panel"""
        try:
            self.db.unban_user(target_user_id)
            self.send_message(chat_id, f"✅ تم إلغاء حظر المستخدم {target_user_id} بنجاح.")
            
        except Exception as e:
            logger.error(f"Error unbanning user: {e}")
            self.send_message(chat_id, "❌ حدث خطأ في إلغاء حظر المستخدم.")

    def handle_broadcast_message(self, user_id: int, chat_id: int, message_text: str):
        """Handle broadcast message from admin"""
        try:
            # Reset user session
            self.user_sessions[user_id] = {}
            
            # Confirm broadcast
            confirm_message = f"""
📣 <b>تأكيد الإذاعة</b>

الرسالة التي ستُرسل:
━━━━━━━━━━━━━━━━━━━━
{message_text}
━━━━━━━━━━━━━━━━━━━━

هل تريد إرسال هذه الرسالة لجميع المستخدمين؟
"""
            
            keyboard = {
                'inline_keyboard': [
                    [
                        {'text': "✅ نعم، أرسل", 'callback_data': f"broadcast_confirm_{hash(message_text) % 10000}"},
                        {'text': "❌ إلغاء", 'callback_data': "admin_main"}
                    ]
                ]
            }
            
            # Store broadcast message temporarily
            self.user_sessions[user_id] = {'broadcast_message': message_text}
            
            self.send_message(chat_id, confirm_message, keyboard)
            
        except Exception as e:
            logger.error(f"Error handling broadcast message: {e}")
            self.send_message(chat_id, "❌ حدث خطأ في معالجة رسالة الإذاعة.")

    def execute_broadcast(self, chat_id: int, message_text: str):
        """Execute broadcast message to all users"""
        try:
            broadcast_result = self.broadcast_message(message_text)
            
            result_message = f"""
📣 <b>نتيجة الإذاعة</b>

✅ تم الإرسال لـ: {broadcast_result['sent']} مستخدم
❌ فشل الإرسال لـ: {broadcast_result['failed']} مستخدم

الرسالة المُرسلة:
━━━━━━━━━━━━━━━━━━━━
{message_text}
━━━━━━━━━━━━━━━━━━━━
"""
            
            keyboard = {'inline_keyboard': [[{'text': "🔙 العودة للإدارة", 'callback_data': "admin_main"}]]}
            self.send_message(chat_id, result_message, keyboard)
            
        except Exception as e:
            logger.error(f"Error executing broadcast: {e}")
            self.send_message(chat_id, "❌ حدث خطأ في تنفيذ الإذاعة.")

    def list_mandatory_channels(self, chat_id: int):
        """List all mandatory channels with management options"""
        try:
            channels = self.db.get_mandatory_channels()
            
            message = f"""
📢 <b>قائمة القنوات الإجبارية</b>

📊 <b>العدد الإجمالي:</b> {len(channels)}

"""
            
            keyboard_buttons = []
            
            if channels:
                for i, channel in enumerate(channels, 1):
                    message += f"{i}. <b>{channel['channel_username']}</b>\n"
                    message += f"   • ID: <code>{channel['channel_id']}</code>\n"
                    message += f"   • تاريخ الإضافة: {channel['added_date'][:10]}\n\n"
                    
                    # Add remove button for each channel
                    keyboard_buttons.append([{
                        'text': f"🗑️ حذف {channel['channel_username'][:15]}...",
                        'callback_data': f"remove_channel_{channel['channel_id']}"
                    }])
            else:
                message += "❌ لا توجد قنوات إجبارية مضافة حالياً.\n"
            
            # Add management buttons
            keyboard_buttons.extend([
                [{'text': "➕ إضافة قناة جديدة", 'callback_data': "admin_add_channel"}],
                [{'text': "🔙 العودة لإدارة القنوات", 'callback_data': "admin_channels"}]
            ])
            
            keyboard = {'inline_keyboard': keyboard_buttons}
            self.send_message(chat_id, message[:4096], keyboard)
            
        except Exception as e:
            logger.error(f"Error listing mandatory channels: {e}")
            self.send_message(chat_id, "❌ حدث خطأ في عرض قائمة القنوات.")

    def handle_navigation(self, user_id: int, chat_id: int, nav_data: str):
        """Handle navigation through search results"""
        try:
            session = self.user_sessions.get(user_id, {})
            if not session.get('current_results'):
                self.send_message(chat_id, "❌ لا توجد نتائج بحث نشطة.")
                return
            
            current_index = session.get('current_index', 0)
            results = session['current_results']
            search_type = session.get('search_type', 'images')
            
            if "prev" in nav_data and current_index > 0:
                current_index -= 1
            elif "next" in nav_data and current_index < len(results) - 1:
                current_index += 1
            else:
                return
            
            # Update session
            self.user_sessions[user_id]['current_index'] = current_index
            
            # Send the new result
            result = results[current_index]
            self.send_search_result(chat_id, user_id, result, search_type)
            
        except Exception as e:
            logger.error(f"Error handling navigation: {e}")

    def handle_search_query(self, user_id: int, chat_id: int, query: str):
        """Handle search query from user"""
        try:
            session = self.user_sessions.get(user_id, {})
            if not session.get('waiting_for_query'):
                return
            
            search_type = session.get('search_type', 'images')
            
            # Clear waiting state
            self.user_sessions[user_id]['waiting_for_query'] = False
            
            # Show searching message
            self.send_message(chat_id, f"🔍 جاري البحث عن: <b>{query}</b>...")
            
            # Perform search
            results = self.pixabay.search(query, search_type)
            
            if not results:
                self.send_message(chat_id, "❌ لم يتم العثور على نتائج. جرب كلمات بحث أخرى.")
                return
            
            # Store results in session
            self.user_sessions[user_id] = {
                'current_query': query,
                'search_type': search_type,
                'current_results': results,
                'current_index': 0
            }
            
            # Save search to database
            self.db.add_search_history(user_id, query, search_type, len(results))
            
            # Send first result
            self.send_search_result(chat_id, user_id, results[0], search_type)
            
        except Exception as e:
            logger.error(f"Error handling search query: {e}")
            self.send_message(chat_id, "❌ حدث خطأ أثناء البحث. حاول مرة أخرى.")

    def send_search_result(self, chat_id: int, user_id: int, result: Dict, search_type: str):
        """Send a single search result to user"""
        try:
            keyboard = self.create_navigation_keyboard(user_id, search_type)
            
            if search_type == 'images':
                caption = f"🖼️ <b>{result.get('tags', 'صورة')}</b>\n📊 المشاهدات: {result.get('views', 0):,}"
                self.send_photo(chat_id, result['webformatURL'], caption, keyboard)
                
            elif search_type == 'videos':
                caption = f"🎥 <b>{result.get('tags', 'فيديو')}</b>\n📊 المشاهدات: {result.get('views', 0):,}"
                # Send video thumbnail with download link
                download_url = result['videos']['medium']['url']
                caption += f"\n🔗 <a href='{download_url}'>تحميل الفيديو</a>"
                self.send_photo(chat_id, result['webformatURL'], caption, keyboard)
                
            elif search_type == 'music':
                caption = f"🎵 <b>{result.get('tags', 'موسيقى')}</b>\n⏱️ المدة: {result.get('duration', 0)} ثانية"
                audio_url = result['videos']['medium']['url']  # Using video URL for audio
                self.send_audio(chat_id, audio_url, caption, keyboard)
                
            elif search_type == 'gifs':
                caption = f"🎭 <b>{result.get('tags', 'صورة متحركة')}</b>\n📊 المشاهدات: {result.get('views', 0):,}"
                # Send as video for GIF
                gif_url = result['videos']['small']['url'] if 'videos' in result else result['webformatURL']
                self.send_video(chat_id, gif_url, caption, keyboard)
                
        except Exception as e:
            logger.error(f"Error sending search result: {e}")
            self.send_message(chat_id, "❌ حدث خطأ أثناء إرسال النتيجة.")

    def handle_message(self, message: Dict):
        """Handle incoming messages"""
        try:
            user_id = message['from']['id']
            chat_id = message['chat']['id']
            
            # Check if user is banned
            if self.db.is_user_banned(user_id):
                self.send_message(chat_id, "❌ تم حظرك من استخدام البوت.")
                return
            
            # Handle commands
            if 'text' in message:
                text = message['text']
                
                if text.startswith('/start'):
                    self.handle_start_command(user_id, chat_id, message['from'])
                elif text.startswith('/help'):
                    help_message = """
🤖 <b>مساعدة بوت البحث في Pixabay</b>

📋 <b>الأوامر المتاحة:</b>
• /start - بدء استخدام البوت
• /help - عرض هذه المساعدة

🔍 <b>أنواع البحث:</b>
• 🖼️ صور عالية الجودة
• 🎥 مقاطع فيديو
• 🎵 ملفات صوتية
• 🎭 صور متحركة GIF

💡 <b>نصائح:</b>
• استخدم كلمات إنجليزية للحصول على نتائج أفضل
• جرب كلمات مختلفة إذا لم تجد ما تبحث عنه
• استخدم أزرار التنقل لتصفح النتائج
"""
                    self.send_message(chat_id, help_message)
                elif text.startswith('/admin'):
                    self.handle_admin_command(user_id, chat_id)
                else:
                    # Check if user is waiting for search query or broadcast message
                    session = self.user_sessions.get(user_id, {})
                    if session.get('waiting_for_query'):
                        self.handle_search_query(user_id, chat_id, text)
                    elif session.get('mode') == 'broadcast' and session.get('waiting_for_message'):
                        self.handle_broadcast_message(user_id, chat_id, text)
                    else:
                        self.send_message(chat_id, "استخدم /start لبدء استخدام البوت أو اختر من الأزرار المتاحة.")
                        
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    def process_update(self, update: Dict) -> bool:
        """Process incoming Telegram update"""
        try:
            if 'message' in update:
                self.handle_message(update['message'])
            elif 'callback_query' in update:
                self.handle_callback_query(update['callback_query'])
            else:
                logger.warning(f"Unknown update type: {update}")
                
            return True
            
        except Exception as e:
            logger.error(f"Error processing update: {e}")
            return False

    def set_webhook(self, webhook_url: str) -> bool:
        """Set webhook for the bot"""
        try:
            data = {'url': webhook_url}
            result = self.send_request('setWebhook', data)
            
            if result and result.get('ok'):
                logger.info(f"Webhook set successfully: {webhook_url}")
                return True
            else:
                logger.error(f"Failed to set webhook: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error setting webhook: {e}")
            return False

    def check_bot_status(self) -> str:
        """Check bot status"""
        try:
            result = self.send_request('getMe', {})
            if result and result.get('ok'):
                return "online"
            else:
                return "offline"
        except Exception as e:
            logger.error(f"Error checking bot status: {e}")
            return "error"

    def broadcast_message(self, message: str) -> Dict:
        """Broadcast message to all users"""
        try:
            users = self.db.get_all_users()
            sent = 0
            failed = 0
            
            for user in users:
                if not user.get('is_banned', False):
                    if self.send_message(user['user_id'], message):
                        sent += 1
                    else:
                        failed += 1
                        
            return {'sent': sent, 'failed': failed}
            
        except Exception as e:
            logger.error(f"Error broadcasting message: {e}")
            return {'sent': 0, 'failed': 0}
