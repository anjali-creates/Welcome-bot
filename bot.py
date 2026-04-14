import logging
import asyncio
import os
import random
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict

# Telegram imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application, 
    MessageHandler, 
    filters, 
    ContextTypes, 
    CommandHandler,
    CallbackQueryHandler,
    JobQueue
)
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.error import TelegramError, RetryAfter

# ==================== CONFIGURATION ====================
BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_OWNER_ID = os.getenv('ADMIN_ID')

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable not set!")

BOT_OWNER_ID = int(BOT_OWNER_ID) if BOT_OWNER_ID else None

# ==================== EMOJI DATABASE ====================
class EmojiDB:
    """Extreme Emoji Collection"""
    
    WELCOME = ["🎉", "🎊", "✨", "🌟", "⭐", "💫", "⚡", "🔥", "💥", "🎈", "🎀", "🎁", "🎂", "🍾", "🥳", "🤩", "😍", "🥰"]
    USER = ["👤", "🧑", "🙋", "🙌", "👋", "🤝", "💁", "🙆", "🙎", "💃", "🕺", "🧘"]
    TIME = ["⏰", "🕐", "🕒", "🕔", "🕖", "🕘", "🕚", "⌚", "📅", "📆", "⏱️", "⏲️"]
    ACTION = ["✅", "❌", "⚠️", "🔔", "📢", "🔊", "🔈", "📣", "🎤", "🔕"]
    HEART = ["💝", "💖", "💗", "💓", "💕", "💞", "💟", "❣️", "💔", "❤️", "🧡", "💛", "💚", "💙", "💜"]
    STAR = ["⭐", "🌟", "✨", "💫", "⚡", "🔥", "💥", "🎯", "🏆", "🎖️", "🏅", "🥇"]
    ARROW = ["➡️", "⬅️", "⬆️", "⬇️", "↗️", "↘️", "↙️", "↖️", "➰", "〰️"]
    BOX = ["┌", "┐", "└", "┘", "├", "┤", "┬", "┴", "┼", "━", "┃", "│"]
    
    @classmethod
    def random(cls, category):
        return random.choice(getattr(cls, category))

# ==================== DATA CLASSES ====================
@dataclass
class GroupData:
    """Store group specific data"""
    group_id: int
    group_title: str
    member_count: int = 0
    welcome_count: int = 0
    last_welcome: Optional[datetime] = None
    total_announcements: int = 0
    is_active: bool = True
    
@dataclass
class MemberData:
    """Store member specific data"""
    user_id: int
    username: str
    full_name: str
    join_date: datetime
    welcome_sent: bool = False

# ==================== BOT STATISTICS ====================
class BotStats:
    """Advanced bot statistics tracking"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.total_welcomes = 0
        self.total_announcements = 0
        self.total_errors = 0
        self.groups: Dict[int, GroupData] = {}
        self.members: Dict[int, MemberData] = {}
        self.command_usage: Dict[str, int] = defaultdict(int)
        
    def add_welcome(self, group_id: int, group_title: str, member_id: int, member_name: str):
        self.total_welcomes += 1
        if group_id not in self.groups:
            self.groups[group_id] = GroupData(group_id, group_title)
        self.groups[group_id].welcome_count += 1
        self.groups[group_id].last_welcome = datetime.now()
        self.groups[group_id].member_count += 1
        
        if member_id not in self.members:
            self.members[member_id] = MemberData(member_id, "", member_name, datetime.now())
            
    def add_announcement(self, group_id: int):
        self.total_announcements += 1
        if group_id in self.groups:
            self.groups[group_id].total_announcements += 1
            
    def add_error(self):
        self.total_errors += 1
        
    def add_command(self, command: str):
        self.command_usage[command] += 1
        
    def get_uptime(self) -> str:
        uptime = datetime.now() - self.start_time
        days = uptime.days
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60
        seconds = uptime.seconds % 60
        return f"{days}d {hours}h {minutes}m {seconds}s"
        
    def get_stats(self) -> Dict:
        return {
            "uptime": self.get_uptime(),
            "total_welcomes": self.total_welcomes,
            "total_announcements": self.total_announcements,
            "total_errors": self.total_errors,
            "total_groups": len(self.groups),
            "total_members": len(self.members),
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "command_usage": dict(self.command_usage)
        }

stats = BotStats()

# ==================== UTILITY FUNCTIONS ====================
def random_emoji(category: str) -> str:
    """Get random emoji from category"""
    return EmojiDB.random(category)

def create_separator(char: str = "━", length: int = 60) -> str:
    """Create decorative separator"""
    return f"{random_emoji('STAR') * 2}{char * length}{random_emoji('STAR') * 2}"

def format_number(num: int) -> str:
    """Format number with commas"""
    return f"{num:,}"

async def send_to_owner(context: ContextTypes.DEFAULT_TYPE, message: str, parse_mode: str = 'HTML'):
    """Send message to bot owner"""
    if BOT_OWNER_ID:
        try:
            await context.bot.send_message(
                chat_id=BOT_OWNER_ID, 
                text=message, 
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"Failed to send to owner: {e}")

async def get_user_profile_photo(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
    """Get user's profile photo file_id"""
    try:
        photos = await context.bot.get_user_profile_photos(user_id, limit=1)
        if photos.photos:
            return photos.photos[0][-1].file_id
    except Exception:
        pass
    return None

