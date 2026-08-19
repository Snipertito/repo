
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ContextTypes

from modules.base          import BaseModule
from modules.azkar.data    import AZKAR_DATA, AZKAR_CATEGORY_KEYS
from modules.azkar.handler import send_azkar_to_chat
from modules.quran_text.handler import send_quran_text
from services.roles        import RolesService
from database              import Database
from utils.emojis          import HOME, CLOCK, GEAR, CROWN, SHIELD, SCHEDULE, DIV, PRAY2, BOOK, plain, smart

def emoji(emoji_str: str, update: Update) -> str:
    """إرجاع الإيموجي المخصصة إذا كان المستخدم يملك تليجرام بريميوم، وإلا الإيموجي العادية"""
    is_premium = bool(getattr(update.effective_user, "is_premium", False))
    return smart(emoji_str, is_premium)

logger = logging.getLogger(__name__)

# ثابت خاص يعبر عن لوحة المطور (ليست مرتبطة بمجموعة واحدة)
DEV_CB_PREFIX = "dv"

roles = RolesService()
db    = Database.get()

SURAHS_LIST = [
    (1, "الفاتحة"), (2, "البقرة"), (3, "آل عمران"), (4, "النساء"), (5, "المائدة"),
    (6, "الأنعام"), (7, "الأعراف"), (8, "الأنفال"), (9, "التوبة"), (10, "يونس"),
    (11, "هود"), (12, "يوسف"), (13, "الرعد"), (14, "إبراهيم"), (15, "الحجر"),
    (18, "الكهف"), (19, "مريم"), (20, "طه"), (21, "الأنبياء"), (24, "النور"),
    (25, "الفرقان"), (27, "النمل"), (28, "القصص"), (32, "السجدة"), (33, "الأحزاب"),
    (34, "سبأ"), (36, "يس"), (37, "الصافات"), (39, "الزمر"), (40, "غافر"),
    (41, "فصلت"), (42, "الشورى"), (44, "الدخان"), (46, "الأحقاف"), (48, "الفتح"),
    (50, "ق"), (51, "الذاريات"), (52, "الطور"), (53, "النجم"), (55, "الرحمن"),
    (56, "الواقعة"), (57, "الحديد"), (58, "المجادلة"), (59, "الحشر"), (60, "الممتحنة"),
    (66, "التحريم"), (67, "الملك"), (69, "الحاقة"), (70, "المعارج"), (71, "نوح"),
    (72, "الجن"), (73, "المزمل"), (74, "المدثر"), (75, "القيامة"), (76, "الإنسان"),
    (78, "النبأ"), (81, "التكوير"), (82, "الانفطار"), (83, "المطففين"), (84, "الانشقاق"),
    (85, "البروج"), (86, "الطارق"), (87, "الأعلى"), (88, "الغاشية"), (89, "الفجر"),
    (90, "البلد"), (91, "الشمس"), (92, "الليل"), (93, "الضحى"), (94, "الشرح"),
    (95, "التين"), (96, "العلق"), (97, "القدر"), (98, "البينة"), (99, "الزلزلة"),
    (100, "العاديات"), (101, "القارعة"), (102, "التكاثر"), (103, "العصر"), (104, "الهمزة"),
    (105, "الفيل"), (106, "قريش"), (107, "الماعون"), (108, "الكوثر"), (109, "الكافرون"),
    (110, "النصر"), (111, "المسد"), (112, "الإخلاص"), (113, "الفلق"), (114, "الناس"),
]

def dv(user_id: int, *parts: str) -> str:
    """بناء callback_data خاص بلوحة المطور (لا يعتمد على chat_id المجموعات)."""
    data = f"{DEV_CB_PREFIX}|{user_id}"
    if parts:
        data += "|" + "|".join(str(p) for p in parts)
    assert len(data.encode()) <= 64, f"callback_data طويل جدا: {data}"
    return data

