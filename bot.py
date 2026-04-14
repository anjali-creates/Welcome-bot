import logging
import asyncio
import os
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler
from telegram.constants import ChatMemberStatus
from telegram.error import TelegramError

# ==================== CONFIG ====================
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN not found!")

ADMIN_ID = int(ADMIN_ID) if ADMIN_ID else None

# ==================== MAXIMUM EMOJIS ====================
WELCOME_EMOJIS = ["🎉", "🎊", "✨", "🌟", "⭐", "💫", "⚡", "🔥", "💥", "🎈", "🎀", "🎁", "🎂", "🍾", "🥳", "🤩", "😍", "🥰", "💖", "💝", "💕", "💞", "💓", "💗", "💙", "💚", "💛", "🧡", "❤️", "💜"]
USER_EMOJIS = ["👤", "🧑", "🙋", "🙌", "👋", "🤝", "💁", "🙆", "🙎", "💃"]
TIME_EMOJIS = ["⏰", "🕐", "🕒", "🕔", "🕖", "🕘", "🕚", "⌚", "📅", "📆"]
ACTION_EMOJIS = ["✅", "❌", "⚠️", "🔔", "🔕", "📢", "🔊", "🔈", "📣", "🎤"]
HEART_EMOJIS = ["💝", "💖", "💗", "💓", "💕", "💞", "💟", "❣️", "💔", "❤️"]
STAR_EMOJIS = ["⭐", "🌟", "✨", "💫", "⚡", "🔥", "💥", "🎯", "🏆", "🎖️"]

# ==================== ANIMATION GIFS ====================
ANIMATION_GIFS = [
    "https://media4.giphy.com/media/3o7abB06u9bNzA8LC8/giphy.gif",
    "https://media2.giphy.com/media/l0MYEqEzwMWFCg8rO/giphy.gif",
    "https://media1.giphy.com/media/26n6WywJyh39n1pBu/giphy.gif",
    "https://media3.giphy.com/media/3o6ZtaO9BZHcOjmErm/giphy.gif",
    "https://media0.giphy.com/media/xUPGcguWZHRC2HyBRS/giphy.gif",
]

# ==================== LOGGING ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== STATS ====================
class BotStats:
    def __init__(self):
        self.total_welcomes = 0
        self.groups = set()
        self.start_time = datetime.now()
    
    def add_welcome(self, group_id):
        self.total_welcomes += 1
        self.groups.add(group_id)
    
    def get_uptime(self):
        uptime = datetime.now() - self.start_time
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60
        seconds = uptime.seconds % 60
        return f"{hours}h {minutes}m {seconds}s"

stats = BotStats()

# ==================== HELPER FUNCTIONS ====================
def random_emoji(emoji_list):
    return random.choice(emoji_list)

async def is_admin(update: Update, user_id: int) -> bool:
    """Check if user is admin in the group"""
    try:
        chat_member = await update.effective_chat.get_member(user_id)
        return chat_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        return False

async def send_to_admin(context, message):
    """Send notification to admin"""
    if ADMIN_ID:
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=message, parse_mode='HTML')
        except:
            pass

async def get_user_profile_photo(user_id, context):
    """Get user's profile photo"""
    try:
        photos = await context.bot.get_user_profile_photos(user_id, limit=1)
        if photos.photos:
            return photos.photos[0][-1].file_id
    except:
        pass
    return None

def get_random_welcome_title():
    titles = [
        "🎉✨ 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐓𝐎 𝐓𝐇𝐄 𝐅𝐀𝐌𝐈𝐋𝐘! ✨🎉",
        "🌟⭐ 𝐍𝐄𝐖 𝐌𝐄𝐌𝐁𝐄𝐑 𝐀𝐑𝐑𝐈𝐕𝐄𝐃! ⭐🌟",
        "💫🔥 𝐀𝐍𝐎𝐓𝐇𝐄𝐑 𝐋𝐄𝐆𝐄𝐍𝐃 𝐉𝐎𝐈𝐍𝐄𝐃! 🔥💫",
        "🎊🥳 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐓𝐎 𝐓𝐇𝐄 𝐂𝐎𝐌𝐌𝐔𝐍𝐈𝐓𝐘! 🥳🎊",
        "💖💝 𝐍𝐄𝐖 𝐅𝐀𝐌𝐈𝐋𝐘 𝐌𝐄𝐌𝐁𝐄𝐑! 💝💖",
    ]
    return random.choice(titles)