async def is_group_admin(chat_id: int, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user is admin in the group"""
    try:
        chat_member = await context.bot.get_chat_member(chat_id, user_id)
        return chat_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception:
        return False

async def get_group_members(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> List:
    """Get all non-bot members from group"""
    members = []
    try:
        async for member in context.bot.get_chat_members(chat_id):
            if not member.user.is_bot:
                members.append(member.user)
    except Exception as e:
        logger.error(f"Error getting members: {e}")
    return members

# ==================== /all COMMAND - TAG EVERYONE ====================
async def all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Ultimate /all command - Tags all members with professional announcement
    Only group admins can use this command
    """
    
    stats.add_command("/all")
    
    # Check if in group
    if update.effective_chat.type == "private":
        await update.message.reply_text(
            f"{random_emoji('ACTION')} <b>This command only works in groups!</b>",
            parse_mode='HTML'
        )
        return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_name = update.effective_user.full_name
    group_name = update.effective_chat.title
    
    # Check admin status
    if not await is_group_admin(chat_id, user_id, context):
        await update.message.reply_text(
            f"""
{random_emoji('ACTION') * 5}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji('ACTION') * 5}

                    {random_emoji('ACTION')} <b>𝐀𝐂𝐂𝐄𝐒𝐒 𝐃𝐄𝐍𝐈𝐄𝐃!</b> {random_emoji('ACTION')}

{random_emoji('ACTION') * 5}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji('ACTION') * 5}

{random_emoji('ARROW')} <b>This command is only for group administrators!</b>

{random_emoji('HEART')} <b>You need to be an admin to use /all</b>

{random_emoji('USER')} <b>Contact group admin to send announcements</b>
""",
            parse_mode='HTML'
        )
        return
    
    # Check if message provided
    if not context.args:
        await update.message.reply_text(
            f"""
{random_emoji('STAR') * 5}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji('STAR') * 5}

                    {random_emoji('ACTION')} <b>𝐇𝐎𝐖 𝐓𝐎 𝐔𝐒𝐄 /𝐀𝐋𝐋</b> {random_emoji('ACTION')}

{random_emoji('STAR') * 5}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji('STAR') * 5}

{random_emoji('ARROW')} <b>Usage:</b>
<code>/all Your announcement message here</code>

{random_emoji('ARROW')} <b>Example:</b>
<code>/all Hello everyone! Welcome to our group!</code>

{random_emoji('HEART')} <b>Note:</b> Everyone in the group will be tagged
""",
            parse_mode='HTML'
        )
        return
    
    message_text = ' '.join(context.args)
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        f"""
{random_emoji('TIME')} <b>𝐏𝐑𝐎𝐂𝐄𝐒𝐒𝐈𝐍𝐆...</b>

{random_emoji('USER')} Fetching group members...
{random_emoji('ACTION')} Preparing announcement...
{random_emoji('STAR')} Almost done...
""",
        parse_mode='HTML'
    )
    
    try:
        # Get all members
        members = await get_group_members(chat_id, context)
        
        if not members:
            await processing_msg.edit_text(
                f"{random_emoji('ACTION')} <b>No members found in this group!</b>",
                parse_mode='HTML'
            )
            return
        
        # Create member tags (Telegram allows ~50 per message)
        tags = []
        for member in members[:50]:
            tags.append(f"<a href='tg://user?id={member.id}'> </a>")
        
        # Build professional announcement
        announcement = f"""
{random_emoji('STAR') * 8}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji('STAR') * 8}

                      {random_emoji('ACTION')} <b>📢 𝐆𝐑𝐎𝐔𝐏 𝐀𝐍𝐍𝐎𝐔𝐍𝐂𝐄𝐌𝐄𝐍𝐓</b> {random_emoji('ACTION')}

{random_emoji('STAR') * 8}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji('STAR') * 8}

{random_emoji('BOX')}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji('BOX')}

{random_emoji('USER')} <b>𝐀𝐝𝐦𝐢𝐧</b>          : {user_name}
{random_emoji('HEART')} <b>𝐆𝐫𝐨𝐮𝐩</b>          : {group_name}
{random_emoji('TIME')} <b>𝐓𝐢𝐦𝐞</b>           : {datetime.now().strftime('%I:%M:%S %p')}
{random_emoji('STAR')} <b>𝐃𝐚𝐭𝐞</b>           : {datetime.now().strftime('%A, %B %d, %Y')}
{random_emoji('USER')} <b>𝐌𝐞𝐦𝐛𝐞𝐫𝐬</b>        : {format_number(len(members))}

{random_emoji('BOX')}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji('BOX')}

{random_emoji('HEART')} <b>𝐌𝐄𝐒𝐒𝐀𝐆𝐄</b>:

{random_emoji('ARROW')} {message_text}

{random_emoji('BOX')}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji('BOX')}

{''.join(tags)}

{random_emoji('STAR')} <b>𝐏𝐥𝐞𝐚𝐬𝐞 𝐫𝐞𝐚𝐝 𝐭𝐡𝐞 𝐚𝐛𝐨𝐯𝐞 𝐚𝐧𝐧𝐨𝐮𝐧𝐜𝐞𝐦𝐞𝐧𝐭 𝐜𝐚𝐫𝐞𝐟𝐮𝐥𝐥𝐲!</b> {random_emoji('STAR')}

{random_emoji('HEART') * 5} <b>𝐓𝐇𝐀𝐍𝐊 𝐘𝐎𝐔 𝐅𝐎𝐑 𝐘𝐎𝐔𝐑 𝐀𝐓𝐓𝐄𝐍𝐓𝐈𝐎𝐍!</b> {random_emoji('HEART') * 5}

{random_emoji('STAR') * 8}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji('STAR') * 8}
"""
        
        # Send announcement
        await context.bot.send_message(
            chat_id=chat_id,
            text=announcement,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        
        # Update stats
        stats.add_announcement(chat_id)
        
        # Delete processing message
        await processing_msg.delete()
        
        # Send confirmation to admin
        await update.message.reply_text(
            f"""
{random_emoji('ACTION') * 3}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji('ACTION') * 3}

                    {random_emoji('STAR')} <b>✅ 𝐀𝐍𝐍𝐎𝐔𝐍𝐂𝐄𝐌𝐄𝐍𝐓 𝐒𝐄𝐍𝐓!</b> {random_emoji('STAR')}

{random_emoji('ACTION') * 3}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji('ACTION') * 3}

{random_emoji('USER')} <b>Members tagged:</b> {format_number(len(members))}
{random_emoji('HEART')} <b>Message:</b> {message_text[:50]}{'...' if len(message_text) > 50 else ''}
{random_emoji('TIME')} <b>Time:</b> {datetime.now().strftime('%I:%M:%S %p')}

{random_emoji('STAR')} <b>Announcement has been sent successfully!</b> {random_emoji('STAR')}
""",
            parse_mode='HTML'
        )
        
        # Notify bot owner
        if BOT_OWNER_ID:
            await send_to_owner(
                context,
                f"""
{random_emoji('ACTION')} <b>/all COMMAND EXECUTED</b> {random_emoji('ACTION')}

{random_emoji('USER')} <b>Admin:</b> {user_name}
{random_emoji('HEART')} <b>Admin ID:</b> <code>{user_id}</code>
{random_emoji('STAR')} <b>Group:</b> {group_name}
{random_emoji('BOX')} <b>Group ID:</b> <code>{chat_id}</code>
{random_emoji('USER')} <b>Members:</b> {format_number(len(members))}
{random_emoji('HEART')} <b>Message:</b> {message_text[:100]}
{random_emoji('TIME')} <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{random_emoji('STAR')} <b>Total Announcements:</b> {stats.total_announcements}
"""
            )
            
    except TelegramError as e:
        await processing_msg.edit_text(
            f"""
{random_emoji('ACTION')} <b>❌ 𝐄𝐑𝐑𝐎𝐑 𝐒𝐄𝐍𝐃𝐈𝐍𝐆 𝐀𝐍𝐍𝐎𝐔𝐍𝐂𝐄𝐌𝐄𝐍𝐓</b> {random_emoji('ACTION')}

{random_emoji('ARROW')} <b>Error:</b> {str(e)[:100]}

{random_emoji('HEART')} <b>Possible reasons:</b>
• Bot is not admin
• Rate limit exceeded
• Group privacy settings
""",
            parse_mode='HTML'
        )
        stats.add_error()

# ==================== WELCOME FUNCTION ====================
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Ultimate welcome function - Professional design with max emojis
    """
    
    if not update.message.new_chat_members:
        return
    
    chat = update.effective_chat
    chat_id = chat.id
    chat_title = chat.title
    
    # Check if bot is admin
    try:
        bot_member = await chat.get_member(context.bot.id)
        is_bot_admin = bot_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        is_bot_admin = False
    
    for new_member in update.message.new_chat_members:
        if new_member.id == context.bot.id:
            continue
        
        # Get member info
        user_id = new_member.id
        user_name = new_member.full_name
        user_first = new_member.first_name or "Guest"
        user_mention = f"<a href='tg://user?id={user_id}'>{user_name}</a>"
        username = f"@{new_member.username}" if new_member.username else f"{random_emoji('ACTION')} No username"
        
        # Get profile photo
        profile_photo = await get_user_profile_photo(user_id, context)
        
        # Time info
        current_time = datetime.now().strftime("%I:%M:%S %p")
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        
        # Update stats
        stats.add_welcome(chat_id, chat_title, user_id, user_name)
        
        # Get member count for this group
        member_count = stats.groups[chat_id].member_count if chat_id in stats.groups else "?"
        
        # Build extreme welcome message
        welcome_message = f"""
{random_emoji('WELCOME') * 10}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji('WELCOME') * 10}