async def _is_dev_access(update: Update, user_id: int) -> bool:
    """التحقق من أن المستخدم مالك البوت فقط."""
    if await roles.is_owner(user_id):
        return True
    await update.callback_query.answer(
        "⛔ لوحـة المطـور مخصصـة لـمـالـك البـوت فـقـط",
        show_alert=True
    )
    return False

async def show_dev_panel(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """الدخول الرئيسي للوحة المطور عبر /devpanel (يُستدعى من owner_cmds)."""
    user_id = update.effective_user.id
    await _show_dashboard(update, context, chat_id, user_id)

async def devpanel_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أزرار لوحة المطور (بادئة dv|)."""
    query  = update.callback_query
    await query.answer()
    data  = query.data or ""
    parts = data.split("|")

    if len(parts) < 2:
        return

    try:
        target_user_id = int(parts[1])
    except ValueError:
        await query.answer("❌ بيانات غير صالحة", show_alert=True)
        return

    user_id = update.effective_user.id
    if user_id != target_user_id:
        await query.answer("⛔ هـذه لوحـة مختصـة بغيـرك", show_alert=True)
        return

    if not await roles.is_owner(user_id):
        await query.answer("⛔ لوحـة المطـور مخصصـة لـمـالـك البـوت فـقـط", show_alert=True)
        return

    path = parts[2:]
    try:
        await _route(update, context, path)
    except Exception as e:
        logger.error(f"خطأ في لوحة المطور: {e}", exc_info=True)
        await query.answer("❌ حـدث خطـأ، حـاول مجـددا", show_alert=True)

async def _route(update: Update, context: ContextTypes.DEFAULT_TYPE, path: list[str]):
    query   = update.callback_query
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if not path or path[0] == "main":
        await _show_dashboard(update, context, chat_id, user_id)
        return

    section = path[0]
    rest    = path[1:]

    if section == "stats":
        await _show_stats(update, context, chat_id, user_id)
    elif section == "groups":
        if not rest:
            await _show_groups_list(update, context, chat_id, user_id)
        elif rest[0] == "sel" and len(rest) >= 2:
            await _select_group(update, context, chat_id, user_id, int(rest[1]))
    elif section == "azkar":
        if len(rest) == 1 and rest[0] in AZKAR_DATA:
            await _confirm_send_azkar(update, context, chat_id, user_id, rest[0])
        elif len(rest) == 2 and rest[0] == "send" and rest[1] in AZKAR_DATA:
            await _do_send_azkar(update, context, chat_id, user_id, rest[1])
        else:
            await _show_categories(update, context, chat_id, user_id)
    elif section == "quran":
        if len(rest) == 1 and rest[0].isdigit():
            await _confirm_send_quran(update, context, chat_id, user_id, int(rest[0]))
        elif len(rest) == 2 and rest[0] == "send" and rest[1].isdigit():
            await _do_send_quran(update, context, chat_id, user_id, int(rest[1]))
        else:
            await _show_quran_list(update, context, chat_id, user_id)
    elif section == "sched":
        if not rest:
            await _show_schedules(update, context, chat_id, user_id)
        elif len(rest) == 2 and rest[0] == "off":
            await _deactivate_schedule(update, context, chat_id, user_id, int(rest[1]))
    else:
        await _show_dashboard(update, context, chat_id, user_id)

async def _edit(query, text: str, keyboard):
    await query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------- 1. الواجهة الرئيسية (Dashboard) ----------

async def _show_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE,
                          chat_id: int, user_id: int):
    query = update.callback_query if update.callback_query else None
    now   = datetime.now().strftime("%d/%m/%Y %H:%M")
    _e = lambda s: emoji(s, update)  # إيموجي ذكية حسب تفعيل بريميوم المستخدم

    groups_count = 0
    schedules_count = 0
    admins_count = 0
    try:
        import aiosqlite
        async with aiosqlite.connect(db.path) as conn:
            async with conn.execute("SELECT COUNT(*) FROM group_settings") as cur:
                row = await cur.fetchone(); groups_count = row[0] if row else 0
            async with conn.execute("SELECT COUNT(*) FROM schedules WHERE is_active=1") as cur:
                row = await cur.fetchone(); schedules_count = row[0] if row else 0
        admins_count = len(await roles.get_admins())
    except Exception as e:
        logger.warning(f"فشل جلب الإحصائيات: {e}")

    text = (
        f"<b>{_e(GEAR)} لوحـة تحكـم المطـور 👨‍💻</b>\n\n"
        f"<blockquote><b>أهـلا يـا مطـور البـوت — اختـر القسـم</b></blockquote>\n\n"
        f"<b>⏰ الوقـت:</b> {now}\n"
        f"<b>👥 المجموعـات المسجلـة:</b> {groups_count}\n"
        f"<b>{_e(SCHEDULE)} الجـداول النشطـة:</b> {schedules_count}\n"
        f"<b>{_e(SHIELD)} المشرفـون:</b> {admins_count}\n\n"
        f"<b>الأقسـام:</b>"
    )

    keyboard = [
        [InlineKeyboardButton(f"📊 الإحصائيات التفصيلية",    callback_data=dv(user_id, "stats")),
         InlineKeyboardButton("👥 المجموعات",                callback_data=dv(user_id, "groups"))],
        [InlineKeyboardButton(f"{_e(PRAY2)} إرسـال الأذكـار",     callback_data=dv(user_id, "azkar")),
         InlineKeyboardButton(f"{_e(BOOK)} إرسـال القـرآن",       callback_data=dv(user_id, "quran"))],
        [InlineKeyboardButton(f"{_e(CLOCK)} الجداول المجدولة",     callback_data=dv(user_id, "sched"))],
    ]

    if query is None:
        # أول دخول عبر الأمر /devpanel
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await _edit(query, text, keyboard)

# ---------- 2. الإحصائيات ----------

async def _show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE,
                      chat_id: int, user_id: int):
    query = update.callback_query

    text_parts = ["<b>📊 الإحصائيات التفصيلية</b>\n"]

    # الملاك
    owners = await roles.get_owners()
    text_parts.append(f"<b>{CROWN} الملاكـون ({len(owners)}/{2}):</b>")
    for o in owners:
        name = o.get("full_name") or o.get("username") or str(o["user_id"])
        text_parts.append(f"  • {name} — <code>{o['user_id']}</code>")

    # المشرفون
    admins = await roles.get_admins()
    text_parts.append(f"\n<b>{SHIELD} المشرفـون ({len(admins)}):</b>")
    if admins:
        for a in admins:
            name = a.get("full_name") or a.get("username") or str(a["user_id"])
            text_parts.append(f"  • {name} — <code>{a['user_id']}</code>")
    else:
        text_parts.append("  <i>لا يوجد مشرفون حاليًا</i>")

    # المجموعات
    import aiosqlite
    try:
        async with aiosqlite.connect(db.path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("SELECT chat_id, chat_title, added_at FROM group_settings ORDER BY added_at DESC") as cur:
                rows = await cur.fetchall()
            async with conn.execute("SELECT COUNT(*) FROM schedules") as cur:
                row = await cur.fetchone(); total_sched = row[0] if row else 0
            async with conn.execute("SELECT COUNT(*) FROM schedules WHERE is_active=1") as cur:
                row = await cur.fetchone(); active_sched = row[0] if row else 0
        text_parts.append("<b>👥 المجموعـات ({}):</b>".format(len(rows)))
        if rows:
            for r in rows:
                title = (r["chat_title"] or "بدون اسم")[:30]
                added = (r["added_at"] or "")[:16]
                text_parts.append(f"  • {title} — <code>{r['chat_id']}</code> — {added}")
        else:
            text_parts.append("  <i>لا توجد مجموعات مسجلة بعد</i>")
        text_parts.append(f"\n<b>{plain(CLOCK)} الجـداول:</b> {active_sched} نشطـة مـن {total_sched} الكليـة")
    except Exception as e:
        logger.warning(f"خطأ في الإحصائيات: {e}")
        text_parts.append(f"\n<i>تعذر جلب بعض التفاصيل</i>")

    text = "\n".join(text_parts)
    keyboard = [[InlineKeyboardButton(f"{HOME} رجوع", callback_data=dv(user_id))]]
    await _edit(query, text, keyboard)

# ---------- 3. المجموعات ----------

async def _show_groups_list(update: Update, context: ContextTypes.DEFAULT_TYPE,
                            chat_id: int, user_id: int):
    import aiosqlite
    query = update.callback_query

    try:
        async with aiosqlite.connect(db.path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("SELECT chat_id, chat_title, added_at FROM group_settings ORDER BY added_at DESC") as cur:
                rows = await cur.fetchall()
    except Exception:
        rows = []

    if not rows:
        text = (
            "<b>👥 المجموعـات</b>\n\n"
            f"<blockquote><b>لا توجـد مجموعـات مسجلـة حاليـاً.\n"
            f"أضـف البـوت لأي مجموعـة وسيسجلها تلقائياً</b></blockquote>"
        )
        keyboard = [[InlineKeyboardButton(f"{HOME} رجوع", callback_data=dv(user_id))]]
        await _edit(query, text, keyboard)
        return

    text = (
        f"<b>👥 المجموعـات المسجلـة ({len(rows)})</b>\n\n"
        f"<blockquote><b>اختـر مجموعـة لإرسـال أذكـار أو قرآن فيهـا</b></blockquote>"
    )

    keyboard = []
    for r in rows[:15]:
        title = (r["chat_title"] or "بدون اسم")[:28]
        keyboard.append([InlineKeyboardButton(
            f"• {title}",
            callback_data=dv(user_id, "groups", "sel", str(r["chat_id"]))
        )])

    if len(rows) > 15:
        text += f"\n<i>... و{len(rows) - 15} مجموعة أخرى</i>"

    keyboard.append([InlineKeyboardButton(f"{HOME} رجوع", callback_data=dv(user_id))])
    await _edit(query, text, keyboard)

async def _select_group(update: Update, context: ContextTypes.DEFAULT_TYPE,
                        chat_id: int, user_id: int, group_id: int):
    query = update.callback_query

    try:
        grp = context.user_data.setdefault("devpanel", {})
        grp["group_id"] = group_id
    except Exception:
        pass

    try:
        chat = await context.bot.get_chat(group_id)
        name = chat.title or str(group_id)
        members = chat.get_members_count if False else None
        # get_chat_members_count متوفر في PTB
        try:
            count = await context.bot.get_chat_member_count(group_id)
        except Exception:
            count = None
    except Exception:
        name = str(group_id)
        count = None

    count_line = f"\n<b>👥 عدد الأعضاء:</b> {count}" if count else ""

    text = (
        "<b>👥 المجموعـة المختـارة</b>\n\n"
        f"<b>• الاسم:</b> {name}\n"
        f"<b>• المعرف:</b> <code>{group_id}</code>"
        f"{count_line}\n\n"
        f"<blockquote><b>اختـر مـا تريـد إرسالـه للمجموعـة</b></blockquote>"
    )

    keyboard = [
        [InlineKeyboardButton(f"{plain(PRAY2)} إرسـال أذكـار",    callback_data=dv(user_id, "azkar")),
         InlineKeyboardButton(f"{plain(BOOK)} إرسـال قرآن",       callback_data=dv(user_id, "quran"))],
        [InlineKeyboardButton("⬅️ قائمـة المجموعـات",       callback_data=dv(user_id, "groups")),
         InlineKeyboardButton(f"{HOME} رجوع",              callback_data=dv(user_id))],
    ]
    await _edit(query, text, keyboard)

# ---------- 4. الأذكار ----------

async def _show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE,
                           chat_id: int, user_id: int):
    query = update.callback_query

    text = (
        f"<b>{PRAY2} الأذكـار</b>\n\n"
        f"<blockquote><b>اختـر نـوع الذكـر لإرسالـه للمجموعـة المختارة</b></blockquote>"
    )

    keyboard = []
    for key in AZKAR_CATEGORY_KEYS:
        cat = AZKAR_DATA[key]
        keyboard.append([InlineKeyboardButton(
            f"{plain(cat['emoji'])} {cat['name']}",
            callback_data=dv(user_id, "azkar", key)
        )])
    keyboard.append([InlineKeyboardButton(f"{HOME} رجوع", callback_data=dv(user_id))])
    await _edit(query, text, keyboard)

async def _confirm_send_azkar(update: Update, context: ContextTypes.DEFAULT_TYPE,
                              chat_id: int, user_id: int, category: str):
    query = update.callback_query
    grp = context.user_data.get("devpanel", {})
    group_id = grp.get("group_id")

    cat = AZKAR_DATA.get(category)
    if not cat:
        await query.answer("❌ الفئـة غيـر موجـودة", show_alert=True)
        return

    if not group_id:
        text = (
            f"<b>{cat['emoji']} {cat['name']}</b>\n\n"
            "<b>⚠️ لم يتم اختيار مجموعة بعد.</b>\n\n"
            f"<blockquote><b>من قسم المجموعات: اختـر المجموعـة أولاً، ثـم عـد إلـى الأذكـار</b></blockquote>"
        )
        keyboard = [
            [InlineKeyboardButton("👥 اختـار مجموعـة", callback_data=dv(user_id, "groups")),
             InlineKeyboardButton(f"{plain(PRAY2)} الأذكـار",  callback_data=dv(user_id, "azkar"))],
            [InlineKeyboardButton(f"{HOME} رجوع",            callback_data=dv(user_id))],
        ]
        await _edit(query, text, keyboard)
        return

    try:
        chat = await context.bot.get_chat(group_id)
        name = chat.title or str(group_id)
    except Exception:
        name = str(group_id)

    zikr = cat["azkar"][0]
    text = (
        f"<b>{cat['emoji']} {cat['name']}</b>\n\n"
        f"<b>📍 المجموعـة:</b> {name} (<code>{group_id}</code>)\n\n"
        f"<b>مثـال علـى الذكـر:</b>\n"
        f"<blockquote><b>« {zikr['text'][:150]}{'...' if len(zikr['text']) > 150 else ''} »</b></blockquote>\n\n"
        f"<blockquote><b>هل تريد إرسال ذكر عشوائي الآن لهذه المجموعة؟</b></blockquote>"
    )

    keyboard = [
        [InlineKeyboardButton("📤 إرسـال الآن",    callback_data=dv(user_id, "azkar", "send", category)),
         InlineKeyboardButton(f"{plain(SCHEDULE)} جدولـة", callback_data=dv(user_id, "sched"))],
        [InlineKeyboardButton(f"{plain(PRAY2)} الأذكـار", callback_data=dv(user_id, "azkar")),
         InlineKeyboardButton(f"{HOME} رجوع",           callback_data=dv(user_id))],
    ]
    await _edit(query, text, keyboard)

async def _do_send_azkar(update: Update, context: ContextTypes.DEFAULT_TYPE,
                         chat_id: int, user_id: int, category: str):
    query = update.callback_query
    grp = context.user_data.get("devpanel", {})
    group_id = grp.get("group_id")
    # إذا لم تُختَر مجموعة: إرسال الذكر إلى محادثة المستخدم الحالية مباشرة
    target = group_id or chat_id
    try:
        await send_azkar_to_chat(context.bot, target, category)
        cat = AZKAR_DATA.get(category, {})
        await query.answer(f"✅ تـم الإرسـال — {cat.get('name', '')}", show_alert=True)
    except Exception as e:
        logger.error(f"فشل إرسال الأذكار من لوحة المطور: {e}")
        await query.answer("❌ فشـل الإرسـال، تأكـد مـن وجود البوت كمشرف في المجموعة", show_alert=True)

    await _confirm_send_azkar(update, context, chat_id, user_id, category)

# ---------- 5. القرآن ----------

async def _show_quran_list(update: Update, context: ContextTypes.DEFAULT_TYPE,
                           chat_id: int, user_id: int):
    query = update.callback_query

    text = (
        f"<b>{BOOK} القـرآن الكريـم (صفحة 1)</b>\n\n"
        f"<blockquote><b>اختـر سـورة لإرسالـها للمجموعـة المختارة</b></blockquote>"
    )

    keyboard = []
    half = len(SURAHS_LIST) // 2
    for i in range(half):
        n1, t1 = SURAHS_LIST[i]
        n2, t2 = SURAHS_LIST[i + half]
        keyboard.append([
            InlineKeyboardButton(f"{n1}. {t1}", callback_data=dv(user_id, "quran", str(n1))),
            InlineKeyboardButton(f"{n2}. {t2}", callback_data=dv(user_id, "quran", str(n2))),
        ])
    keyboard.append([InlineKeyboardButton(f"{HOME} رجوع", callback_data=dv(user_id))])
    await _edit(query, text, keyboard)

async def _confirm_send_quran(update: Update, context: ContextTypes.DEFAULT_TYPE,
                              chat_id: int, user_id: int, surah_num: int):
    query = update.callback_query
    grp = context.user_data.get("devpanel", {})
    group_id = grp.get("group_id")
    surah_name = dict(SURAHS_LIST).get(surah_num, f"سورة {surah_num}")
    # إذا لم تُختَر مجموعة: إرسال السورة إلى محادثة المستخدم الحالية مباشرة
    target = group_id or chat_id
    try:
        chat = await context.bot.get_chat(target)
        name = chat.title or str(target)
    except Exception:
        name = str(target)
    _e = lambda s: emoji(s, update)
    text = (
        f"<b>{_e(BOOK)} {surah_name}</b>\n\n"
        f"<b>📍 المجموعـة:</b> {name} (<code>{group_id}</code>)\n\n"
        f"<blockquote><b>هل تريد إرسال الصفحة الأولى من هذه السورة الآن؟</b></blockquote>"
    )
    keyboard = [
        [InlineKeyboardButton("📤 إرسـال الآن",    callback_data=dv(user_id, "quran", "send", str(surah_num))),
         InlineKeyboardButton(f"{_e(SCHEDULE)} جدولـة", callback_data=dv(user_id, "sched"))],
        [InlineKeyboardButton(f"{_e(BOOK)} السـور",     callback_data=dv(user_id, "quran")),
         InlineKeyboardButton(f"{HOME} رجوع",        callback_data=dv(user_id))],
    ]
    await _edit(query, text, keyboard)

async def _do_send_quran(update: Update, context: ContextTypes.DEFAULT_TYPE,
                         chat_id: int, user_id: int, surah_num: int):
    query = update.callback_query
    grp = context.user_data.get("devpanel", {})
    group_id = grp.get("group_id")
    # إذا لم تُختَر مجموعة: إرسال السورة إلى محادثة المستخدم الحالية مباشرة
    target = group_id or chat_id
    try:
        await send_quran_text(context.bot, target, surah_num)
        await query.answer(f"✅ تـم الإرسـال", show_alert=True)
    except Exception as e:
        logger.error(f"فشل إرسال القرآن من لوحة المطور: {e}")
        await query.answer("❌ فشـل الإرسـال، حـاول مجـددا", show_alert=True)

    await _confirm_send_quran(update, context, chat_id, user_id, surah_num)

# ---------- 6. الجداول المجدولة ----------

async def _show_schedules(update: Update, context: ContextTypes.DEFAULT_TYPE,
                          chat_id: int, user_id: int):
    import aiosqlite
    query = update.callback_query

    scheds = await db.get_active_schedules()

    if not scheds:
        text = (
            f"<b>{CLOCK} الجـداول المجدولـة</b>\n\n"
            f"<blockquote><b>لا توجـد جـداول نشطـة حاليـاً</b></blockquote>\n\n"
            f"<blockquote><b>مـن لوحـات المجموعـات: اختـر أذكـار أو قرآن ← جدولـة الإرسـال</b></blockquote>"
        )
        keyboard = [[InlineKeyboardButton(f"{HOME} رجوع", callback_data=dv(user_id))]]
        await _edit(query, text, keyboard)
        return

    text = (
        f"<b>{CLOCK} الجـداول النشطـة ({len(scheds)})</b>\n\n"
        f"<blockquote><b>يمكنـك إلغـاء أي جدول مـن هـنا</b></blockquote>"
    )

    keyboard = []
    for s in scheds[:10]:
        module_name = {
            "azkar": "أذكـار",
            "quran_text": "قـرآن",
            "quran_audio": "تلاوات",
            "permissions": "صلاحيات",
        }.get(s["module_key"], s["module_key"])

        category = ""
        if s["module_key"] == "azkar":
            cat = AZKAR_DATA.get(s["job_data"].get("category", ""), {})
            category = f" — {cat.get('emoji', '')} {cat.get('name', '')}"
        elif s["module_key"] == "quran_text":
            sn = s["job_data"].get("surah_num")
            if sn:
                category = f" — {dict(SURAHS_LIST).get(int(sn), f'سورة {sn}')}"

        mode = {
            "min": "كل دقيقة", "hr": "كل ساعة", "daily": "يومي",
            "weekly": "أسبوعي", "monthly": "شهري", "yearly": "سنوي",
        }.get(s["interval_type"], s["interval_type"])

        keyboard.append([InlineKeyboardButton(
            f"🗑 {module_name}{category} ({mode})",
            callback_data=dv(user_id, "sched", "off", str(s["id"]))
        )])

    if len(scheds) > 10:
        text += f"\n<i>... و{len(scheds) - 10} جدول آخر</i>"

    keyboard.append([InlineKeyboardButton(f"{HOME} رجوع", callback_data=dv(user_id))])
    await _edit(query, text, keyboard)

async def _deactivate_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE,
                               chat_id: int, user_id: int, schedule_id: int):
    query = update.callback_query
    try:
        await db.deactivate_schedule(schedule_id)
        try:
            from services.scheduler import SchedulerService
            scheduler = SchedulerService.get()
            await scheduler.cancel_schedule(schedule_id)
        except Exception as e:
            logger.warning(f"فشل إلغاء مهمة الجدول في Scheduler: {e}")
        await query.answer(f"✅ تـم إلغـاء الجدول ({schedule_id})", show_alert=True)
    except Exception as e:
        logger.error(f"فشل إلغاء الجدول: {e}")
        await query.answer("❌ فشـل إلغـاء الجدول", show_alert=True)
    await _show_schedules(update, context, chat_id, user_id)


# ---------- تسجيل الوحدة في Registry ----------

class DevPanelModule(BaseModule):
    """لوحة تحكم المطور (مالك البوت فقط)."""
    KEY     = "devpanel"
    NAME    = "لوحة المطور"
    EMOJI   = "👨‍💻"

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                              query, chat_id: int):
        # لا شيء هنا — أزرار لوحة المطور تُعالج عبر معالج الدفقات العام dv_callback_handler في bot.py
        return None

    async def execute_scheduled_job(self, bot: Bot, chat_id: int, job_data: dict):
        # لا توجد مهام مجدولة خاصة بلوحة المطور
        return
