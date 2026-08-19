

from modules.quran_text.data import SURAHS  

RECITERS: dict[str, dict] = {
    "alaf": {
        "name_ar":  "مشاري راشد العفاسي",
        "edition":  "ar.alafasy",
        "emoji":    "🎙",
    },
    "sdis": {
        "name_ar":  "عبد الرحمن السديس",
        "edition":  "ar.abdurrahmanas-sudais",
        "emoji":    "🎙",
    },
    "hsr": {
        "name_ar":  "محمود خليل الحصري",
        "edition":  "ar.husary",
        "emoji":    "🎙",
    },
    "mnsw": {
        "name_ar":  "محمد صديق المنشاوي",
        "edition":  "ar.minshawi",
        "emoji":    "🎙",
    },
    "mahr": {
        "name_ar":  "ماهر المعيقلي",
        "edition":  "ar.mahermuaiqly",
        "emoji":    "🎙",
    },
    "nain": {
        "name_ar":  "أحمد نعينع",
        "edition":  "ar.ahmadnainai",
        "emoji":    "🎙",
        "base_url": "https://server11.mp3quran.net/ahmad_nu",
    },
    "said": {
        "name_ar":  "السيد سعيد",
        "edition":  None,
        "emoji":    "🎙",
        # الملفات مستضافة على JukeHost (CDN مجاني دائم)
        "base_url": "https://audio.jukehost.co.uk",
        "audio_dir": "said",
        "jh_urls": {
        '001': 'https://audio.jukehost.co.uk/01a01751-136b-739e-bd20-62e8599e7f0c',
        '002-001': 'https://audio.jukehost.co.uk/01a01751-fd45-720b-a52f-1bc0051ab01f',
        '002-002': 'https://audio.jukehost.co.uk/01a01752-37a1-7369-bed0-d138b4db0b64',
        '003-001': 'https://audio.jukehost.co.uk/01a01763-373e-72c7-bdbc-5fbe2c4b5f0e',
        '003-002': 'https://audio.jukehost.co.uk/01a01771-567c-71c0-a67c-639dc72ede2d',
        '004-001': 'https://audio.jukehost.co.uk/01a01764-d898-72f6-86fb-1a69e4c2a7c0',
        '005-001': 'https://audio.jukehost.co.uk/01a01764-eb9c-71e0-a045-b3e921123d62',
        '006-002': 'https://audio.jukehost.co.uk/01a01764-ff2c-73e1-9f54-c333fbabd72e',
        '012': 'https://audio.jukehost.co.uk/01a01771-5f31-7301-a8bc-8fde0cf0ef1c',
        '013-001': 'https://audio.jukehost.co.uk/01a01765-265f-707d-9103-a5117d1a41b0',
        '014-001': 'https://audio.jukehost.co.uk/01a01771-707d-7373-b0d3-d1e0b00d3b14',
        '016-001': 'https://audio.jukehost.co.uk/01a01771-7f7f-7349-b2ba-ff3e05d3acdb',
        '017-001': 'https://audio.jukehost.co.uk/01a01765-a3e0-7240-ad65-8ecc8b713e66',
        '018-001': 'https://audio.jukehost.co.uk/01a01765-9a49-7242-a6ed-fe3330f1033b',
        '019-001': 'https://audio.jukehost.co.uk/01a01771-89ae-739f-9e48-5b994a1e1724',
        '020-001': 'https://audio.jukehost.co.uk/01a01771-a9da-7167-afa2-ec762b1a91ef',
        '021-001': 'https://audio.jukehost.co.uk/01a01771-cd27-7140-b89a-47257019dcae',
        '023-001': 'https://audio.jukehost.co.uk/01a01771-c103-73a9-8253-23e6aaee2e82',
        '025-001': 'https://audio.jukehost.co.uk/01a01771-c7d3-7018-9f3f-e8c7a10ae007',
        '028-001': 'https://audio.jukehost.co.uk/01a01771-9755-7095-9c78-398310ada63a',
        '030-001': 'https://audio.jukehost.co.uk/01a01771-f34e-70d7-9c17-87d6ff469883',
        '030-002': 'https://audio.jukehost.co.uk/01a01781-afa2-7151-ac35-d116ba0de059',
        '031': 'https://audio.jukehost.co.uk/01a01772-10fd-7345-8419-9cf3e8713b34',
        '032': 'https://audio.jukehost.co.uk/01a01772-0913-73c0-8b80-ccb62addae68',
        '033-001': 'https://audio.jukehost.co.uk/01a01771-a652-719c-82d1-11178b406280',
        '035': 'https://audio.jukehost.co.uk/01a01772-2484-73c6-b291-50836cb9e297',
        '036-001': 'https://audio.jukehost.co.uk/01a01772-3b5e-72db-9a79-bdfc812bcb9d',
        '049': 'https://audio.jukehost.co.uk/01a01772-586c-72fa-8d54-40add442aaca',
        '050': 'https://audio.jukehost.co.uk/01a01776-11cc-71a5-a7a2-9dc429fd564f',
        '050-001': 'https://audio.jukehost.co.uk/01a01757-15e5-7082-a9f5-8023acc9b289',
        '054': 'https://audio.jukehost.co.uk/01a01776-2e30-717a-bf43-79388b9131aa',
        '055-001': 'https://audio.jukehost.co.uk/01a01776-2eb8-724f-8f08-56c12085fd4c',
        '059': 'https://audio.jukehost.co.uk/01a01776-43a9-72ba-a183-bae2ac44d2ba',
        '066': 'https://audio.jukehost.co.uk/01a01776-5501-7046-8281-989858f5e1bb',
        '069': 'https://audio.jukehost.co.uk/01a01776-5eae-73e1-b85a-dccc101301a7',
        '073': 'https://audio.jukehost.co.uk/01a01776-6d8e-7397-b94f-0fcad16f2c4c',
        '075': 'https://audio.jukehost.co.uk/01a01776-823e-72ea-a78c-5b49ebb2452c',
        '078-001': 'https://audio.jukehost.co.uk/01a01776-7ffb-73fa-8d11-16de881fcb39',
        '079': 'https://audio.jukehost.co.uk/01a01776-979a-7104-ac5c-bf72a5d31120',
        '082': 'https://audio.jukehost.co.uk/01a01776-9bce-7225-9fef-5c1a98621f92',
        '085': 'https://audio.jukehost.co.uk/01a01776-a771-71b4-824c-6b358d0ad88f',
        '086': 'https://audio.jukehost.co.uk/01a01776-b42b-7303-9fd5-d13e9db40fff',
        '087': 'https://audio.jukehost.co.uk/01a01776-c284-71cc-ba5e-3fcb62d6a48e',
        '088': 'https://audio.jukehost.co.uk/01a01776-ccac-70b7-a62e-c29539417322',
        '089': 'https://audio.jukehost.co.uk/01a01776-d70e-72b2-b3af-93e85577430a',
        '090': 'https://audio.jukehost.co.uk/01a01781-cac2-7010-951d-b4e5e081ec5b',
        '091': 'https://audio.jukehost.co.uk/01a01776-ed7b-73ce-a350-eabeae2fde6b',
        '093': 'https://audio.jukehost.co.uk/01a01776-f886-707d-b31d-c69e71a86975',
        '096': 'https://audio.jukehost.co.uk/01a01781-d7cb-73e8-8cbf-ffd6deb5e424',
        '097': 'https://audio.jukehost.co.uk/01a01777-123f-7093-bac9-1f738e981d14',
        '099': 'https://audio.jukehost.co.uk/01a01777-1de9-71bf-8840-381e1c759d1b',
        '106': 'https://audio.jukehost.co.uk/01a01777-2b80-732f-aae2-3655a19c7529',
        '108': 'https://audio.jukehost.co.uk/01a01781-e1c0-71d6-86b1-a54e93229d6a',
        },
        "full_surahs": [],
        "partial_surahs": [],
    },
    "mosad": {
        "name_ar":  "عبد الرحمن مسعد",
        "edition":  None,
        "emoji":    "🎙",
        # الملفات مستضافة على JukeHost (CDN مجاني دائم)
        "base_url": "https://audio.jukehost.co.uk",
        "audio_dir": "mosad",
        "jh_urls": {
        '002-001': 'https://audio.jukehost.co.uk/01a01713-7137-71f2-85ca-422f5210d08d',
        '002-002': 'https://audio.jukehost.co.uk/01a01713-8028-734a-a92d-e36ce83f43fa',
        '002-003': 'https://audio.jukehost.co.uk/01a01713-97e8-7008-ae38-fee44f60bd8e',
        '003-001': 'https://audio.jukehost.co.uk/01a01713-aa70-720b-8be5-c20fcf4e2868',
        '003-002': 'https://audio.jukehost.co.uk/01a01713-ba0b-722a-853b-01300973985f',
        '003-003': 'https://audio.jukehost.co.uk/01a01713-cf5b-73b0-a773-424cc65f4ece',
        '005-001': 'https://audio.jukehost.co.uk/01a01713-db83-7361-afed-c569dbaccf47',
        '007-001': 'https://audio.jukehost.co.uk/01a01713-e90e-7351-8562-e2bfcbd37c0e',
        '010': 'https://audio.jukehost.co.uk/01a01714-10ae-73e9-9b99-d641391f0c36',
        '010-001': 'https://audio.jukehost.co.uk/01a01713-fb01-70d4-92eb-878b00e2c0fc',
        '011': 'https://audio.jukehost.co.uk/01a01738-5556-7010-a5d2-3715b2d764fe',
        '013-001': 'https://audio.jukehost.co.uk/01a01715-7af1-731f-aa91-f4597f1fda19',
        '013-002': 'https://audio.jukehost.co.uk/01a01716-dac8-721f-a4c4-1a8173d0dbce',
        '013-003': 'https://audio.jukehost.co.uk/01a01718-3ad4-70de-bdcc-29a0537cf05a',
        '014-001': 'https://audio.jukehost.co.uk/01a01719-9b8c-73b0-a5bc-f0b1e62a54f5',
        '015': 'https://audio.jukehost.co.uk/01a01719-b4ac-71b1-8f38-6595c318704b',
        '016-001': 'https://audio.jukehost.co.uk/01a01719-cb3a-7158-a7f8-1ee76c67c334',
        '016-002': 'https://audio.jukehost.co.uk/01a01719-d1cc-7086-ae10-c0b05df769d5',
        '017': 'https://audio.jukehost.co.uk/01a0173c-9c28-7376-8a9a-318d855a8b98',
        '019-001': 'https://audio.jukehost.co.uk/01a0171c-9738-712e-9848-15096e0bcffa',
        '019-002': 'https://audio.jukehost.co.uk/01a0171c-a411-72aa-ba8e-8a8b7bdf1bae',
        '019-003': 'https://audio.jukehost.co.uk/01a0171c-ab69-70c3-aa76-528cd5d09116',
        '021-001': 'https://audio.jukehost.co.uk/01a0171e-19bb-72cc-8852-f2a56ebed847',
        '023-001': 'https://audio.jukehost.co.uk/01a0171e-3157-72d7-9999-948de87aca89',
        '024-001': 'https://audio.jukehost.co.uk/01a0171e-3b77-7323-8966-b13a3e956648',
        '025': 'https://audio.jukehost.co.uk/01a0171f-beef-72dd-a6dd-40ce66429b84',
        '025-001': 'https://audio.jukehost.co.uk/01a0171f-9e63-732f-b06f-1ddacc04e00c',
        '025-002': 'https://audio.jukehost.co.uk/01a0171f-af4d-71fd-8de0-a0a6f756c23c',
        '027-001': 'https://audio.jukehost.co.uk/01a0171f-cf4c-72df-bfbe-e60f535935c8',
        '029-001': 'https://audio.jukehost.co.uk/01a0171f-ddf0-7316-985f-3991f761ab8c',
        '029-002': 'https://audio.jukehost.co.uk/01a0171f-ea38-7126-a51a-90c687532e65',
        '030-001': 'https://audio.jukehost.co.uk/01a01721-4ab3-726d-8054-e1cda21d50e6',
        '032': 'https://audio.jukehost.co.uk/01a01722-af35-7349-9be4-c0d02109b68a',
        '049': 'https://audio.jukehost.co.uk/01a01722-c583-726d-9c33-051b37e5561f',
        '067': 'https://audio.jukehost.co.uk/01a01722-d766-7242-bafd-0a5bc00bb2d5',
        '073': 'https://audio.jukehost.co.uk/01a01722-e503-7247-abbe-21818a8d264e',
        '078': 'https://audio.jukehost.co.uk/01a01722-ec84-73a4-afc9-bd5230a62643',
        '087': 'https://audio.jukehost.co.uk/01a01722-f2fe-7071-9e7c-abfb0bccd037',
        '088': 'https://audio.jukehost.co.uk/01a01722-fb86-735a-97f7-3b732b74667f',
        '100': 'https://audio.jukehost.co.uk/01a01723-02cf-73ab-8eef-568549c908a0',
        '107': 'https://audio.jukehost.co.uk/01a01723-0a69-71f1-8a21-1808aa800535',
        '112': 'https://audio.jukehost.co.uk/01a01724-6b02-71f5-885c-9832d3471776',
        '113': 'https://audio.jukehost.co.uk/01a01725-cb18-70f8-b747-c3993221065f',
        '114': 'https://audio.jukehost.co.uk/01a01727-2b19-7334-802d-4961977d1a78',
        },
        "full_surahs": [],
        "partial_surahs": [],
    },
}