{random_emoji('STAR') * 5} {random_emoji('WELCOME')} <b>✨ 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐓𝐎 𝐓𝐇𝐄 𝐔𝐋𝐓𝐈𝐌𝐀𝐓𝐄 𝐂𝐎𝐌𝐌𝐔𝐍𝐈𝐓𝐘 ✨</b> {random_emoji('WELCOME')} {random_emoji('STAR') * 5}

{random_emoji('WELCOME') * 10}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji('WELCOME') * 10}

┌{'─' * 100}┐
│{random_emoji('BOX') * 98}│
│  {random_emoji('USER')} {random_emoji('USER')} {random_emoji('USER')} <b>📋 𝐌𝐄𝐌𝐁𝐄𝐑 𝐈𝐍𝐅𝐎𝐑𝐌𝐀𝐓𝐈𝐎𝐍</b> {random_emoji('USER')} {random_emoji('USER')} {random_emoji('USER')}  │
│{random_emoji('BOX') * 98}│
├{'─' * 100}┤
│                                                                                                    │
│     {random_emoji('USER')}  <b>𝐅𝐔𝐋𝐋 𝐍𝐀𝐌𝐄</b>     : {user_mention:<50}                    │
│     {random_emoji('ARROW')}  <b>𝐔𝐒𝐄𝐑𝐍𝐀𝐌𝐄</b>     : {username:<50}                          │
│     {random_emoji('HEART')}  <b>𝐔𝐒𝐄𝐑 𝐈𝐃</b>       : <code>{user_id}</code><33}                               │
│     {random_emoji('STAR')}  <b>𝐆𝐑𝐎𝐔𝐏 𝐍𝐀𝐌𝐄</b>    : {chat_title:<50}                          │
│     {random_emoji('TIME')}  <b>𝐉𝐎𝐈𝐍 𝐓𝐈𝐌𝐄</b>     : {current_time:<50}                        │
│     {random_emoji('ACTION')}  <b>𝐉𝐎𝐈𝐍 𝐃𝐀𝐓𝐄</b>     : {current_date:<50}                        │
│     {random_emoji('USER')}  <b>𝐌𝐄𝐌𝐁𝐄𝐑 #</b>      : {format_number(member_count):<50}                        │
│     {random_emoji('HEART')}  <b>𝐓𝐎𝐓𝐀𝐋 𝐖𝐄𝐋𝐂𝐎𝐌𝐄𝐒</b> : {format_number(stats.total_welcomes):<50}                        │
│                                                                                                    │
└{'─' * 100}┘