# ==================== /all COMMAND - TAG EVERYONE ====================
async def all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tag all members in the group (Admin only)"""
    
    # Check if command is used in a group
    if update.effective_chat.type == "private":
        await update.message.reply_text("❌ This command only works in groups!")
        return
    
    # Check if user is admin
    user_id = update.effective_user.id
    if not await is_admin(update, user_id):
        await update.message.reply_text("""
╔══════════════════════════════════════╗
║  ❌ 𝐀𝐂𝐂𝐄𝐒𝐒 𝐃𝐄𝐍𝐈𝐄𝐃! ❌              ║
╚══════════════════════════════════════╝

🔒 <b>𝐓𝐡𝐢𝐬 𝐜𝐨𝐦𝐦𝐚𝐧𝐝 𝐢𝐬 𝐨𝐧𝐥𝐲 𝐟𝐨𝐫 𝐚𝐝𝐦𝐢𝐧𝐬!</b>

👑 <b>𝐎𝐧𝐥𝐲 𝐠𝐫𝐨𝐮𝐩 𝐚𝐝𝐦𝐢𝐧𝐬 𝐜𝐚𝐧 𝐮𝐬𝐞 /all</b>

💡 <b>𝐂𝐨𝐧𝐭𝐚𝐜𝐭 𝐠𝐫𝐨𝐮𝐩 𝐚𝐝𝐦𝐢𝐧 𝐭𝐨 𝐬𝐞𝐧𝐝 𝐚𝐧𝐧𝐨𝐮𝐧𝐜𝐞𝐦𝐞𝐧𝐭𝐬</b>
""", parse_mode='HTML')
        return
    
    # Get the message to send
    if not context.args:
        await update.message.reply_text("""
╔══════════════════════════════════════╗
║  📝 𝐇𝐎𝐖 𝐓𝐎 𝐔𝐒𝐄 /𝐀𝐋𝐋 𝐂𝐎𝐌𝐌𝐀𝐍𝐃          ║
╚══════════════════════════════════════╝

✨ <b>𝐔𝐬𝐚𝐠𝐞:</b>
<code>/all Your message here</code>

📌 <b>𝐄𝐱𝐚𝐦𝐩𝐥𝐞:</b>
<code>/all Hello everyone! Welcome to the group!</code>

⚠️ <b>𝐍𝐨𝐭𝐞:</b>
• Only admins can use this command
• Everyone in the group will be tagged
• Use responsibly!
""", parse_mode='HTML')
        return
    
    message_text = ' '.join(context.args)
    chat_id = update.effective_chat.id
    admin_name = update.effective_user.full_name
    
    # Send typing indicator
    await update.message.chat.send_action(action="typing")
    
    # Initial message
    processing_msg = await update.message.reply_text("""
⏳ <b>𝐏𝐑𝐎𝐂𝐄𝐒𝐒𝐈𝐍𝐆...</b>

📢 Fetching members and sending announcements...
✨ Please wait, this may take a few seconds...
""", parse_mode='HTML')
    
    try:
        # Get all members
        members = []
        async for member in context.bot.get_chat_members(chat_id):
            if not member.user.is_bot:
                members.append(member.user)
        
        if not members:
            await processing_msg.edit_text("❌ No members found in this group!")
            return
        
        # Create tag message
        tags = []
        for member in members[:50]:  # Limit to 50 members per message (Telegram limit)
            tags.append(f"<a href='tg://user?id={member.id}'> </a>")
        
        # Build announcement
        announcement = f"""
╔══════════════════════════════════════════════════════════════╗
║              📢 𝐆𝐑𝐎𝐔𝐏 𝐀𝐍𝐍𝐎𝐔𝐍𝐂𝐄𝐌𝐄𝐍𝐓 📢                    ║
╚══════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────┐
│  👑 <b>𝐀𝐝𝐦𝐢𝐧:</b> {admin_name}                                 │
│  🕐 <b>𝐓𝐢𝐦𝐞:</b> {datetime.now().strftime('%I:%M:%S %p')}       │
│  📅 <b>𝐃𝐚𝐭𝐞:</b> {datetime.now().strftime('%B %d, %Y')}         │
│  👥 <b>𝐓𝐨𝐭𝐚𝐥 𝐌𝐞𝐦𝐛𝐞𝐫𝐬:</b> {len(members)}                         │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  💬 <b>𝐌𝐄𝐒𝐒𝐀𝐆𝐄:</b>                                            │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  {message_text}                                              │
│                                                               │
└──────────────────────────────────────────────────────────────┘

{''.join(tags)}

✨ <b>𝐏𝐥𝐞𝐚𝐬𝐞 𝐫𝐞𝐚𝐝 𝐭𝐡𝐞 𝐚𝐛𝐨𝐯𝐞 𝐚𝐧𝐧𝐨𝐮𝐧𝐜𝐞𝐦𝐞𝐧𝐭 𝐜𝐚𝐫𝐞𝐟𝐮𝐥𝐥𝐲!</b> ✨

