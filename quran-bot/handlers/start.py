
import html
import logging
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
)
from telegram.ext import ContextTypes

from config          import WEBAPP_URL
from services.roles  import RolesService
from database        import Database
from utils.emojis    import (
    LINE, HIJAB, BOOK, PRAY, BEADS, FAQ, INFO, BACK,
    QUESTION, CLOCK, PEN, PRAY2, FAQ2, PRAY3, DOWN,
    PC, NUM1, NUM2, NUM3, NUM4, WAVE, GEAR
)

logger  = logging.getLogger(__name__)
roles   = RolesService()
db      = Database.get()

WAITING_QUESTION = "waiting_religious_question"

def ce(emoji_id: str, fallback: str) -> str:
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

def main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("المصحـف الكـريم",    web_app=WebAppInfo(url=WEBAPP_URL),              icon_custom_emoji_id="5888888221424685873")],
        [InlineKeyboardButton("الاذكـار",            web_app=WebAppInfo(url=f"{WEBAPP_URL}/azkar"),   icon_custom_emoji_id="5996581850607261681")],
        [InlineKeyboardButton("اسئـلة دينيـة",      callback_data="questions",                        icon_custom_emoji_id="5783013214539225637")],
        [InlineKeyboardButton("عـن البـوت  (FAQ)",  callback_data="about",                            icon_custom_emoji_id="5431450689454750972")],
        [InlineKeyboardButton("قنـاة البـوت",       callback_data="channel",                          icon_custom_emoji_id="5224688446974475279")],
    ]
    return InlineKeyboardMarkup(keyboard)

def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("رجـوع للقائمـة", callback_data="back_main", icon_custom_emoji_id="5960671702059848143")]
    ])

def build_welcome(user) -> str:
    full_name = html.escape(user.full_name)
    mention   = f'<a href="tg://user?id={user.id}">{full_name}</a>'
    return (
        f"<b>• اهـلا وسهـلا يـا : </b>{mention}\n"
        f"<b>{LINE}{LINE}{LINE}{LINE}{HIJAB}{LINE}{LINE}{LINE}{LINE}</b>\n\n"
        f"<blockquote><b>• اهـلا بـك انـا بـوت القـران الكـريم {BOOK}</b></blockquote>\n"
        f"<blockquote><b>• يمكنـك مـن خلالـي التصفـح في كتـاب الله</b></blockquote>\n"
        f"<blockquote><b>• وايضـا يمكنـك قـراءة الاذكـار {PRAY}</b></blockquote>"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    user = update.effective_user
    context.user_data.pop("state", None)
    context.user_data.pop("sched", None)

    if context.args:
        arg = context.args[0]
        if arg.startswith("panel_"):
            try:
                chat_id = int(arg[6:])  
                await _open_panel(update, context, chat_id)
                return
            except (ValueError, IndexError):
                pass

    bot_username = (await context.bot.get_me()).username
    keyboard = main_menu_keyboard()

    add_btn = InlineKeyboardButton(
        "➕ قـم بإضافـة البـوت الآن",
        url=f"https://t.me/{bot_username}?startgroup=true"
    )
    kb_list = list(keyboard.inline_keyboard)
    kb_list.append([add_btn])
    keyboard = InlineKeyboardMarkup(kb_list)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=build_welcome(user),
        parse_mode="HTML",
        reply_markup=keyboard,
    )

async def _open_panel(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    
    from services.panel_access import PanelAccessService
    from modules.panel.handler import show_main_panel

    user    = update.effective_user
    pa_svc  = PanelAccessService()

    has_access = await pa_svc.can_access_panel(context.bot, chat_id, user.id)

    if not has_access:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=(
                "<b>⛔ ليس لديك صلاحية الوصول للوحة التحكم لهذه المجموعة</b>\n\n"
                "<blockquote><b>يجب أن تكون مشرفا في المجموعة للوصول لهذه اللوحة</b></blockquote>"
            ),
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )
        return

    try:
        chat = await context.bot.get_chat(chat_id)
        chat_name = chat.title or str(chat_id)
    except Exception:
        chat_name = str(chat_id)

    await db.upsert_group(chat_id, chat_name, "group")

    from modules.registry import ModuleRegistry
    registry = ModuleRegistry.get()
    modules  = registry.all_modules()

    keyboard = []
    content_modules = [m for m in modules if m.KEY != "permissions"]
    perms_module    = registry.get_module("permissions")

    row = []
    for mod in content_modules:
        row.append(mod.get_menu_button(chat_id))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    if perms_module:
        keyboard.append([perms_module.get_menu_button(chat_id)])

    text = (
        f"<b>{GEAR} لوحـة التحكـم</b>\n\n"
        f"<b>📍 المجموعـة: {chat_name}</b>\n\n"
        f"<blockquote><b>اختـر القسـم الـذي تريـد إدارتـه</b></blockquote>"
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
