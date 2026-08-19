

import re

def ce(emoji_id: str, fallback: str) -> str:
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

def plain(emoji: str) -> str:
    """إزالة غلاف tg-emoji لعرض الإيموجي العادي (مثل أزرار الكيبورد التي لا تدعم custom emoji)"""
    return re.sub(r'<tg-emoji emoji-id="[0-9]+">(.*?)</tg-emoji>', r'\1', emoji)

def extract_ce(emoji: str) -> str:
    """استخراج الإيموجي العادي (fallback) من غلاف tg-emoji"""
    m = re.search(r'<tg-emoji emoji-id="[0-9]+">(.*?)</tg-emoji>', emoji)
    return m.group(1) if m else emoji

def smart(emoji: str, is_premium: bool) -> str:
    """إرجاع الإيموجي المخصصة (custom) إذا كان المستخدم بريميوم، وإلا الإيموجي العادية"""
    return emoji if is_premium else plain(emoji)

LINE       = ce("5382360493161725288", "➖")
HIJAB      = ce("5861496736781964441", "🧕")
BOOK       = ce("5996966593777640829", "📖")
PRAY       = ce("5280780732745141885", "🙏")
GREEN_BOOK = ce("5888888221424685873", "📗")
BEADS      = ce("5996581850607261681", "📿")
FAQ        = ce("5431450689454750972", "❓")
QUESTION   = ce("5783013214539225637", "❔")
INFO       = ce("5224688446974475279", "ℹ️")
BACK       = ce("5960671702059848143", "⬅️")
ASK        = ce("5382187118216879236", "❓")
CLOCK      = ce("5258258882022612173", "⏲")
PEN        = ce("5852614525370503272", "📝")
PRAY2      = ce("5859341586617340244", "🤲")
FAQ2       = ce("5776056162088652694", "❓")
PRAY3      = ce("5289949229496671641", "🤲")
DOWN       = ce("5409210859169787977", "⬇️")
PC         = ce("5870692618244984670", "💻")
NUM1       = ce("5798796566516993587", "1⃣")
NUM2       = ce("5798643450932891251", "2⃣")
NUM3       = ce("5798439598900125383", "3⃣")
NUM4       = ce("5798618995389112011", "4⃣")
WAVE       = ce("5413554183502572090", "👋")

CROWN      = ce("5217437013170482788", "👑")
SHIELD     = "🛡"    
GEAR       = ce("5217617101149199744", "⚙️")
PLUS       = "➕"    
MINUS      = "➖"
CHECK      = ce("5217544005100794307", "✅")
CROSS      = ce("5210952531676504517", "❌")
LOCK       = "🔒"   
UNLOCK     = "🔓"   
PERSON     = "👤"   
PEOPLE     = ce("5258513401784573443", "👥")
STAR       = "⭐"

QURAN_AUDIO = ce("5463107823946717464", "🎵")
QURAN_TEXT  = ce("5859652353271009280", "📖")
AZKAR_ICON  = ce("6323343284609484532", "📿")
SCHEDULE    = ce("5413879192267805083", "🗓")
SEND        = ce("5445355530111437729", "📤")
MOSQUE      = "🕌"
SUN         = "🌅"
MOON        = "🌙"
SLEEP       = "😴"
WAKE        = "🌄"
AFTER_PRAY  = "🕌"
TASBIH      = ce("6323343284609484532", "📿")
SPEAKER     = "🔊"
RECITER     = "🎙"   
NEXT_PAGE   = "◀️"   
PREV_PAGE   = "▶️"   
HOME        = "🏠"   
SETTINGS    = "⚙️"
CHANNEL     = ce("5852471614628696454", "📢")
WARNING     = ce("5330250080161136767", "⚠️")
SUCCESS     = ce("5217544005100794307", "✅")
ERROR       = ce("5210952531676504517", "❌")
ARROW_RIGHT = "←"
TIMER       = ce("5382194935057372936", "⏱")

CLOCK2     = ce("5800903634522737987", "⏰")   
CALENDAR   = ce("5028418466000930064", "📅")   
SKIP       = ce("5323616095150566666", "⏭️")   
ID_ICON    = ce("5818885490065017876", "🆔")   
REPEAT     = ce("5226702984204797593", "🔄")   
PIN        = ce("5445300717738806281", "📍")   
BOOKS      = ce("5373098009640836781", "📚")   
CHAT       = ce("5443038326535759644", "💬")   
NUMBERS    = ce("5226513232549664618", "🔢")   
NO_ENTRY   = ce("5445350865776941647", "⛔")   

DIV = "━━━━━━━━━━━━━━━━━━━━"
DIV_SHORT = "──────────────"
