
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from services.roles import RolesService
from config         import (
    MAX_OWNERS, ALL_PERMISSIONS, DEFAULT_ADMIN_PERMISSIONS,
    PERM_MANAGE_ADMINS
)
from utils.emojis   import CROWN, SHIELD, CHECK, CROSS, PEOPLE, DIV

logger = logging.getLogger(__name__)
roles  = RolesService()

async def _require_owner(update: Update) -> bool:
    
    if not await roles.is_owner(update.effective_user.id):
        await update.message.reply_text(
            "<b>⛔ هـذا الأمـر للمالـك فقـط</b>",
            parse_mode="HTML"
        )
        return False
    return True

async def _require_owner_or_manage_admin(update: Update) -> bool:
    
    uid = update.effective_user.id
    if await roles.is_owner(uid):
        return True
    if await roles.has_permission(uid, PERM_MANAGE_ADMINS):
        return True
    await update.message.reply_text(
        "<b>⛔ ليـس لديـك صلاحيـة هـذا الأمـر</b>",
        parse_mode="HTML"
    )
    return False

async def cmd_owners(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_owner(update):
        return

    owners = await roles.get_owners()
    if not owners:
        await update.message.reply_text("<b>لا يوجـد مالكـون مسجلـون</b>", parse_mode="HTML")
        return

    lines = [f"<b>{CROWN} المالكـون ({len(owners)}/{MAX_OWNERS}):</b>\n"]
    for o in owners:
        name = o.get("full_name") or o.get("username") or str(o["user_id"])
        lines.append(f"<b>• {name}</b> — <code>{o['user_id']}</code>")

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")

async def cmd_addowner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_owner(update):
        return

    if not context.args:
        await update.message.reply_text(
            "<b>الاستخـدام:</b> <code>/addowner {user_id}</code>",
            parse_mode="HTML"
        )
        return

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("<b>❌ معـرف المستخـدم يجـب أن يكـون رقمـا</b>", parse_mode="HTML")
        return

    try:
        user_info = await context.bot.get_chat(target_id)
        full_name = user_info.full_name or str(target_id)
        username  = user_info.username or ""
    except Exception:
        full_name = str(target_id)
        username  = ""

    ok, err = await roles.add_owner(target_id, username, full_name, update.effective_user.id)
    if ok:
        await update.message.reply_text(
            f"<b>{CHECK} تمـت إضافـة {full_name} كمالـك ✅</b>",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(f"<b>{CROSS} {err}</b>", parse_mode="HTML")

async def cmd_removeowner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_owner(update):
        return

    if not context.args:
        await update.message.reply_text(
            "<b>الاستخـدام:</b> <code>/removeowner {user_id}</code>",
            parse_mode="HTML"
        )
        return

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("<b>❌ معـرف المستخـدم يجـب أن يكـون رقمـا</b>", parse_mode="HTML")
        return

    ok, err = await roles.remove_owner(target_id, update.effective_user.id)
    if ok:
        await update.message.reply_text(f"<b>{CHECK} تمـت إزالـة المالـك ✅</b>", parse_mode="HTML")
    else:
        await update.message.reply_text(f"<b>{CROSS} {err}</b>", parse_mode="HTML")

async def cmd_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_owner_or_manage_admin(update):
        return

    admins = await roles.get_admins()
    if not admins:
        await update.message.reply_text("<b>لا يوجـد مشرفـون مسجلـون</b>", parse_mode="HTML")
        return

    lines = [f"<b>{SHIELD} المشرفـون ({len(admins)}):</b>\n"]
    for a in admins:
        name  = a.get("full_name") or a.get("username") or str(a["user_id"])
        perms = a.get("permissions", {})
        active_perms = [k for k, v in perms.items() if v]
        perm_str = ", ".join(active_perms) if active_perms else "بـلا صلاحيـات"
        lines.append(f"<b>• {name}</b> — <code>{a['user_id']}</code>\n  <i>{perm_str}</i>")

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")

async def cmd_addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_owner_or_manage_admin(update):
        return

    if not context.args:
        await update.message.reply_text(
            "<b>الاستخـدام:</b> <code>/addadmin {user_id}</code>",
            parse_mode="HTML"
        )
        return

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("<b>❌ معـرف المستخـدم يجـب أن يكـون رقمـا</b>", parse_mode="HTML")
        return

    try:
        user_info = await context.bot.get_chat(target_id)
        full_name = user_info.full_name or str(target_id)
        username  = user_info.username or ""
    except Exception:
        full_name = str(target_id)
        username  = ""

    ok, err = await roles.add_admin(target_id, username, full_name,
                                     added_by=update.effective_user.id)
    if ok:
        await update.message.reply_text(
            f"<b>{CHECK} تمـت إضافـة {full_name} كمشرفـا ✅</b>\n\n"
            f"<blockquote><b>لتعديـل صلاحياتـه استخـدم /setperms {target_id}</b></blockquote>",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(f"<b>{CROSS} {err}</b>", parse_mode="HTML")

async def cmd_removeadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_owner_or_manage_admin(update):
        return

    if not context.args:
        await update.message.reply_text(
            "<b>الاستخـدام:</b> <code>/removeadmin {user_id}</code>",
            parse_mode="HTML"
        )
        return

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("<b>❌ معـرف المستخـدم يجـب أن يكـون رقمـا</b>", parse_mode="HTML")
        return

    ok, err = await roles.remove_admin(target_id)
    if ok:
        await update.message.reply_text(f"<b>{CHECK} تمـت إزالـة المشـرف ✅</b>", parse_mode="HTML")
    else:
        await update.message.reply_text(f"<b>{CROSS} {err}</b>", parse_mode="HTML")

async def cmd_setperms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_owner(update):
        return

    if not context.args:
        perms_list = "\n".join(f"  • <code>{p}</code>" for p in ALL_PERMISSIONS)
        await update.message.reply_text(
            f"<b>الاستخـدام:</b> <code>/setperms {{user_id}} {{perm}}=true/false ...</code>\n\n"
            f"<b>الصلاحيـات المتاحـة:</b>\n{perms_list}",
            parse_mode="HTML"
        )
        return

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("<b>❌ معـرف المستخـدم يجـب أن يكـون رقمـا</b>", parse_mode="HTML")
        return

    current_perms = await roles.db.get_admin_permissions(target_id)
    if not current_perms:
        current_perms = dict(DEFAULT_ADMIN_PERMISSIONS)

    for arg in context.args[1:]:
        if "=" in arg:
            key, val = arg.split("=", 1)
            key = key.strip()
            val = val.strip().lower() in ("true", "1", "yes", "نعم")
            if key in ALL_PERMISSIONS:
                current_perms[key] = val

    ok, err = await roles.update_admin_permissions(target_id, current_perms)
    if ok:
        active = [k for k, v in current_perms.items() if v]
        await update.message.reply_text(
            f"<b>{CHECK} تـم تحديـث الصلاحيـات ✅</b>\n\n"
            f"<b>الصلاحيـات النشطـة: {', '.join(active) or 'لا شيء'}</b>",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(f"<b>{CROSS} {err}</b>", parse_mode="HTML")

async def cmd_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    if not context.args:
        await update.message.reply_text(
            "<b>الاستخـدام:</b> <code>/panel {chat_id}</code>",
            parse_mode="HTML"
        )
        return

    try:
        chat_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("<b>❌ معـرف المجموعـة يجـب أن يكـون رقمـا</b>", parse_mode="HTML")
        return

    bot_me   = await context.bot.get_me()
    link     = f"https://t.me/{bot_me.username}?start=panel_{chat_id}"

    await update.message.reply_text(
        f"<b>⚙️ رابـط لوحـة التحكـم:</b>\n{link}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⚙️ فتـح لوحـة التحكـم", url=link)
        ]])
    )

async def cmd_devpanel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    if not await _require_owner(update):
        return

    from modules.devpanel.handler import show_dev_panel

    await show_dev_panel(update, context, update.effective_chat.id)
