
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from modules.registry     import ModuleRegistry
from services.panel_access import PanelAccessService
from utils.emojis          import GEAR, HOME, CROSS, WARNING, CHECK, CROWN, SHIELD

logger = logging.getLogger(__name__)

panel_access = PanelAccessService()

async def panel_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    query = update.callback_query
    await query.answer()

    data   = query.data or ""
    parts  = data.split("|")

    if len(parts) < 2:
        return

    try:
        chat_id = int(parts[1])
    except (ValueError, IndexError):
        await query.answer("❌ بيانات غير صالحة", show_alert=True)
        return

    user_id = update.effective_user.id

    has_access = await panel_access.can_access_panel(context.bot, chat_id, user_id)
    if not has_access:
        await query.answer(
            "⛔ ليـس لديـك صلاحيـة الوصـول للوحـة التحكـم لهـذه المجموعـة",
            show_alert=True
        )
        return

    if len(parts) == 2 or parts[2] == "main":
        await show_main_panel(query, context, chat_id)
        return

    module_key = parts[2]
    path       = parts[3:]
    registry   = ModuleRegistry.get()
    module     = registry.get_module(module_key)

    if module is None:
        await query.answer("❌ الوحـدة غيـر موجـودة", show_alert=True)
        return

    try:
        await module.handle_callback(update, context, chat_id, path)
    except Exception as e:
        logger.error(f"خطأ في وحدة {module_key}: {e}", exc_info=True)
        await query.answer("❌ حـدث خطـأ، حـاول مجـددا", show_alert=True)

async def show_main_panel(query, context, chat_id: int):
    
    try:
        chat = await context.bot.get_chat(chat_id)
        chat_name = chat.title or str(chat_id)
    except Exception:
        chat_name = str(chat_id)

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

    await query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def back_to_main_button(chat_id: int) -> InlineKeyboardButton:
    
    return InlineKeyboardButton(f"{HOME} القائمـة الرئيسيـة", callback_data=f"cp|{chat_id}|main")