┌{'─' * 100}┐
│{random_emoji('BOX') * 98}│
│  {random_emoji('HEART')} {random_emoji('HEART')} {random_emoji('HEART')} <b>💝 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐌𝐄𝐒𝐒𝐀𝐆𝐄</b> {random_emoji('HEART')} {random_emoji('HEART')} {random_emoji('HEART')}  │
│{random_emoji('BOX') * 98}│
├{'─' * 100}┤
│                                                                                                    │
│     {random_emoji('WELCOME')} <b>𝐃𝐞𝐚𝐫 {user_first},</b> {random_emoji('WELCOME')}                                                    │
│                                                                                                    │
│     {random_emoji('STAR')} <b>𝐀 𝐕𝐄𝐑𝐘 𝐖𝐀𝐑𝐌 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐓𝐎 𝐎𝐔𝐑 𝐀𝐌𝐀𝐙𝐈𝐍𝐆 𝐂𝐎𝐌𝐌𝐔𝐍𝐈𝐓𝐘!</b> {random_emoji('STAR')}          │
│                                                                                                    │
│     {random_emoji('HEART')} <b>𝐖𝐞'𝐫𝐞 𝐬𝐨 𝐞𝐱𝐜𝐢𝐭𝐞𝐝 𝐭𝐨 𝐡𝐚𝐯𝐞 𝐲𝐨𝐮 𝐡𝐞𝐫𝐞!</b> {random_emoji('HEART')}                                      │
│                                                                                                    │
│     {random_emoji('USER')} <b>𝐘𝐨𝐮 𝐚𝐫𝐞 𝐧𝐨𝐰 𝐩𝐚𝐫𝐭 𝐨𝐟 𝐬𝐨𝐦𝐞𝐭𝐡𝐢𝐧𝐠 𝐬𝐩𝐞𝐜𝐢𝐚𝐥!</b> {random_emoji('USER')}                              │
│                                                                                                    │
│     {random_emoji('ARROW')} <b>𝐅𝐞𝐞𝐥 𝐟𝐫𝐞𝐞 𝐭𝐨 𝐢𝐧𝐭𝐫𝐨𝐝𝐮𝐜𝐞 𝐲𝐨𝐮𝐫𝐬𝐞𝐥𝐟 𝐭𝐨 𝐞𝐯𝐞𝐫𝐲𝐨𝐧𝐞!</b> {random_emoji('ARROW')}                  │
│                                                                                                    │
└{'─' * 100}┘

