
import logging
import html
from datetime import datetime, timedelta
from telegram import Chat, ChatMember, User
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

def escape(text: str) -> str:
    
    return html.escape(str(text))

def mention(user: User) -> str:
    
    name = escape(user.full_name)
    return f'<a href="tg://user?id={user.id}">{name}</a>'

def format_datetime(dt: datetime) -> str:
    
    return dt.strftime("%Y-%m-%d %H:%M")

def parse_time(time_str: str) -> tuple[int, int] | None:
    
    try:
        parts = time_str.strip().split(":")
        if len(parts) != 2:
            return None
        h, m = int(parts[0]), int(parts[1])
        if 0 <= h <= 23 and 0 <= m <= 59:
            return h, m
    except (ValueError, IndexError):
        pass
    return None

def parse_date(date_str: str) -> datetime | None:
    
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None

def next_occurrence(hour: int, minute: int) -> datetime:
    
    now = datetime.utcnow()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return target

def interval_to_seconds(interval_type: str, interval_value: int = 1) -> int:
    
    mapping = {
        "minutes": 60,
        "hours":   3600,
        "daily":   86400,
        "weekly":  604800,
        "monthly": 2592000,    
        "yearly":  31536000,   
    }
    base = mapping.get(interval_type, 60)
    return base * interval_value

def interval_label(interval_type: str, interval_value: int = 1) -> str:
    
    labels = {
        "minutes": f"كـل {interval_value} دقيقـة" if interval_value > 1 else "كـل دقيقـة",
        "hours":   f"كـل {interval_value} ساعـة" if interval_value > 1 else "كـل ساعـة",
        "daily":   "يوميـاً",
        "weekly":  "أسبوعيـاً",
        "monthly": "شهريـاً",
        "yearly":  "سنويـاً",
    }
    return labels.get(interval_type, f"كـل {interval_value} وحـدة")

async def is_group_creator(bot, chat_id: int, user_id: int) -> bool:
    
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status == ChatMember.OWNER
    except Exception as e:
        logger.debug(f"is_group_creator error: {e}")
        return False

async def is_group_admin(bot, chat_id: int, user_id: int) -> bool:
    
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in (ChatMember.OWNER, ChatMember.ADMINISTRATOR)
    except Exception as e:
        logger.debug(f"is_group_admin error: {e}")
        return False

async def get_chat_safe(bot, chat_id: int) -> Chat | None:
    
    try:
        return await bot.get_chat(chat_id)
    except Exception as e:
        logger.debug(f"get_chat_safe error for {chat_id}: {e}")
        return None