RECITER_KEYS = list(RECITERS.keys())

AUDIO_BASE = "https://cdn.islamic.network/quran/audio-surah/64"

def get_audio_url(reciter_key: str, surah_num: int) -> str:
    reciter = RECITERS[reciter_key]
    if reciter.get("base_url") == "__self_hosted__":
        # السيرفر المستضيف للمصوتات هو سيرفر الميني آب نفسه (لا مشكلة CORS)
        from config import WEBAPP_URL
        audio_dir = reciter.get("audio_dir", "saeed")
        # إن كانت السورة "ما تيسر" فقط، شغّل أول مقطع جزئي متاح لها
        if surah_num in reciter.get("partial_surahs", []) and surah_num not in reciter.get("full_surahs", []):
            audio_file = _first_partial_file(audio_dir, surah_num)
        else:
            audio_file = f"{surah_num:03d}.mp3"
        return f"{WEBAPP_URL}/audio/{audio_dir}/{audio_file}"
    # القراء ذوو روابط JukeHost المباشرة (j h_urls): رابط لكل ملف باسمه
    jh = reciter.get("jh_urls", {})
    if jh:
        num = f"{surah_num:03d}"
        # السورة الكاملة لها رابط باسمها المباشر (NNN)، الجزئية (ما تيسر) باسمها مع مقطع
        if num in jh:
            return jh[num]
        if f"{num}-001" in jh:
            return jh[f"{num}-001"]
        # السور الجزئية قد تكون بصيغة NNN-002 أو أخرى
        for i in range(1, 5):
            key = f"{num}-{i:03d}"
            if key in jh:
                return jh[key]
        raise KeyError(f"No JukeHost URL for {reciter_key}/{num}")
    if "base_url" in reciter:
        # السور الجزئية ("ما تيسر") تُشغَّل من أول مقطع لها NNN-001.mp3
        if surah_num in reciter.get("partial_surahs", []) and surah_num not in reciter.get("full_surahs", []):
            return f"{reciter['base_url']}/{surah_num:03d}-001.mp3"
        return f"{reciter['base_url']}/{surah_num:03d}.mp3"
    edition = reciter["edition"]
    return f"{AUDIO_BASE}/{edition}/{surah_num}.mp3"