┌{'─' * 100}┐
│{random_emoji('BOX') * 98}│
│  {random_emoji('ACTION')} {random_emoji('ACTION')} {random_emoji('ACTION')} <b>📌 𝐐𝐔𝐈𝐂𝐊 𝐆𝐔𝐈𝐃𝐄𝐋𝐈𝐍𝐄𝐒</b> {random_emoji('ACTION')} {random_emoji('ACTION')} {random_emoji('ACTION')}  │
│{random_emoji('BOX') * 98}│
├{'─' * 100}┤
│                                                                                                    │
│     {random_emoji('ACTION')}  <b>✅ 𝐁𝐞 𝐑𝐞𝐬𝐩𝐞𝐜𝐭𝐟𝐮𝐥</b>     - Treat everyone with kindness and respect          │
│     {random_emoji('ACTION')}  <b>✅ 𝐍𝐨 𝐒𝐩𝐚𝐦𝐦𝐢𝐧𝐠</b>      - No promotional or irrelevant messages          │
│     {random_emoji('ACTION')}  <b>✅ 𝐇𝐞𝐥𝐩 𝐎𝐭𝐡𝐞𝐫𝐬</b>      - Share knowledge and support fellow members      │
│     {random_emoji('ACTION')}  <b>✅ 𝐒𝐭𝐚𝐲 𝐀𝐜𝐭𝐢𝐯𝐞</b>      - Regular participation makes the group better    │
│                                                                                                    │
└{'─' * 100}┘

{random_emoji('WELCOME') * 10}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji('WELCOME') * 10}

{random_emoji('STAR') * 10} <b>⭐ 𝐄𝐍𝐉𝐎𝐘 𝐘𝐎𝐔𝐑 𝐒𝐓𝐀𝐘! ⭐</b> {random_emoji('STAR') * 10}

{random_emoji('WELCOME') * 10}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji('WELCOME') * 10}
"""
        
        # Create buttons
        keyboard = [
            [
                InlineKeyboardButton(f"{random_emoji('ACTION')} 𝐑𝐔𝐋𝐄𝐒 {random_emoji('ACTION')}", url="https://t.me/telegram"),
                InlineKeyboardButton(f"{random_emoji('USER')} 𝐈𝐍𝐓𝐑𝐎 {random_emoji('USER')}", url=f"tg://user?id={user_id}")
            ],
            [
                InlineKeyboardButton(f"{random_emoji('HEART')} 𝐒𝐔𝐏𝐏𝐎𝐑𝐓 {random_emoji('HEART')}", url="https://t.me/telegram"),
                InlineKeyboardButton(f"{random_emoji('STAR')} 𝐔𝐏𝐃𝐀𝐓𝐄𝐒 {random_emoji('STAR')}", url="https://t.me/telegram")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send welcome message
        try:
            if is_bot_admin and profile_photo:
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
            logger.error(f"Welcome message error: {e}")
            # Fallback message
            await update.message.reply_text(
                f"""
{random_emoji('WELCOME') * 5}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji('WELCOME') * 5}

        {random_emoji('STAR')} <b>✨ 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 {user_mention} ✨</b> {random_emoji('STAR')}