╔══════════════════════════════════════════════════════════════╗
║         💫 𝐓𝐇𝐀𝐍𝐊 𝐘𝐎𝐔 𝐅𝐎𝐑 𝐘𝐎𝐔𝐑 𝐀𝐓𝐓𝐄𝐍𝐓𝐈𝐎𝐍! 💫            ║
╚══════════════════════════════════════════════════════════════╝
"""
        
        # Send the announcement
        await context.bot.send_message(
            chat_id=chat_id,
            text=announcement,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        
        # Delete processing message
        await processing_msg.delete()
        
        # Send success message to admin
        await update.message.reply_text(f"""
✅ <b>𝐀𝐍𝐍𝐎𝐔𝐍𝐂𝐄𝐌𝐄𝐍𝐓 𝐒𝐄𝐍𝐓 𝐒𝐔𝐂𝐂𝐄𝐒𝐒𝐅𝐔𝐋𝐋𝐘!</b> ✅

📊 <b>𝐒𝐭𝐚𝐭𝐢𝐬𝐭𝐢𝐜𝐬:</b>
• 👥 Members notified: {len(members)}
• 🕐 Time: {datetime.now().strftime('%I:%M:%S %p')}
• 💬 Message: {message_text[:50]}...

✨ <b>Everyone has been tagged!</b>
""", parse_mode='HTML')
        
        # Notify admin
        await send_to_admin(context, f"""
📢 <b>/all COMMAND USED</b>

👑 <b>Admin:</b> {admin_name}
🏠 <b>Group:</b> {update.effective_chat.title}
👥 <b>Members:</b> {len(members)}
💬 <b>Message:</b> {message_text[:100]}
🕐 <b>Time:</b> {datetime.now().strftime('%I:%M:%S %p')}
""")
        
    except TelegramError as e:
        await processing_msg.edit_text(f"""
❌ <b>𝐄𝐑𝐑𝐎𝐑 𝐒𝐄𝐍𝐃𝐈𝐍𝐆 𝐀𝐍𝐍𝐎𝐔𝐍𝐂𝐄𝐌𝐄𝐍𝐓</b> ❌

⚠️ <b>Error:</b> {str(e)[:100]}

