
import os

BOT_TOKEN            = os.environ.get("BOT_TOKEN", "")
OPENROUTER_API_KEY   = os.environ.get("OPENROUTER_API_KEY", "")
WEBAPP_URL           = (
    os.environ.get("WEBAPP_URL", "")
    or os.environ.get("RENDER_EXTERNAL_URL", "")
    or f"https://{os.environ.get('REPLIT_DEV_DOMAIN', '')}"
).rstrip("/")
BOT_CHANNEL          = os.environ.get("BOT_CHANNEL", "")          
BOT_CHANNEL_URL      = os.environ.get("BOT_CHANNEL_URL", "")      

_oid = os.environ.get("OWNER_ID", "")
INITIAL_OWNER_ID: int | None = int(_oid) if _oid.lstrip("-").isdigit() else None

DB_PATH = "quran_bot.db"

MAX_OWNERS        = 2           
SURAHS_PER_PAGE   = 10          
AZKAR_QUOTE_LEN   = 200         

PERM_MANAGE_ADMINS  = "manage_admins"
PERM_USE_PANEL      = "use_panel"
PERM_SEND_AZKAR     = "send_azkar"
PERM_SEND_QURAN     = "send_quran"

ALL_PERMISSIONS = [
    PERM_MANAGE_ADMINS,
    PERM_USE_PANEL,
    PERM_SEND_AZKAR,
    PERM_SEND_QURAN,
]

DEFAULT_ADMIN_PERMISSIONS = {
    PERM_MANAGE_ADMINS: False,
    PERM_USE_PANEL:     True,
    PERM_SEND_AZKAR:    True,
    PERM_SEND_QURAN:    True,
}

PANEL_ACCESS_ALL_ADMINS = "all_admins"   
PANEL_ACCESS_SPECIFIC   = "specific"     
PANEL_ACCESS_OWNER_ONLY = "owner_only"   