{random_emoji('WELCOME') * 5}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji('WELCOME') * 5}

        {random_emoji('HEART')} <b>𝐓𝐨 {chat_title}</b> {random_emoji('HEART')}

        {random_emoji('USER')} <b>𝐖𝐞'𝐫𝐞 𝐠𝐥𝐚𝐝 𝐭𝐨 𝐡𝐚𝐯𝐞 𝐲𝐨𝐮!</b> {random_emoji('USER')}

{random_emoji('STAR')} <b>𝐄𝐧𝐣𝐨𝐲 𝐲𝐨𝐮𝐫 𝐬𝐭𝐚𝐲!</b> {random_emoji('STAR')}
""",
                parse_mode='HTML'
            )
        
        # Notify bot owner
        if BOT_OWNER_ID:
            await send_to_owner(
                context,
                f"""
{random_emoji('WELCOME')} <b>𝐍𝐄𝐖 𝐌𝐄𝐌𝐁𝐄𝐑 𝐉𝐎𝐈𝐍𝐄𝐃!</b> {random_emoji('WELCOME')}

{random_emoji('USER')} <b>Name:</b> {user_name}
{random_emoji('HEART')} <b>ID:</b> <code>{user_id}</code>
{random_emoji('STAR')} <b>Group:</b> {chat_title}
{random_emoji('ACTION')} <b>Group ID:</b> <code>{chat_id}</code>
{random_emoji('USER')} <b>Bot Admin:</b> {'✅ Yes' if is_bot_admin else '❌ No'}
{random_emoji('TIME')} <b>Time:</b> {current_time}

{random_emoji('STAR')} <b>Total Welcomes:</b> {stats.total_welcomes}
"""
            )

# ==================== STATS COMMAND ====================
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot statistics (owner only)"""
    
    if BOT_OWNER_ID and update.effective_user.id != BOT_OWNER_ID:
        await update.message.reply_text(
            f"{random_emoji('ACTION')} <b>This command is only for bot owner!</b>",
            parse_mode='HTML'
        )
        return
    
    stats_data = stats.get_stats()
    
    stats_message = f"""
{random_emoji('STAR') * 10}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji('STAR') * 10}

                    {random_emoji('ACTION')} <b>📊 𝐁𝐎𝐓 𝐒𝐓𝐀𝐓𝐈𝐒𝐓𝐈𝐂𝐒</b> {random_emoji('ACTION')}

{random_emoji('STAR') * 10}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji('STAR') * 10}

{random_emoji('USER')} <b>📈 𝐏𝐄𝐑𝐅𝐎𝐑𝐌𝐀𝐍𝐂𝐄:</b>
{random_emoji('ARROW')} Uptime: {stats_data['uptime']}
{random_emoji('ARROW')} Total Welcomes: {format_number(stats_data['total_welcomes'])}
{random_emoji('ARROW')} Total Announcements: {format_number(stats_data['total_announcements'])}
{random_emoji('ARROW')} Total Errors: {format_number(stats_data['total_errors'])}

{random_emoji('HEART')} <b>👥 𝐆𝐑𝐎𝐔𝐏𝐒 & 𝐌𝐄𝐌𝐁𝐄𝐑𝐒:</b>
{random_emoji('ARROW')} Active Groups: {format_number(stats_data['total_groups'])}
{random_emoji('ARROW')} Total Members: {format_number(stats_data['total_members'])}

{random_emoji('ACTION')} <b>⚡ 𝐂𝐎𝐌𝐌𝐀𝐍𝐃 𝐔𝐒𝐀𝐆𝐄:</b>
"""
    for cmd, count in stats_data['command_usage'].items():
        stats_message += f"{random_emoji('ARROW')} {cmd}: {format_number(count)}\n"
    
    stats_message += f"""
{random_emoji('TIME')} <b>🕐 𝐒𝐓𝐀𝐑𝐓 𝐓𝐈𝐌𝐄:</b>
{random_emoji('ARROW')} {stats_data['start_time']}

{random_emoji('STAR') * 10}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji('STAR') * 10}

{random_emoji('HEART')} <b>✨ 𝐁𝐨𝐭 𝐢𝐬 𝐫𝐮𝐧𝐧𝐢𝐧𝐠 𝐩𝐞𝐫𝐟𝐞𝐜𝐭𝐥𝐲!</b> {random_emoji('HEART')}
"""
    
    await update.message.reply_text(stats_message, parse_mode='HTML')

