
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from modules.base          import BaseModule
from services.panel_access import PanelAccessService
from services.roles        import RolesService
from utils.emojis          import (
    SHIELD, PEOPLE, LOCK, UNLOCK, CHECK, CROSS,
    PERSON, GEAR, HOME, DIV
)
from config import (
    PANEL_ACCESS_ALL_ADMINS, PANEL_ACCESS_SPECIFIC, PANEL_ACCESS_OWNER_ONLY
)

logger = logging.getLogger(__name__)

panel_access = PanelAccessService()
roles_svc    = RolesService()

class PermissionsModule(BaseModule):
    KEY   = "permissions"
    NAME  = "الصلاحيات"
    EMOJI = SHIELD

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                               chat_id: int, path: list[str]):
        query   = update.callback_query
        user_id = update.effective_user.id

        is_owner = await roles_svc.is_owner(user_id)
        from utils.helpers import is_group_creator
        is_creator = await is_group_creator(context.bot, chat_id, user_id)

        if not is_owner and not is_creator:
            await query.answer("⛔ هـذا القسـم للمالـك أو منشـئ المجموعـة فقـط", show_alert=True)
            return

        if not path:
            await self._show_permissions_menu(query, context, chat_id)
            return

        action = path[0]

        if action == "all":
            await panel_access.set_mode(chat_id, PANEL_ACCESS_ALL_ADMINS)
            await query.answer("✅ تـم السمـاح لجميـع المشرفيـن")
            await self._show_permissions_menu(query, context, chat_id)

        elif action == "own":
            await panel_access.set_mode(chat_id, PANEL_ACCESS_OWNER_ONLY)
            await query.answer("✅ تـم تقييـد الوصـول للمالـك فقـط")
            await self._show_permissions_menu(query, context, chat_id)

        elif action == "sp":
            await panel_access.set_mode(chat_id, PANEL_ACCESS_SPECIFIC)
            await query.answer("✅ وضـع المشرفيـن المحددـين")
            await self._show_permissions_menu(query, context, chat_id)

        else:
            await self._show_permissions_menu(query, context, chat_id)

    async def _show_permissions_menu(self, query, context, chat_id: int):
        mode = await panel_access.get_mode(chat_id)

        mode_labels = {
            PANEL_ACCESS_ALL_ADMINS: f"{UNLOCK} جميـع المشرفيـن",
            PANEL_ACCESS_SPECIFIC:   f"{PERSON} مشرفـون محددـون",
            PANEL_ACCESS_OWNER_ONLY: f"{LOCK} المالـك فقـط",
        }
        current = mode_labels.get(mode, mode)

        keyboard = [
            [InlineKeyboardButton(
                f"{'✅ ' if mode == PANEL_ACCESS_ALL_ADMINS else ''}👥 السمـاح لجميـع المشرفيـن",
                callback_data=self.cb(chat_id, "all")
            )],
            [InlineKeyboardButton(
                f"{'✅ ' if mode == PANEL_ACCESS_SPECIFIC else ''}👤 مشرفـون محددـون فقـط",
                callback_data=self.cb(chat_id, "sp")
            )],
            [InlineKeyboardButton(
                f"{'✅ ' if mode == PANEL_ACCESS_OWNER_ONLY else ''}🔒 المالـك فقـط",
                callback_data=self.cb(chat_id, "own")
            )],
            [InlineKeyboardButton(f"{HOME} رجـوع", callback_data=f"cp|{chat_id}|main")],
        ]

        text = (
            f"<b>{SHIELD} صلاحيـات لوحـة التحكـم</b>\n\n"
            f"{DIV}\n\n"
            f"<b>الوضـع الحالـي: {current}</b>\n\n"
            f"<blockquote>"
            f"<b>• جميـع المشرفيـن</b> — كـل مشـرف في المجموعـة يستطيـع الوصـول للوحـة\n\n"
            f"<b>• مشرفـون محددـون</b> — فقـط مـن تختـاره يصـل للوحـة\n\n"
            f"<b>• المالـك فقـط</b> — لا أحـد يصـل للوحـة سواك"
            f"</blockquote>"
        )

        await query.edit_message_text(
            text=text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