def get_reciter_info(reciter_key: str) -> dict:
    """إرجاع معلومات القارئ (يدعم عرض قائمة السور المتاحة للقراء ذوي المصاحف الجزئية)."""
    return RECITERS.get(reciter_key, {})


def is_surah_available(reciter_key: str, surah_num: int) -> bool:
    """التحقق من توفر سورة معينة لقارئ (للقراء ذوي التلاوات المحدودة مثل السيد سعيد).
    السورة متوفرة إذا كانت كاملة أو جزئية (ما تيسر)."""
    reciter = RECITERS.get(reciter_key)
    if not reciter:
        return False
    # قراء JukeHost: السورة متوفرة إذا كان لها رابط مباشر في jh_urls
    jh = reciter.get("jh_urls", {})
    if jh:
        num = f"{surah_num:03d}"
        if num in jh or f"{num}-001" in jh:
            return True
        for i in range(1, 5):
            if f"{num}-{i:03d}" in jh:
                return True
        return False
    full = reciter.get("full_surahs")
    partial = reciter.get("partial_surahs", [])
    if full is not None:
        if surah_num in full:
            return True
        if surah_num in partial:
            return True
        return False
    return True


def is_surah_full(reciter_key: str, surah_num: int) -> bool:
    """هل السورة متوفرة كتلاوة كاملة (وليست ما تيسر فقط) لهذا القارئ؟"""
    reciter = RECITERS.get(reciter_key)
    if not reciter:
        return False
    jh = reciter.get("jh_urls", {})
    if jh:
        return f"{surah_num:03d}" in jh
    return surah_num in reciter.get("full_surahs", [])


import os
def _first_partial_file(audio_dir: str, surah_num: int) -> str:
    """إرجاع أول ملف جزئي متاح لسورة (NNN-001.mp3 ثم 002 وهكذا)."""
    audio_root = os.path.join(os.path.dirname(__file__), "..", "..", "webapp", "assets", "audio")
    d = os.path.join(audio_root, audio_dir)
    p = f"{surah_num:03d}-001.mp3"
    if os.path.exists(os.path.join(d, p)):
        return p
    # البحث عن أي مقطع جزئي بترتيب الرقم
    for i in range(1, 20):
        p = f"{surah_num:03d}-{i:03d}.mp3"
        if os.path.exists(os.path.join(d, p)):
            return p
    return f"{surah_num:03d}.mp3"