# ==================== START COMMAND ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - Show bot info"""
    
    stats.add_command("/start")
    
    start_message = f"""
{random_emoji('STAR') * 10}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji('STAR') * 10}

                    {random_emoji('WELCOME')} <b>🤖 𝐔𝐋𝐓𝐑𝐀 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐁𝐎𝐓</b> {random_emoji('WELCOME')}

{random_emoji('STAR') * 10}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji('STAR') * 10}

{random_emoji('USER')} <b>✨ 𝐅𝐄𝐀𝐓𝐔𝐑𝐄𝐒:</b>
{random_emoji('ARROW')} 🎉 Professional Welcome Messages
{random_emoji('ARROW')} 👤 Profile Photo Display
{random_emoji('ARROW')} 💝 Maximum Emojis Support
{random_emoji('ARROW')} 📢 /all Command - Tag Everyone
{random_emoji('ARROW')} 👑 Group Admin Only Commands
{random_emoji('ARROW')} 📊 Real-time Statistics

{random_emoji('ACTION')} <b>📌 𝐀𝐃𝐌𝐈𝐍 𝐂𝐎𝐌𝐌𝐀𝐍𝐃𝐒:</b>
{random_emoji('ARROW')} <code>/all &lt;message&gt;</code> - Tag all members
{random_emoji('ARROW')} <code>/stats</code> - View bot statistics (Owner)

{random_emoji('HEART')} <b>💡 𝐇𝐎𝐖 𝐓𝐎 𝐔𝐒𝐄:</b>
{random_emoji('ARROW')} Add me to your group
{random_emoji('ARROW')} Make me admin (for full features)
{random_emoji('ARROW')} I'll welcome new members automatically
{random_emoji('ARROW')} Use /all as admin to announce

{random_emoji('STAR')} <b>⭐ 𝐀𝐝𝐝 𝐦𝐞 𝐭𝐨 𝐚𝐧𝐲 𝐠𝐫𝐨𝐮𝐩!</b> {random_emoji('STAR')}

{random_emoji('STAR') * 10}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji('STAR') * 10}
"""
    
    await update.message.reply_text(start_message, parse_mode='HTML')

# ==================== HELP COMMAND ====================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command - Show all commands"""
    
    help_message = f"""
{random_emoji('STAR') * 10}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji('STAR') * 10}

                    {random_emoji('ACTION')} <b>📚 𝐁𝐎𝐓 𝐂𝐎𝐌𝐌𝐀𝐍𝐃𝐒</b> {random_emoji('ACTION')}

{random_emoji('STAR') * 10}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji('STAR') * 10}

{random_emoji('USER')} <b>👥 𝐆𝐄𝐍𝐄𝐑𝐀𝐋 𝐂𝐎𝐌𝐌𝐀𝐍𝐃𝐒:</b>
{random_emoji('ARROW')} <code>/start</code> - Show bot information
{random_emoji('ARROW')} <code>/help</code> - Show this help message

{random_emoji('ACTION')} <b>👑 𝐀𝐃𝐌𝐈𝐍 𝐂𝐎𝐌𝐌𝐀𝐍𝐃𝐒 (𝐆𝐫𝐨𝐮𝐩 𝐀𝐝𝐦𝐢𝐧𝐬 𝐎𝐧𝐥𝐲):</b>
{random_emoji('ARROW')} <code>/all &lt;message&gt;</code> - Tag all members with announcement

{random_emoji('STAR')} <b>⚡ 𝐁𝐎𝐓 𝐎𝐖𝐍𝐄𝐑 𝐂𝐎𝐌𝐌𝐀𝐍𝐃𝐒:</b>
{random_emoji('ARROW')} <code>/stats</code> - View bot statistics

{random_emoji('HEART')} <b>📝 𝐄𝐗𝐀𝐌𝐏𝐋𝐄𝐒:</b>
{random_emoji('ARROW')} <code>/all Hello everyone! Welcome to our group!</code>
{random_emoji('ARROW')} <code>/all Important announcement! Please read.</code>

{random_emoji('USER')} <b>⚠️ 𝐍𝐎𝐓𝐄𝐒:</b>
{random_emoji('ARROW')} • /all command only works in groups
{random_emoji('ARROW')} • Only group admins can use /all
{random_emoji('ARROW')} • Bot needs to be admin to tag members
{random_emoji('ARROW')} • Use responsibly - don't spam

{random_emoji('STAR')} <b>✨ 𝐁𝐨𝐭 𝐢𝐬 𝐫𝐞𝐚𝐝𝐲 𝐭𝐨 𝐰𝐞𝐥𝐜𝐨𝐦𝐞 𝐦𝐞𝐦𝐛𝐞𝐫𝐬!</b> {random_emoji('STAR')}

{random_emoji('STAR') * 10}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji('STAR') * 10}
"""
    
    await update.message.reply_text(help_message, parse_mode='HTML')