💡 <b>Possible reasons:</b>
• Bot is not admin
• Too many requests
• Group privacy settings
""", parse_mode='HTML')

# ==================== WELCOME FUNCTION ====================
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome new members with professional design"""
    
    if not update.message.new_chat_members:
        return
    
    chat = update.effective_chat
    stats.add_welcome(chat.id)
    
    # Check if bot is admin
    try:
        bot_member = await chat.get_member(context.bot.id)
        is_admin = bot_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        is_admin = False
    
    for new_member in update.message.new_chat_members:
        if new_member.id == context.bot.id:
            continue
        
        # User information
        user_name = new_member.full_name
        user_first = new_member.first_name or "Guest"
        user_mention = f"<a href='tg://user?id={new_member.id}'>{user_name}</a>"
        username = f"@{new_member.username}" if new_member.username else f"{random_emoji(['🚫', '❌'])} No username"
        user_id = new_member.id
        
        # Get profile photo
        profile_photo = await get_user_profile_photo(user_id, context)
        
        # Time stamp
        current_time = datetime.now().strftime("%I:%M:%S %p")
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        
        # Build professional welcome message
        welcome_title = get_random_welcome_title()
        
        welcome_message = f"""
{random_emoji(WELCOME_EMOJIS) * 8}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji(WELCOME_EMOJIS) * 8}

                      {welcome_title}

{random_emoji(WELCOME_EMOJIS) * 8}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji(WELCOME_EMOJIS) * 8}

┌────────────────────────────────────────────────────────────────┐
│                    📋 𝐌𝐄𝐌𝐁𝐄𝐑 𝐈𝐍𝐅𝐎𝐑𝐌𝐀𝐓𝐈𝐎𝐍                      │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│        {random_emoji(USER_EMOJIS)}  𝐅𝐔𝐋𝐋 𝐍𝐀𝐌𝐄      : {user_mention}                         │
│        🏷️  𝐔𝐒𝐄𝐑𝐍𝐀𝐌𝐄      : {username}                           │
│        🆔  𝐔𝐒𝐄𝐑 𝐈𝐃        : <code>{user_id}</code>                              │
│        {random_emoji(USER_EMOJIS)}  𝐆𝐑𝐎𝐔𝐏 𝐍𝐀𝐌𝐄     : {chat.title}                           │
│        {random_emoji(TIME_EMOJIS)}  𝐉𝐎𝐈𝐍 𝐓𝐈𝐌𝐄      : {current_time}                         │
│        📅  𝐉𝐎𝐈𝐍 𝐃𝐀𝐓𝐄      : {current_date}                         │
│        📊  𝐓𝐎𝐓𝐀𝐋 𝐖𝐄𝐋𝐂𝐎𝐌𝐄𝐒  : {stats.total_welcomes}                         │
│                                                                │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                    💝 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐍𝐎𝐓𝐄 💝                           │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  🎉 <b>𝐃𝐞𝐚𝐫 {user_first},</b> 🎉                                 │
│                                                                │
│  ✨ <b>𝐀 𝐯𝐞𝐫𝐲 𝐰𝐚𝐫𝐦 𝐰𝐞𝐥𝐜𝐨𝐦𝐞 𝐭𝐨 𝐨𝐮𝐫 𝐚𝐦𝐚𝐳𝐢𝐧𝐠 𝐜𝐨𝐦𝐦𝐮𝐧𝐢𝐭𝐲!</b> ✨    │
│                                                                │
│  🌟 <b>𝐖𝐞'𝐫𝐞 𝐬𝐨 𝐞𝐱𝐜𝐢𝐭𝐞𝐝 𝐭𝐨 𝐡𝐚𝐯𝐞 𝐲𝐨𝐮 𝐡𝐞𝐫𝐞!</b> 🌟                │
│                                                                │
│  💫 <b>𝐅𝐞𝐞𝐥 𝐟𝐫𝐞𝐞 𝐭𝐨 𝐢𝐧𝐭𝐫𝐨𝐝𝐮𝐜𝐞 𝐲𝐨𝐮𝐫𝐬𝐞𝐥𝐟 𝐚𝐧𝐝 𝐦𝐚𝐤𝐞 𝐟𝐫𝐢𝐞𝐧𝐝𝐬!</b> 💫  │
│                                                                │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                    📌 𝐐𝐔𝐈𝐂𝐊 𝐆𝐔𝐈𝐃𝐄𝐋𝐈𝐍𝐄𝐒                        │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│        ✅  <b>𝐁𝐞 𝐑𝐞𝐬𝐩𝐞𝐜𝐭𝐟𝐮𝐥</b>    - Treat everyone with kindness    │
│        ✅  <b>𝐍𝐨 𝐒𝐩𝐚𝐦𝐦𝐢𝐧𝐠</b>     - No promotional messages        │
│        ✅  <b>𝐇𝐞𝐥𝐩 𝐎𝐭𝐡𝐞𝐫𝐬</b>     - Share and support each other   │
│        ✅  <b>𝐒𝐭𝐚𝐲 𝐀𝐜𝐭𝐢𝐯𝐞</b>     - Regular participation         │
│                                                                │
└────────────────────────────────────────────────────────────────┘

{random_emoji(WELCOME_EMOJIS) * 8}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji(WELCOME_EMOJIS) * 8}

                    {random_emoji(STAR_EMOJIS)} <b>𝐄𝐍𝐉𝐎𝐘 𝐘𝐎𝐔𝐑 𝐒𝐓𝐀𝐘!</b> {random_emoji(STAR_EMOJIS)} 

{random_emoji(WELCOME_EMOJIS) * 8}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji(WELCOME_EMOJIS) * 8}
        """
        
        # Buttons
        keyboard = [
            [
                InlineKeyboardButton("📜 𝐑𝐔𝐋𝐄𝐒", url="https://t.me/telegram"),
                InlineKeyboardButton("💬 𝐈𝐍𝐓𝐑𝐎", url=f"tg://user?id={user_id}")
            ],
            [
                InlineKeyboardButton("🆘 𝐒𝐔𝐏𝐏𝐎𝐑𝐓", url="https://t.me/telegram"),
                InlineKeyboardButton("📢 𝐔𝐏𝐃𝐀𝐓𝐄𝐒", url="https://t.me/telegram")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send animation
        try:
            random_gif = random.choice(ANIMATION_GIFS)
            await update.message.reply_animation(
                animation=random_gif,
                caption=f"🎉 <b>𝐍𝐄𝐖 𝐌𝐄𝐌𝐁𝐄𝐑 𝐀𝐋𝐄𝐑𝐓!</b> 🎉\n\n✨ {user_mention} ✨ 𝐡𝐚𝐬 𝐣𝐨𝐢𝐧𝐞𝐝!",
                parse_mode='HTML'
            )
            await asyncio.sleep(1)
        except:
            pass
        
        # Send welcome message
        try:
            if is_admin and profile_photo:
                await update.message.reply_photo(
                    photo=profile_photo,
                    caption=welcome_message,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text(
                    welcome_message,
                    parse_mode='HTML',
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
        except Exception as e:
            await update.message.reply_text(
                f"🎉✨ <b>𝐖𝐄𝐋𝐂𝐎𝐌𝐄 {user_mention}</b> ✨🎉\n\n🌟 <b>𝐓𝐨 {chat.title}</b> 🌟\n\n💫 <b>𝐖𝐞'𝐫𝐞 𝐠𝐥𝐚𝐝 𝐭𝐨 𝐡𝐚𝐯𝐞 𝐲𝐨𝐮!</b> 💫",
                parse_mode='HTML'
            )
        
        # Admin notification
        await send_to_admin(context, f"""
🎉 <b>𝐍𝐄𝐖 𝐌𝐄𝐌𝐁𝐄𝐑!</b> 🎉

👤 <b>Name:</b> {user_name}
🆔 <b>ID:</b> <code>{user_id}</code>
🏠 <b>Group:</b> {chat.title}
👑 <b>Admin Mode:</b> {'✅ Yes' if is_admin else '❌ No'}
⏰ <b>Time:</b> {current_time}
📊 <b>Total:</b> {stats.total_welcomes}
""")

# ==================== ERROR HANDLER ====================
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Error: {context.error}")
    if ADMIN_ID:
        await send_to_admin(context, f"⚠️ Error: {str(context.error)[:100]}")

# ==================== START COMMAND ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    await update.message.reply_text(f"""
🤖 <b>𝐔𝐋𝐓𝐑𝐀 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐁𝐎𝐓 𝐈𝐒 𝐀𝐂𝐓𝐈𝐕𝐄!</b> 🤖

✨ <b>𝐅𝐞𝐚𝐭𝐮𝐫𝐞𝐬:</b> ✨

🎬 <b>𝐀𝐧𝐢𝐦𝐚𝐭𝐢𝐨𝐧 𝐆𝐈𝐅𝐬</b>
🖼️ <b>𝐏𝐫𝐨𝐟𝐢𝐥𝐞 𝐏𝐡𝐨𝐭𝐨</b>
💝 <b>𝐌𝐚𝐱𝐢𝐦𝐮𝐦 𝐄𝐦𝐨𝐣𝐢𝐬</b>
📢 <b>/all 𝐂𝐨𝐦𝐦𝐚𝐧𝐝</b> - Tag everyone (Admin only)

<b>📌 𝐀𝐝𝐦𝐢𝐧 𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬:</b>
/all Your message - Tag all members

💡 <b>𝐀𝐝𝐝 𝐦𝐞 𝐭𝐨 𝐚𝐧𝐲 𝐠𝐫𝐨𝐮𝐩!</b>
""", parse_mode='HTML')

# ==================== HELP COMMAND ====================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command"""
    await update.message.reply_text(f"""
╔══════════════════════════════════════╗
║  📚 <b>𝐁𝐎𝐓 𝐂𝐎𝐌𝐌𝐀𝐍𝐃𝐒</b>                  ║
╚══════════════════════════════════════╝

✨ <b>𝐀𝐯𝐚𝐢𝐥𝐚𝐛𝐥𝐞 𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬:</b>

/start - Start the bot
/help - Show this help message

👑 <b>𝐀𝐝𝐦𝐢𝐧 𝐎𝐧𝐥𝐲:</b>

/all &lt;message&gt; - Tag all members in group

<b>📝 𝐄𝐱𝐚𝐦𝐩𝐥𝐞:</b>
<code>/all Hello everyone! Important announcement!</code>

⚠️ <b>𝐍𝐨𝐭𝐞:</b>
• Bot must be admin to tag everyone
• Use responsibly
""", parse_mode='HTML')

# ==================== MAIN ====================
def main():
    """Start bot"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS, 
        welcome_new_member
    ))
    application.add_handler(CommandHandler("all", all_command))
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_error_handler(error_handler)
    
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║                                                                ║
    ║     🔥 ULTRA WELCOME BOT - WITH /all COMMAND 🔥               ║
    ║                                                                ║
    ║     ✨ Features:                                               ║
    ║     • Professional Welcome with Max Emojis                    ║
    ║     • Animation GIFs                                          ║
    ║     • /all Command - Tag Everyone (Admin Only)                ║
    ║     • Profile Photo Support                                   ║
    ║     • Admin + Non-Admin Mode                                  ║
    ║                                                                ║
    ║     🚀 BOT IS RUNNING! 🚀                                     ║
    ║                                                                ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()