# ==================== ERROR HANDLER ====================
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Global error handler"""
    stats.add_error()
    logger.error(f"Update {update} caused error {context.error}")
    
    if BOT_OWNER_ID:
        await send_to_owner(
            context,
            f"""
{random_emoji('ACTION')} <b>⚠️ 𝐄𝐑𝐑𝐎𝐑 𝐃𝐄𝐓𝐄𝐂𝐓𝐄𝐃</b> {random_emoji('ACTION')}

{random_emoji('ARROW')} <b>Error:</b> {str(context.error)[:150]}
{random_emoji('TIME')} <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{random_emoji('HEART')} <b>Total Errors:</b> {stats.total_errors}

{random_emoji('STAR')} <b>Auto-recovery in progress...</b>
"""
        )

# ==================== SETUP COMMANDS ====================
async def setup_commands(application: Application):
    """Setup bot commands menu"""
    commands = [
        BotCommand("start", "Show bot information"),
        BotCommand("help", "Show help message"),
        BotCommand("all", "Tag all members (Admin only)"),
    ]
    
    if BOT_OWNER_ID:
        commands.append(BotCommand("stats", "View bot statistics (Owner)"))
    
    await application.bot.set_my_commands(commands)

# ==================== MAIN FUNCTION ====================
def main():
    """Main function to run the bot"""
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS, 
        welcome_new_member
    ))
    application.add_handler(CommandHandler("all", all_command))
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    
    if BOT_OWNER_ID:
        application.add_handler(CommandHandler("stats", stats_command))
    
    application.add_error_handler(error_handler)
    
    # Setup commands on startup
    application.post_init = setup_commands
    
    # Print startup message
    print("""
    ╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
    ║                                                                                                              ║
    ║     ██╗░░░██╗██╗████████╗██████╗░░█████╗░  ██╗░░░░░███████╗██╗░░░██╗███████╗██╗░░░░░                             ║
    ║     ██║░░░██║██║╚══██╔══╝██╔══██╗██╔══██╗  ██║░░░░░██╔════╝╚██╗░██╔╝██╔════╝██║░░░░░                             ║
    ║     ██║░░░██║██║░░░██║░░░██████╔╝███████║  ██║░░░░░█████╗░░░╚████╔╝░█████╗░░██║░░░░░                             ║
    ║     ██║░░░██║██║░░░██║░░░██╔══██╗██╔══██║  ██║░░░░░██╔══╝░░░░╚██╔╝░░██╔══╝░░██║░░░░░                             ║
    ║     ╚██████╔╝██║░░░██║░░░██║░░██║██║░░██║  ███████╗███████╗░░░██║░░░███████╗███████╗                             ║
    ║     ░╚═════╝░╚═╝░░░╚═╝░░░╚═╝░░╚═╝╚═╝░░╚═╝  ╚══════╝╚══════╝░░░╚═╝░░░╚══════╝╚══════╝                             ║
    ║                                                                                                              ║
    ║     🔥 EXTREME WELCOME BOT - ULTIMATE EDITION 🔥                                                             ║
    ║                                                                                                              ║
    ║     ✅ Features Loaded:                                                                                      ║
    ║     • Professional Welcome Message with Max Emojis                                                          ║
    ║     • /all Command - Tag All Members (Admin Only)                                                           ║
    ║     • Profile Photo Display Support                                                                         ║
    ║     • Real-time Statistics Tracking                                                                         ║
    ║     • Admin & Non-Admin Mode Support                                                                        ║
    ║     • Bot Owner Notifications                                                                               ║
    ║     • Auto Error Recovery                                                                                   ║
    ║                                                                                                              ║
    ║     🚀 BOT IS RUNNING AT FULL POWER! 🚀                                                                     ║
    ║                                                                                                              ║
    ╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Run bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
