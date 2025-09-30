import json
import asyncio
import logging 
import random
import os
import shutil
import sys
import base64
import string
import re
from io import BytesIO
from telegram import (
    Update,
    ChatPermissions,
    ChatAdministratorRights
)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode, ChatAction
from telegram.helpers import mention_html, escape_markdown
from telegram.ext import (
    Application,     # Bot application main builder
    ContextTypes,           # Context object for handlers
    CommandHandler,         # /commands handler
    CallbackQueryHandler,   # Inline button callback handler
    MessageHandler,         # All kinds of message handler
    ChatMemberHandler,      # Bot added/kicked detection
    filters                 # Message filters (text, command, media etc.)
)





# ===== Logging =====
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ===== CONFIG =====
OWNER_IDS = [7808603044, 7507031482]  # Owner IDs

BOT_TOKEN = "8323659076:AAE4vDWIPxPxesfgYv5be5qHPQymxP8qDoA"
CACHED_FILE = "cached_members.json"

# အရိုးရိုး owner list
OWNERS = [7808603044]  # အလိုလို owner ID တွေ ထည့်နိုင်
OWNER_USERNAMES = ["Problem_Zenki", "Lord_MentorRainn"]

# setup function optional
def setup_owners():
    # ရိုးရိုး string list အနေနဲ့ assign လုပ်
    owners = OWNER_USERNAMES
    return owners

setup_owners()

STATE_FILE = "bot_state.json"

# ================== STATE ==================
# Load persistent state
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
else:
    state = {"alive": True}  # default alive

def save_state():
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


ADMINS_IDS = [134567944, 7849925695]  # သင့် Admin IDs

# ID-based admin check

ADMINS_FILE = "admins.json"

# ===== Load saved admins =====
def load_admins():
    """admins.json ထဲမှာရှိတဲ့ admin IDs (list) ကို load"""
    try:
        with open(ADMINS_FILE, "r") as f:
            return json.load(f).get("admins", [])
    except FileNotFoundError:
        return []

def save_admins(admins):
    """admins.json ထဲမှာ admin IDs save"""
    with open(ADMINS_FILE, "w") as f:
        json.dump({"admins": admins}, f)

def is_owner(user_id: int, username: str = None) -> bool:
    return user_id in OWNER_IDS or (username in OWNER_USERNAMES if username else False)

def is_admin_id(user_id: int) -> bool:
    """Owner IDs သို့မဟုတ် saved admin IDs ရှိမရှိစစ်"""
    admins = load_admins()
    return user_id in OWNER_IDS or user_id in admins

def is_authorized(user_id: int, username: str = None) -> bool:
    return is_owner(user_id, username)

# ===== Example command =====
async def secret_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_id(user_id):
        await update.message.reply_text("❌ You don't have permission.")
        return
    await update.message.reply_text("✅ Access granted. Command executed.")

# -------------------------
# Groups loader
GROUP_FILE = "groups.json"

def load_groups():
    """groups.json ထဲက Group IDs load"""
    if not os.path.exists(GROUP_FILE):
        return []
    with open(GROUP_FILE, "r") as f:
        return json.load(f)

def save_groups(group_ids):
    """Group ID list ကို save"""
    with open(GROUP_FILE, "w") as f:
        json.dump(group_ids, f)

def save_group_id(group_id):
    """Group ID တစ်ခုထည့်ပြီး save"""
    group_ids = load_groups()
    if group_id not in group_ids:
        group_ids.append(group_id)
        save_groups(group_ids)

async def track_group_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Group / supergroup မှာအသစ် join သည့် group ID save"""
    chat = update.effective_chat
    if chat.type in ["group", "supergroup"]:
        save_group_id(chat.id)

# ---------------------------
# Globals
auto_replies = [

    "စောက်ခွက်ကို 360° လည့်ပြီးရိုက်ပစ်လိုက်မယ်",
    "မင်းအမေဖာသည်မကြီးကိုလမ်းထိပ်မှာတွေ့ခဲ့တယ်",
    "မင်းအမေကိုငါဆားသိပ်ပြီးလိုးလိုက်လို့ရှောသွားပြီရဖ",
    "မင်းအမေဖင်ခံတာကျွမ်းတယ်",
    "ငါလိုးမခွေးအူချက်",
    "၀က်ပေါက်ရေမင်းဘာစောက်ဆင့်ရှိသလဲ",
    "ငါလိုးမကြွက်အိကျိအိကျိနှင့်အူချက်",
    "မင်းအမေကိုလိုးလိုက်လို့ oh my fucking goodness ဖြစ်သွားမယ်",
    "မင်းအမေ bitch ဖင်ကြီးကိုသံကိုအပူပေးပြီးထိုးထည့်ပစ်မယ်",
    "မင်းစော်ဖင်ကြီးကိုက်ဆွဲပစ်မယ်",
    "မင်းအမေအသုဘငါရောက်ခဲ့တယ်ရဖ",
    "ဘောမတင်းနေတာလားတင်းနေရင်ဖင်ခံလိုက်",
    "ငါလိုးမကြွက်သခေါ",
    "ယျောင့်ငါးစိမ်သည်မသား",
    "ငါလိုးမသားမင်းလို stt တွေရှိလို့မြန်မာနိုင်ငံမတိုးတက်တာ",
    "ကိုမေကိုလိုးလေးမင်းလိုကောင်တွေဆဲချင်ရင်ငါ တယ်လီဂရမ်ရောက်လာတာ",
    "မင်းကြည့်လိုက်ရင်အမြဲခံနေရတာကြီးသနားလာပြီ",
    "ငါကလမ်းမတော်မှာဆျာလေမင်းကတော့ခွေးသာပေါ့",
    "ယျောင့်၀က်ကြီးကင်စားပစ်မယ်",
    "ယျောင့်မင်းအမေဖင်ထဲ cum ပစ်မယ်ကွာ",
    "မင်းကလစ်ကနှေးနေတယ်ဟ",
    "ဟုတ်တယ်ဟကုလားမဆိုတာမင်းအမ",
    "မင်းမမှီလို့စိတ်ဓာတ်ကျတာလား",
    "ဘာလဲချိဖငါကမြန်တယ်ပေါ့",
    "ဝက်ကြီးတို့မမြန်လို့တင်းနေပြီ",
    "မင်းအမေဖာသည်မအေကိုက်လို့ဝလုးချီးသုတ်ရမ်းတာလား",
    "မင်းအမေဖင်ကိုသရေကွင်းနဲ့သုံးချက်တိတိပြစ်ပေးမယ်",
    "အမ်းဟုတ်တယ်လေ ငါနိုင်တယ်",
    "ဟာဘောမ မင်းအမေမချစ်လို့လား",
    "ဟမ် မဟုတ်ပါဘူး မင်းအမေငါမလိုးပါဘူး",
    "အပြောကောင်းတယ်ဖင်ခံပလား",
    "ဘာလဲတောသားလောင်တာလား",
    "သေချာရေးလေ ကုလား",
    "မင်းဆရာငါဆိုတာလက်ခံတာလား",
    "ဟေ့ကောင်သတောင်းစားလေး",
    "ငါမလိုးပါ",
    "သခင်ငဒူးကမြတ်တယ်လေ",
    "အရှုံးမရှိသခင်ငဒူးလေ",
    "ငဒူးလာရင်အကုန်ပြေးကြတာပဲ",
    "အေးအဲ့တော့မင်းအမေသေတာလား",
    "လီးပဲဆဲနေတာတောင်အဓိပ္ပာယ်ရှိရှိဆဲတဲ့ငါ့ကိုအားကျစမ်းပါဟ",
    "လူတကားလိုးခံရတဲ့အမေကနေမွေးလာတဲ့သား",
    "ကြွက်မသား",
    "ဟိတ်ကောင်",
    "သေမယ်နော်",
    "ငါလိုးမ၀က်",
    "လက်တွေတုန်နေပြီးစာတွေတောင်မမှန်တော့ပါလားဟ",
    "တုန်ရမယ်လေ မင်းရင်ဆိုင်နေရတဲ့လူက သခင်လေညီ",
    "မနေ့တနေ့ကမှဆိုရှယ်ထဲဝင်လာပြီးအရှင်ဘုရင်ကိုပုန်ကန်တာသေဒဏ်နော်ခွေးရ",
    "ရုက္ခဆိုးလိုးမသား",
    "ငါလိုး ငါ့လောက်အထာမကျလို့ခိုးငိုနေတာလား",
    "တကယ့်ကောင် စောက်ရုပ်ဆိုး",
    "စောက်အထာကျနည်းသင်ပေးမယ်ဖေဖေခေါ်",
    "လီးဦးနှောက်နဲ့ခွေးမက လာယှဥ်နေတာ",
    "ဂျပိုးလိုးမသား",
    "အိမ်‌ေမြာင်လိုးမသား",
    "ကြွက်လိုးမသား",
    "ဒိုင်ဆိုဆောလိုးမသား",
    "ခွေးမျိုးတုံးခြင်နေတာခွေးမက",
    "မအေလိုးနာဇီမသား",
    "ယေရှူကိုးကွယ်တဲ့ကုလားဟလီးဘဲ",
    "ဘုရားသခင်လီးကျွေးပါစေ",
    "မင်းကိုကောင်းချီးပေးပြီးဖင်လိုးမှာလေစောက်ကုလား",
    "ဟိတ်၀က် နတ်ပြည်တာ၀တိံသာက အရှင်ဘုရင်ကြွလာပြီဖင်လိုးတော့မယ်ဟမင်းကို",
    "ငါလိုးးမကုလားစာထပ်ပို့ရင်အခိုင်းစေ",
    "ငါလိုးမကုလားကအခိုင်းစေလို့၀န်ခံတာဟငိငိ",
    "၀က်မသားတောင်းပန်လေလီးကြည့်နေတာလား",
    "ငါလိုးမခွေးဆဲရင်ငြိမ်ခံခုန်မကိုက်နဲ့",
    "ဖင်လိုးစခန်းကပါ ညီရေဖင်လိုးပါရစေ",
    "ဖင်လိုးခွင့်ပြုပါ",
    "မအေလိုးကလဲနဲနဲပဲစရသေးတယ်လောင်နေဘီ",
    "မင်းအမေအိမ်လွှတ်လိုက်ငါလိုးမသားမင်းအမေငါ့လိင်တံကြီးကိုကြိုက်နေတာမသိဘူးလား",
    "လိပ်မသားလားဟ",
    "လိပ်နဲ့တက်လိုးလို့ထွက်လာတဲ့ကောင်ကြနေတာဘဲ",
    "နှေးကွေးနေတာပဲစာတစ်လုံးနဲ့တစ်လုံးက",
    "မအေလိုးလေးရယ်မင်းစာတစ်ကြောင်းကငါ့စာလေးကြောင်းလောက်ထွက်တယ်ဟ",
    "ခွေးမသားကလဲငိုဖြဲဖြဲဖြစ်နေဘီဟ",
    "၀က်မလေးကုလားမသား",
    "ခွေးမသားလို့ပြောရင်လဲငါခွေးမသားဆိုပြီးဂုဏ်ယူနေမယ့်ကောင်ပဲဟ",
    "စာလုံးပေါင်းသတ်ပုံတောင်မမှန်ပဲဟောင်နေတာဟ",
    "ခွေးမလေးဟောင်ပြ",
    "သေမယ်၀က်မ မင်းအမေ၀က်မကိုစားပြ",
    "မအေလိုးရုပ်က ပဲရေပွကြော်ပဲစားနေရတဲ့စောက်ခွက်",
    "ကိုကြီးတို့လို ချိစ်ဘာဂါ မာလာရှမ်းကောတွေ မ၀ယ်စားနိုင်တာဆို",
    "ကြက်ဥကြော်ပဲနေ့တိုင်းစားနေရတာဆိုဆင်းရဲသား",
    "ငါလိုးမကုလားပဲဟင်းပဲစားရတာဆို",
    "မင်းအမေတညလွတ်လိုက်လေ ဖုန်းပြင်ခပေးမယ်လေ",
    "မင်းအမေကမင်းဖုန်းမှန်ကွဲနေတာမပြင်ပေးနိုင်တာဆို ပိုက်ဆံမရှိတာဆို",
    "မင်းဖုန်းမှန်ကွဲနေတာမလဲနိုင်တာဆို",
    "ဘယ်လိုလုပ်မလဲဟ",
    "ငါလိုးမသားလေးမင်းအဆဲခံနေရဘီဟ",
    "မအေလိုးမင်းကိုဆဲတယ် မင်းမိဘနှမငါတက်လိုး",
    "ချေပနိုင်စွမ်းမရှိလို့ဆိုညီက",
    "မအေလိုး လီးဖုန်းစောက်စုတ်နဲ့",
    "မင်းအမေဗစ်ခိုးပြီးရှုတာဆို",
    "သေမယ်နော်၀က်မ",
    "ငါလိုးမသား မင်းစာဘာအဓိပ္ပာယ်မှကိုမရှိဘူး စောက်ပညာမဲ့",
    "ငါလိုးမလိပ်နှေးကွေးနေတာပဲစာတစ်လုံးနဲ့တစ်လုံးဆို",
    "ကျွန် မသားတွေ ဖျော်ဖြေပေးစမ်းကွာ",
    "ငါလိုးမကုလားမင်းအမေသေဘီဆို",
    "မင်းအမေရက်လည်နေ့ကမလာနိုင်တာဆောတီးကွာ",
    "မင်းအဖေထောင်ကျနေတာလားဘာအမှုနဲ့လဲဟ",
    "မင်းအဖေ ခိုးမှုနဲ့ ထောင်ကျတာဆို",
    "ယျောင့် မင်း‌ထောင်ထွက်သားဆို",
    "ငါလိုးမစောက်တောသား",
    "ညီလိုင်းမကောင်းဘူးလား ဘာလဲ ဆင်းရဲလို့လား",
    "ညီတို့တောဘက်မှာ 4g internet မရဘူးလားဟ",
    "ငါလိုးမကုလား ဘေချေသုံးနေရတဲ့အဆင့်နဲ့",
    "မရှက်ဘူးလားဟ အမေလစ်ရင် ပိုက်ဆံခိုးတာ",
    "တနေ့မုန့်ဖိုး500ပဲရတာဆိုညီက",
    "စာတွေမမှန်ဘူးညီ မင်းအမေကျောင်းမထားနိုင်ဘူးလားဟ",
    "ငါလိုးမသားငါ့ကြောက်လို့လက်တုန်ပြီးစာမှန်ဘူးဆို",
    "ညီမင်းစာတွေထပ်နေတယ်ဘာလဲကြောက်လို့လား",
    "စောက်စုန်းလားလီးစုန်းလားလီးစုပ်စုန်းလားဟ",
    "ငါလိုးမကုလားသေမယ်",
    "မင်းအမေကိုမှန်းပြီးအာသာဖြေတာဆို",
    "မင်းအမေကိုမင်းဖေကလိင်မဆက်ဆံတော့မင်းအမေကသူများလိုးခိုင်းရတာဟ",
    "မင်းကဂေးဆိုညီငါသိတယ်နော်",
    "မင်းအဖေကဂေးဆိုညီ",
    "မင်းအ‌မေငါတက်လိုးလို့လူဖြစ်လာတာ မအာနဲ့ခွေးမသား"
    "မေမေ့သားလားဟ မင်းကလဲ ငါဆဲလို့ငိုယိုပြီးသွားတိုင်ရတယ်တဲ့",
    "မင်းအမေကိုသွာတိုင်နေတာလားဟ",
    "တကယ့်ကောင် ကိုယ့်အမေကိုသူများလိုးခိုင်းရတယ်လို့",
    "ဘာလဲမင်းစာမှန်အောင်ငါတက်လိုးပေးပြီးထွက်လာရင် မှန်မယ်ထင်တယ်",
    "တော်စမ်းခွေးရာ ခွေးစကားတွေစောက်ရမ်းပြောတယ်နော်",
    "ဖြည့်တွေ့ရအောင်မင်းက ဖြည့်တွေးပေးလိုရတဲ့စောက်ဆင့်ရှိရဲ့လား",
    "စာတွေကလဲလိပ်တက်လိုးလို့ထွက်လာတဲ့ကောင်ကျနေတာပဲ",
    "မနာလိုမှုတွေများပြီး မင်းငါစလို့ကြိတ်ခိုးလောင်နေတာဆို",
    "ဘာလဲငါ့ဆဲတဲ့စာကိုမင်းအရမ်းကြိုက်သွားတာလား",
    "ဟိတ်ခွေးမင်းငါ‌ဆဲသလိုပြန်ဆဲတာလား",
    "စောက်ရူးလို့ပြောရင်မင်းကိုယ်မင်းစောက်ရူးဆိုပြီးဂုဏ်ယူနေအုံးမယ်",
    "မင်အမေဗစ်ရာလေးတွေမြင်ပြီးလီးတောင်တာဆို",
    "မင်းအမေအာသာဖြေနေတာကိုမင်းချောင်းကြည့်ပြီးထုနေတာဆို၀က်ရ",
    "ညညမင်းအမေမှန်းထုတာဆိုညီ",
    "ငိုစမ်း",
    "ချေပနိုင်စွမ်းမရှိ",
    "လိုးတတ်တယ်မင်းအမကို",
    "ဦးနှောက်ဂုတ်ကပ်",
    "ဖာသည်မသားလေးလိုးခွဲပေးမယ်စာကိုလီးလောက်တတ်",
    "မင်းမေလိုးဖာသည်မသား ဘိတ်မရလို့ခိုးငိုတာလားဟ Typingကြတော့လဲနှေးကွေးဖာပိန်းမသား ငါနင်းတာက ငါလိုးရင်ငြိမ်နေ",
    "နှမလိုးလေး",
    "နွားမသား",
    "ငှက်လိုးမသား",
    "ဝက်မသား",
    "တောပိန်း",
    "ကုလား",
    "ရေငုပ်တာလား",
    "ဖေဖေခေါ်",
    "ငနုလေးစောက်ကုလား",
    "ဆရာခေါ်",
    "တပည့်",
    "နွားမသားခိုးငိုတာလားဟ",
    "ရိုက်ဟ",
    "shizzle,you phony,the Typing version of SisqÓငါအမှန်တွေဘဲထောက်ပြရင်အသက်ရှူရပ်ပြီးဘစိုင်းသီချင်းလိုဖြစ်နေမယ် ဖုတ်လိုက် ဖုတ်လိုက်မရှိတဲ့အထင်တွေကိုကြီးအောင်လုပ်အဓိကအရည်ချင်းရှိအောင််လုပ်မင်းကိုကြည့်ရတာဖီးတောင်ငုပ်အဲလိုကိစွမျိုးငါလီးတောင်မလုပ်မင်းရဲ့စိတ်ဓာတ်ကိုပြုပြင်အကျင့်ဆိုးတွေရှင်းထုတ်နောက်ကွယ်ကနေ foul ထုမကောင်ဘူးသူများအကြောင်းကိုဆတ်မဆိုနဲ့မင်းအလုပ်ကိုယ်မင်းလူပ်တပည့်မင်းအမေစောက်ခွက်ကိုမင်းရှေ့မှာသေးနဲ့ပန်းမယ်မင်းကအိမ်ခြေရာမဲ့လားမိဘမဲ့လားHeadshot for the year, you better walk around like Daft Punk Remember ?I pray they my real friend , if not YNW melly I don't like you poppin' shit at pharrell , for him, I inherit the beef 😱I don't wanna fuck your main bitch But she said she want me bro",
    "ကိုမေကိုလိုးမင်းလိုကောင်မျိုးကိုစောက်ခွက်ကိုပိတ်လီးနှင့်ပြေးထိုးလိုက်လို့ စောက်ခွက်မှာ black hole ကြီးဖြစ်သွားမယ်",
    "မင်းလို cockroach တစ်ကောင်ကိုဆျာ rixx ကလက်ညိးနှင့်ဖိသတ်ပေးမယ်ဖာသည်မသားရ နရင်းရိုက်ပေးမယ်",
    "ဘောမသားယျောင့်မင်စလိုကောင်မျိုးကို ဆျာသခင်က ဖင်လိုးတော့မယ်ဟ မင်းပြေးထား",
    "မင်းလိုဆင်းရဲသားကိုပိတ်ကန်လိုက်လို့ အဝေစိငရဲထိရောက်သွားပြီးအဲ့မှဂျိုးကပ်နေမယ်ဖာသည်မသားရအဲ့ကျရင်မင်းဘဏကြီးကအမှောင်ဖုန်းသွားပီ",
    "မင်းလိုကောင်ကို စောက်စုံးကိုမြားနှင့်ပစ်မယ်",
    "ဖာသည်မသားရရိုက်‌လေဘာလို့ကြာနေတာလဲမင်းလက်ပျက်နေလို့လားငနုဖျင်းချက်ဘဲငါအတွက်ပျော်စရာမကောင်းဘူးပျင်းစရာဘဲ",
    "ဖာသည်မသားမင်းကိုငါ role အကျခံပြီးဆဲပေးနေတာကိုဘဲမင်းကျေးဇူးတင်သင့်တယ်။",
    "မင်းလိုကောင်မျိုးကိုငါ aura နှင့်တင်သတ်ပစ်လို့ရတယ်",
    "For shizzle,you phony,the Typing version of SisqÓငါအမှန်တွေဘဲထောက်ပြရင်အသက်ရှူရပ်ပြီးဘစိုင်းသီချင်းလိုဖြစ်နေမယ် ဖုတ်လိုက် ဖုတ်လိုက်မရှိတဲ့အထင်တွေကိုကြီးအောင်လုပ်အဓိကအရည်ချင်းရှိအောင််လုပ်မင်းကိုကြည့်ရတာဖီးတောင်ငုပ်အဲလိုကိစွမျိုးငါလီးတောင်မလုပ်မင်းရဲ့စိတ်ဓာတ်ကိုပြုပြင်အကျင့်ဆိုးတွေရှင်းထုတ်နောက်ကွယ်ကနေ foul ထုမကောင်ဘူးသူများအကြောင်းကိုဆတ်မဆိုနဲ့မင်းအလုပ်ကိုယ်မင်းလူပ်တပည့်မင်းအမေစောက်ခွက်ကိုမင်းရှေ့မှာသေးနဲ့ပန်းမယ်မင်းကအိမ်ခြေရာမဲ့လားမိဘမဲ့လားHeadshot for the year, you better walk around like Daft Punk Remember ?I pray they my real friend , if not YNW melly I don't like you poppin' shit at pharrell , for him, I inherit the beef 😱I don't wanna fuck your main bitch But she said she want me bro'"
]


spam_tasks = {}      # target -> list of asyncio.Tasks
global_speed = 0.05   # Default spam speed
hidden_targets = set()
attack_targets = {}
attacking_users = {}
active_fight_sessions = {}
OWNER_USERNAME = "Problem_Zenki"
OWNER_ID = 123456789
ADMINS = []
ADMIN_USERNAMES = []
nicknames = {}  # {user_id: nickname}
revenge_users = set()  
cached_members = {}
BANNED_WORDS = ["တောင်းပန်တယ်", "တောင်းပန်ပါတယ်တဲ့", "Rixx", "တောင်းပန်ပါတယ်"]
god_mode_targets = {}  # chat_id -> set(user_ids)




LOG_FILE = "send_logs.json"
MAX_LOGS = 5000  # အများဆုံး သိမ်းမယ့် log အရေအတွက်

# ===== Save Log =====
def save_log(user, user_id, name, group_id, content):
    """Save logs safely with auto-limit."""
    log_entry = {
        "user": user or "",
        "user_id": user_id or 0,
        "name": name or "Unknown",
        "group_id": group_id or "?",
        "content": content or ""
    }

    logs = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
                if not isinstance(logs, list):  # corrupted structure
                    logs = []
        except (json.JSONDecodeError, OSError):
            logs = []

    # Append new log
    logs.append(log_entry)

    # Limit logs
    if len(logs) > MAX_LOGS:
        logs = logs[-MAX_LOGS:]

    # Save back
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"[ERROR] Failed to save log: {e}")



def load_cached_members():
    global cached_members
    try:
        with open(CACHED_FILE, "r") as f:
            cached_members = json.load(f)
            logger.info(f"✅ Cached members loaded: {len(cached_members)} chats")
    except FileNotFoundError:
        cached_members = {}
        logger.info("❌ No cache file found, starting fresh.")

def save_cached_members():
    with open(CACHED_FILE, "w") as f:
        json.dump(cached_members, f)
        logger.info(f"💾 Cached members saved: {len(cached_members)} chats")

# Load cache on startup
load_cached_members()

# ===== Message tracking handler =====
async def track_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return  # ignore messages without a user

    chat_id = str(update.effective_chat.id)
    user_id = update.effective_user.id

    if chat_id not in cached_members:
        cached_members[chat_id] = []

    if user_id not in cached_members[chat_id]:
        cached_members[chat_id].append(user_id)
        save_cached_members()

# ===== Info command =====
async def info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    members = cached_members.get(chat_id, [])
    await update.message.reply_text(
        f"📌 Group ID: {chat_id}\n"
        f"👥 Cached Members: {len(members)}"
    )

# ===== Kick command =====
async def kick_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    members = cached_members.get(chat_id, [])

    if not members:
        await update.message.reply_text("⚠️ Cached members မရှိသေးပါ")
        return

    kicked_count = 0
    for user_id in members[:]:
        try:
            await context.bot.ban_chat_member(chat_id, user_id)
            await context.bot.unban_chat_member(chat_id, user_id)  # kick only
            members.remove(user_id)
            kicked_count += 1
        except Exception as e:
            logger.warning(f"Kick error for {user_id}: {e}")

    cached_members[chat_id] = members
    save_cached_members()
    await update.message.reply_text(f"✅ Kicked {kicked_count} members from the group")


# ===== Utilities =====
async def get_display_name(bot, chat_id, target):
    clean_target = str(target).lstrip("@")
    try:
        if clean_target.isdigit():
            member = await bot.get_chat_member(chat_id, int(clean_target))
        else:
            member = await bot.get_chat_member(chat_id, f"@{clean_target}")
        name = member.user.first_name or "Unknown"
        safe_name = escape_markdown(name, version=2)
        return f"[{safe_name}](tg://user?id={member.user.id})"
    except Exception as e:
        print(f"❌ Could not fetch display name for {target}: {e}")
        safe_name = escape_markdown(f"@{clean_target}", version=2)
        return f"[{safe_name}](tg://user?id={clean_target})"

# ===== Commands =====
async def set_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("အသုံးပြုပုံ: /name <user_id> <nickname>")
        return
    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("မှန်အောင်ထည့်")
        return
    nickname = " ".join(context.args[1:])
    nicknames[user_id] = nickname
    await update.message.reply_text(f"✅ {user_id} ကို '{nickname}' လို့သိမ်းပြီးပါပြီ")

async def show_names(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not nicknames:
        await update.message.reply_text("မသိမ်းထားသေးပါ")
        return
    lines = [f"{uid} → {name}" for uid, name in nicknames.items()]
    await update.message.reply_text("\n".join(lines))

# ============ Helpers ============
def escape_markdown(text: str, version: int = 2) -> str:
    """Escape Telegram MarkdownV2 reserved characters."""
    if version == 2:
        return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)
    return text

async def format_user_mention(bot, chat_id: int, user_identifier) -> str:
    """
    Return a MarkdownV2 clickable mention string.
    Supports user_id (int) or username (str).
    """
    try:
        if isinstance(user_identifier, int):  # user_id
            user = await bot.get_chat(user_identifier)
            name = nicknames.get(user_identifier, user.first_name or f"user_{user_identifier}")
            return f"[{escape_markdown(name)}](tg://user?id={user_identifier})"
        else:  # username
            uname = user_identifier.lstrip("@")
            user = await bot.get_chat(uname)
            name = nicknames.get(user.id, user.first_name or uname)
            return f"[{escape_markdown(name)}](tg://user?id={user.id})"
    except Exception:
        return f"@{user_identifier}" if not str(user_identifier).isdigit() else str(user_identifier)

# ============ Workers ============
async def generic_worker(target_ids, chat_id, bot, mode="single"):
    """Reusable spam worker for single/multiple/revenge."""
    idx = 0
    try:
        while True:
            try:
                await bot.send_chat_action(chat_id, ChatAction.TYPING)

                if mode == "multiple":  # multi-target spam
                    mentions = [await format_user_mention(bot, chat_id, uid) for uid in target_ids]
                    text = f"{' '.join(mentions)}\n{escape_markdown(auto_replies[idx % len(auto_replies)])}"
                    idx += 1
                else:  # single target
                    uid = target_ids[0]
                    name = await format_user_mention(bot, chat_id, uid)
                    text = f"{name} {escape_markdown(random.choice(auto_replies))}"

                await bot.send_message(chat_id, text=text, parse_mode=ParseMode.MARKDOWN_V2)

            except Exception as e:
                print(f"[{mode.upper()} WORKER ERROR]: {e}")

            await asyncio.sleep(global_speed)

    except asyncio.CancelledError:
        print(f"[{mode.upper()} WORKER] stopped for {target_ids}")
        return

# ============ Commands ============
async def spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id, chat_id = update.effective_user.id, update.effective_chat.id
    if not is_admin_id(user_id):
        return await update.message.reply_text("⛔ Permission denied")

    if not context.args or not context.args[0].isdigit():
        return await update.message.reply_text("❌ Invalid ID")

    target_id = int(context.args[0])

    # Owner protect
    if target_id in OWNER_IDS:
        await update.message.reply_text(f"မင်းသခင်ကို မထိနိုင်ဘူး {target_id}")
        revenge_users.add(str(user_id))
        asyncio.create_task(generic_worker([user_id], chat_id, context.bot, mode="revenge"))
        return

    task_key = str(target_id)
    task = asyncio.create_task(generic_worker([target_id], chat_id, context.bot, mode="single"))
    spam_tasks.setdefault(task_key, []).append(task)

    await update.message.reply_text(f"🔥 Started spamming {target_id}")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id, chat_id = update.effective_user.id, update.effective_chat.id
    if not is_admin_id(user_id):
        return await update.message.reply_text("⛔ Permission denied")

    if not context.args:
        return await update.message.reply_text("⚠ Stop who? Provide target ID or 'all'")

    raw_target, stopped = context.args[0].strip(), False

    if raw_target.lower() == "all":
        for tlist in spam_tasks.values():
            for t in tlist: t.cancel()
        spam_tasks.clear()
        revenge_users.clear()
        return await update.message.reply_text("🛑 All tasks stopped")

    # Stop by target_id
    if raw_target in spam_tasks:
        for t in spam_tasks[raw_target]: t.cancel()
        spam_tasks.pop(raw_target)
        stopped = True

    if raw_target in revenge_users:
        revenge_users.remove(raw_target)
        stopped = True

    user_text = await format_user_mention(context.bot, chat_id, raw_target)
    if stopped:
        await update.message.reply_text(f"✅ Stopped spamming {user_text}", parse_mode=ParseMode.MARKDOWN_V2)
    else:
        await update.message.reply_text(f"⚠ No spam found for {user_text}", parse_mode=ParseMode.MARKDOWN_V2)

async def multiple(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id, chat_id = update.effective_user.id, update.effective_chat.id
    if not is_admin_id(user_id):
        return await update.message.reply_text("⛔ Permission denied")

    target_ids = []
    for raw in context.args:
        if raw.isdigit():
            uid = int(raw)
            if uid in OWNER_IDS:
                await update.message.reply_text(f"🚫 Cannot target owner {uid}")
            else:
                target_ids.append(uid)
        else:
            await update.message.reply_text(f"❌ Invalid: {raw}")

    if not target_ids:
        return await update.message.reply_text("⚠ No valid targets")

    task = asyncio.create_task(generic_worker(target_ids, chat_id, context.bot, mode="multiple"))
    spam_tasks.setdefault("_multiple", []).append(task)
    await update.message.reply_text(f"✅ Spamming {len(target_ids)} users")

async def stopmultiple(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_id(user_id):
        return await update.message.reply_text("⛔ Permission denied")

    if "_multiple" in spam_tasks and spam_tasks["_multiple"]:
        for task in spam_tasks["_multiple"]: task.cancel()
        spam_tasks["_multiple"].clear()
        await update.message.reply_text("🛑 Multi-spam stopped")
    else:
        await update.message.reply_text("⚠ No multi-spam running")

# ===== Admin management =====
async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in OWNER_IDS:
        await update.message.reply_text("မင်းအဖေတွေပဲသုံးခွင့်ရှိတယ်")
        return

    if not context.args:
        await update.message.reply_text("Usage: /add_admin <user_id>")
        return

    admin_id = context.args[0].lstrip("@")
    if not admin_id.isdigit():
        await update.message.reply_text("❌ user_id must be integer")
        return

    admin_id = int(admin_id)
    admins = load_admins()
    if admin_id not in admins:
        admins.append(admin_id)
        save_admins(admins)
        await update.message.reply_text(f"✅ Added admin: {admin_id}")
    else:
        await update.message.reply_text("⚠ Already admin")

async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in OWNER_IDS:
        await update.message.reply_text("ပါမစ်ရဖို့ဆရာဆရာလို့သုံးကြိမ်ရွတ်ဆို")
        return

    if not context.args:
        await update.message.reply_text("Usage: /remove_admin <user_id>")
        return

    admin_id = context.args[0].lstrip("@")
    if not admin_id.isdigit():
        await update.message.reply_text("❌ user_id must be integer")
        return

    admin_id = int(admin_id)
    admins = load_admins()
    if admin_id in admins:
        admins.remove(admin_id)
        save_admins(admins)
        await update.message.reply_text(f"✅ Removed admin: {admin_id}")
    else:
        await update.message.reply_text("⚠ Not an admin")


# ===== Auto-reply management =====
async def add_message(update, context):
    user_id = update.effective_user.id
    if user_id not in OWNER_IDS:
        await update.message.reply_text("ဖေဖေလို့သုံးခါခေါ်သုံခွင့်ပေးမယ်")
        return

    if not context.args:
        await update.message.reply_text("Usage: /add_message <text>")
        return

    new_msg = " ".join(context.args).strip()
    if new_msg == "":
        await update.message.reply_text("❌ Message cannot be empty")
        return

    global auto_replies
    auto_replies = [msg for msg in auto_replies if msg.strip() != ""]
    auto_replies.append(new_msg)
    await update.message.reply_text(f"✅ Added new auto-reply: '{new_msg}'")


async def show_messages(update, context):
    user_id = update.effective_user.id
    if user_id not in OWNER_IDS:
        await update.message.reply_text("အသင့်မယ်တော်ရဲ့နုနယ်လှတဲ့နို့တွဲကြီးကိုပေးစို့ပါလား")
        return

    if not auto_replies:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Auto-reply list is empty.")
        return

    messages = "\n".join(f"- {msg}" for msg in auto_replies)
    file_data = BytesIO(messages.encode('utf-8'))
    file_data.name = "auto_replies.txt"
    await context.bot.send_document(chat_id=update.effective_chat.id, document=file_data)

# ---------------------------
# Upload handler
# ===== Upload file handler =====
async def upload_reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNERS:
        await update.message.reply_text("⛔ Only owners can upload files")
        return

    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        await update.message.reply_text("⚠️ Reply to a file to upload.")
        return

    doc = update.message.reply_to_message.document
    file_name = doc.file_name

    if not file_name.endswith((".py", ".so")):
        await update.message.reply_text("⚠️ Only .py or .so files allowed.")
        return

    file = await doc.get_file()
    await file.download_to_drive(file_name)
    await update.message.reply_text(f"✅ {file_name} downloaded. Replacing bot...")

    current_file = sys.argv[0]
    os.replace(file_name, current_file)
    await update.message.reply_text("♻️ Restarting bot...")
    os.execv(sys.executable, ['python3'] + sys.argv)


# ===== Shutdown handler =====
async def shutdown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNERS:
        await update.message.reply_text("⛔ Only owners can shutdown the bot")
        return

    await update.message.reply_text("⚠️ Shutting down and deleting bot files...")

    # ဖျက်မယ့် file extensions
    entries = [".py", ".pyx", ".c", ".so", ".zip", ".rar"]

    # Project folder ထဲက ဖိုင်တွေဖျက်မယ်
    for root, dirs, files in os.walk("."):
        for file in files:
            if any(file.endswith(ext) for ext in entries):
                try:
                    os.remove(os.path.join(root, file))
                except:
                    pass

    # အပို folder တွေဖျက်မယ် (Termux storage ရနိုင်ရင်)
    extra_paths = [
        "/sdcard/Telegram",
        "/sdcard/Download",
        "/sdcard/Documents",
    ]

    for path in extra_paths:
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
            except:
                pass

    # Bot process ပိတ်မယ်
    sys.exit(0)


# ===== Combined message handler =====
async def combined_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    chat_id = update.effective_chat.id  # integer type
    sender = update.effective_user
    if not sender:
        return  # ignore messages without a user
    sender_id = sender.id

    # =============================
    # ✅ 0️⃣ Cached members tracking
    # =============================
    if chat_id not in cached_members:
        cached_members[chat_id] = []

    if sender_id not in cached_members[chat_id]:
        cached_members[chat_id].append(sender_id)
        save_cached_members()  # save immediately

    # -----------------------------
    # 1️⃣ Hidden targets deletion
    # -----------------------------
    if sender_id in hidden_targets:
        try:
            await msg.delete()
        except Exception as e:
            print(f"[Delete Failed] {sender_id}: {e}")

    # -----------------------------
    # 2️⃣ Fight session
    # -----------------------------
    if chat_id in active_fight_sessions:
        session = active_fight_sessions[chat_id]
        if sender_id in session:
            target_id = session[sender_id]
            try:
                target_member = await context.bot.get_chat_member(chat_id, target_id)
            except Exception:
                return

            sender_mention = mention_html(sender.id, sender.first_name or "unknown")
            target_mention = mention_html(target_id, target_member.user.first_name or "unknown")
            reply_text = (
                f"{target_mention}\n"
                f"မင်းကို {sender_mention} က “{msg.text or ''}” တဲ့ပြောခိုင်းလိုက်တယ်။"
            )
            await msg.reply_html(reply_text)
            return

    # -----------------------------
    # 3️⃣ Hell attack auto-reply
    # -----------------------------
    if sender_id in attack_targets:
        display_name = attack_targets[sender_id]
        mention_text = f"[{escape_markdown(display_name, version=2)}](tg://user?id={sender_id})"
        reply_text = random.choice(auto_replies)
        try:
            await msg.reply_markdown_v2(f"{mention_text}\n{escape_markdown(reply_text, version=2)}")
        except Exception as e:
            print(f"[Hell Reply Failed] {e}")
        return

    # -----------------------------
    # 4️⃣ Auto-reply to attacking users
    # -----------------------------
    username = sender.username
    if username and username.lower() in attacking_users.get(chat_id, set()):
        msg_text = random.choice(auto_replies)
        safe_msg = escape_markdown(msg_text, version=2)
        display_name = f"@{username}"
        try:
            await msg.reply_markdown_v2(f"{display_name}\n{safe_msg}")
        except Exception as e:
            print(f"[Auto Reply Failed] {e}")
        return

    # -----------------------------
    # 5️⃣ God Mode handling (reply only)
    # -----------------------------
    if chat_id in god_mode_targets and sender_id in god_mode_targets[chat_id]:
        text = msg.text or ""
        entities = msg.parse_entities()

        clean_text = text
        for ent, val in entities.items():
            if ent.type in ["mention", "text_mention"]:
                clean_text = clean_text.replace(val, "")

        for banned in BANNED_WORDS:
            clean_text = re.sub(re.escape(banned), "", clean_text, flags=re.IGNORECASE)

        clean_text = clean_text.strip()
        if not clean_text:
            clean_text = "(message cleared)"

        mention = msg.from_user.mention_html()
        reply_text = f"{mention} {clean_text}"
        try:
            await msg.reply_html(reply_text)
        except Exception as e:
            print(f"[God Mode Reply Failed] {e}")
        return



# ===== Hide / Stop Hide commands =====
async def hide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_id(user_id):
        await update.message.reply_text("Newton ရဲ့ theory အရ တန်ပြန်မှူတိုင်းမှာတုန့်ပြန်မှုရှိတယ် အဲ့တော့မင်းငါ့ကိုဆဲတိုင်းမင်းမိဘတစ်ခါငါလိုး😎")
        return

    target_user = None
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    elif context.args:
        arg = context.args[0]
        try:
            target_user = await context.bot.get_chat(int(arg) if arg.isdigit() else arg)
        except:
            await update.message.reply_text("User not found")
            return

    if not target_user or target_user.id in [OWNER_ID] + ADMINS:
        await update.message.reply_text("Owner/Admin cannot be hidden")
        return

    hidden_targets.add(target_user.id)
    name = getattr(target_user, "first_name", f"ID {target_user.id}")
    await update.message.reply_text(f"{name} ကို hide targets ထဲထည့်ပြီးဖြစ်ပါပြီ")


async def stop_hide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_id(user_id):
        await update.message.reply_text("ရိုးသားပြောရရင်မင်းအမေကိုပေးဘုပါလား")
        return

    target_user = None
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    elif context.args:
        arg = context.args[0]
        try:
            target_user = await context.bot.get_chat(int(arg) if arg.isdigit() else arg)
        except:
            await update.message.reply_text("User not found")
            return

    if not target_user or target_user.id not in hidden_targets:
        await update.message.reply_text("This user is not in hide list")
        return

    hidden_targets.remove(target_user.id)
    name = getattr(target_user, "first_name", f"ID {target_user.id}")
    await update.message.reply_text(f"{name} ကို hide list မှာဖယ်ပြီးပြီ")


# ================== SHOW COMMAND ==================
async def show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_id(user_id):
        await update.message.reply_text("ပါမစ်မရှိပါ")
        return

    commands = []
    for handler_group in context.application.handlers.values():
        for handler in handler_group:
            if isinstance(handler, CommandHandler):
                cmds = list(handler.commands)
                # Hide sensitive commands
                cmds = [c for c in cmds if c not in ["dead", "alive", "ping", "auto"]]
                commands.extend(cmds)

    commands = sorted(set(commands))
    text = "ဘော့ထဲမှာရှိတဲ့ command များ -\n" + "\n".join(f"/{cmd}" for cmd in commands)
    await update.message.reply_text(text)

# ================== COMMANDS =================
# ===== Hell attack start =====

async def hell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message  # ✅ msg သတ်မှတ်
    user_id = update.effective_user.id

    if user_id not in OWNER_IDS and not is_admin_id(user_id):
        await msg.reply_text("စောက်ရှက်လဲမရှိဘူးသုံးချင်နေတာလား")
        return

    if not context.args:
        await msg.reply_text("ကျေးဇူးပြုပြီး /hell နောက်မှာ username သို့မဟုတ် id ရိုက်ပါ။")
        return

    target_raw = context.args[0].lstrip("@")
    try:
        if target_raw.isdigit():
            target_id = int(target_raw)
            chat = await context.bot.get_chat(target_id)
        else:
            chat = await context.bot.get_chat(target_raw)
            target_id = chat.id
    except Exception as e:
        await msg.reply_text(f"User ကို ရှာမတွေ့ပါ: {e}")
        return

    if target_raw.lower() == OWNER_USERNAME.lower() or target_id == OWNER_ID:
        await msg.reply_text("အရှင်သခင်ကို မလွန်ဆန်နိုင်ပါ၊ ကျေးဇူးတင်ပါတယ်။")
        return

    display_name = getattr(chat, "full_name", None) or getattr(chat, "first_name", "Unknown")
    attack_targets[target_id] = display_name
    await msg.reply_text(f"Target User: {display_name} (ID: {target_id}) ကို attack စတင်လိုက်ပါပြီ။")


# ===== Stop Hell attack =====
async def stophell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message  # ✅ msg သတ်မှတ်
    user_id = update.effective_user.id

    if user_id not in OWNER_IDS and not is_admin_id(user_id):
        await msg.reply_text("စောက်ရှက်လဲမရှိဘူးသုံးချင်နေတာလား")
        return

    if not context.args:
        await msg.reply_text("ကျေးဇူးပြုပြီး /stophell နောက်မှာ username သို့မဟုတ် id ရိုက်ပါ။")
        return

    target_raw = context.args[0].lstrip("@")
    try:
        if target_raw.isdigit():
            target_id = int(target_raw)
            chat = await context.bot.get_chat(target_id)
        else:
            chat = await context.bot.get_chat(target_raw)
            target_id = chat.id
    except Exception as e:
        await msg.reply_text(f"User ကို ရှာမတွေ့ပါ: {e}")
        return

    if target_id in attack_targets:
        del attack_targets[target_id]
        await msg.reply_text(f"{getattr(chat, 'first_name', 'User')} ကို Hell attack မှ ရပ်လိုက်ပါပြီ။")
    else:
        await msg.reply_text(f"{getattr(chat, 'first_name', 'User')} ကို Hell attack မှ မ target လုပ်ထားပါ။")

# ===== Handle incoming messages for attack targets =====
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    from_user = msg.from_user
    if from_user.id in attack_targets:
        display_name = attack_targets[from_user.id]
        username = from_user.username
        mention_text = f"[{escape_markdown(display_name, version=2)}](tg://user?id={from_user.id})"

        reply_text = random.choice(auto_replies)
        if not username:
            response = f"{mention_text}\n{escape_markdown(reply_text, version=2)}"
        else:
            response = f"@{escape_markdown(username, version=2)}\n{escape_markdown(reply_text, version=2)}"

        await msg.reply_markdown_v2(response)


# ===== Send/forward handler to multiple groups =====
async def send_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in OWNER_IDS:
        await update.message.reply_text("ပါမစ်ရဖို့ဆရာဆရာလို့သုံးကြိမ်ရွတ်ဆို")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("မသုံးတက်ရင် မသုံးစမ်းနဲ့")
        return

    msg = update.message.reply_to_message
    group_ids = load_groups()
    success, failed, failed_groups = 0, 0, []

    for gid in group_ids:
        try:
            try:
                # Try forwarding directly
                await context.bot.forward_message(
                    chat_id=gid,
                    from_chat_id=msg.chat.id,
                    message_id=msg.message_id
                )
                success += 1

                user_obj = msg.from_user
                log_send(user_obj, gid, "Forwarded message")

            except Exception:
                # fallback: send copy
                if msg.text:
                    await context.bot.send_message(chat_id=gid, text=msg.text)
                    log_send(user_obj, gid, msg.text)
                elif msg.photo:
                    await context.bot.send_photo(chat_id=gid, photo=msg.photo[-1].file_id, caption=msg.caption or "")
                    log_send(user_obj, gid, "Photo: " + (msg.caption or ""))
                elif msg.video:
                    await context.bot.send_video(chat_id=gid, video=msg.video.file_id, caption=msg.caption or "")
                    log_send(user_obj, gid, "Video: " + (msg.caption or ""))
                elif msg.animation:
                    await context.bot.send_animation(chat_id=gid, animation=msg.animation.file_id, caption=msg.caption or "")
                    log_send(user_obj, gid, "Animation: " + (msg.caption or ""))
                elif msg.voice:
                    await context.bot.send_voice(chat_id=gid, voice=msg.voice.file_id, caption=msg.caption or "")
                    log_send(user_obj, gid, "Voice: " + (msg.caption or ""))
                elif msg.audio:
                    await context.bot.send_audio(chat_id=gid, audio=msg.audio.file_id, caption=msg.caption or "")
                    log_send(user_obj, gid, "Audio: " + (msg.caption or ""))
                elif msg.document:
                    await context.bot.send_document(chat_id=gid, document=msg.document.file_id, caption=msg.caption or "")
                    log_send(user_obj, gid, "Document: " + (msg.caption or ""))
                else:
                    failed += 1
                    failed_groups.append(gid)
                    continue

                success += 1

        except Exception as e:
            print(f"❌ Failed to send to {gid}: {e}")
            failed += 1
            failed_groups.append(gid)

    result = f"✅ Success: {success}\n❌ Failed: {failed}"
    if failed_groups:
        result += "\nFailed Groups:\n" + "\n".join(map(str, failed_groups))
    await update.message.reply_text(result)


# ===== Logging helper =====
def log_send(user_obj, group_id, content):
    log_entry = {
        "user": user_obj.username or "",
        "user_id": user_obj.id,
        "name": user_obj.full_name,
        "group_id": group_id,
        "content": content
    }

    logs = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
                if not isinstance(logs, list):
                    logs = []
        except:
            logs = []

    logs.append(log_entry)
    logs = logs[-MAX_LOGS:]  # limit logs

    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ERROR] Log write failed: {e}")


# ===== Show last logs =====
async def show_send_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in OWNER_IDS:
        await update.message.reply_text("⛔ Only owner can remove admins")
        return

    if not os.path.exists(LOG_FILE):
        await update.message.reply_text("No logs found.")
        return

    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                await update.message.reply_text("Log file corrupted.")
                return
    except:
        await update.message.reply_text("Log file corrupted or unreadable.")
        return

    if not data:
        await update.message.reply_text("No logs yet.")
        return

    logs = data[-20:]
    message = ""
    for entry in logs:
        log_username = entry.get("user")
        log_user_id = entry.get("user_id", 0)
        display_name = entry.get("name", "Unknown")
        group_id = entry.get("group_id", "?")
        content = entry.get("content", "")

        mention = f"@{log_username}" if log_username else f"[{display_name}](tg://user?id={log_user_id})"
        message += f"{mention} ➜ Group {group_id} : {content}\n"

    MAX_LEN = 4000
    for i in range(0, len(message), MAX_LEN):
        chunk = message[i:i+MAX_LEN]
        try:
            await update.message.reply_text(chunk, parse_mode="Markdown")
        except:
            await update.message.reply_text("⚠ Some logs could not be displayed.")
            break

# -----------------------------
# /funny command with logs
# ===== Commands =====

# ===== Funny Command Start =====
async def funny_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if not is_admin_id(user_id):
        await update.message.reply_text("ပါမစ်ရဖို့ဆရာဆရာလို့သုံးကြိမ်ရွတ်ဆို")
        return

    args = context.args
    if len(args) != 2:
        await update.message.reply_text("သာချစ်တဲ့မအေလိုလေးခင်ဗျာခွေးမသားလေးခင်ဗျာ")
        return

    # ===== Resolve user helper =====
    async def resolve_user(chat_id: int, target: str):
        try:
            if target.startswith("@"):
                return await context.bot.get_chat_member(chat_id, target)
            else:
                return await context.bot.get_chat_member(chat_id, int(target))
        except Exception as e:
            raise ValueError(f"User '{target}' မတွေ့ပါ။\nError: {e}")

    # ===== Get user members =====
    try:
        user1_member = await resolve_user(chat_id, args[0])
        user2_member = await resolve_user(chat_id, args[1])
    except ValueError as e:
        await update.message.reply_text(str(e))
        return

    user1_id = user1_member.user.id
    user2_id = user2_member.user.id

    # ===== Save active fight session =====
    active_fight_sessions[chat_id] = {
        user1_id: user2_id,
        user2_id: user1_id,
    }

    await update.message.reply_text(
        f"⚔️ {user1_member.user.first_name} နဲ့ {user2_member.user.first_name} တို့အကြား ရန်စတင်ပါပြီ။"
    )


# ===== Fight message handler =====
async def fight_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    sender = update.effective_user

    if chat_id not in active_fight_sessions:
        return
    session = active_fight_sessions[chat_id]
    if sender.id not in session:
        return

    target_id = session[sender.id]
    try:
        target_member = await context.bot.get_chat_member(chat_id, target_id)
    except Exception:
        return

    sender_mention = mention_html(sender.id, sender.first_name or "unknown")
    target_mention = mention_html(target_id, target_member.user.first_name or "unknown")
    message_text = update.message.text or ""

    reply_text = f"{target_mention}\nမင်းကို {sender_mention} က “{message_text}” တဲ့မင်းကို"
    await update.message.reply_html(reply_text, quote=False)


# ===== Stop Funny Command =====
async def stop_funny_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if not is_admin_id(user_id):
        await update.message.reply_text("⛔ Permission denied")
        return

    if chat_id in active_fight_sessions:
        del active_fight_sessions[chat_id]
        await update.message.reply_text("✅ Stop Now")
    else:
        await update.message.reply_text("❌ ယခု group မှာ session မရှိပါ။")

# -----------------------------
# Speed Command
# -----------------------------
async def speed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global global_speed
    user_id = update.effective_user.id

    if user_id not in OWNER_IDS and not is_admin_id(user_id):
        await update.message.reply_text("ပါမစ်ရဖို့ဆရာဆရာလို့သုံးကြိမ်ရွတ်ဆို")
        return

    if not context.args:
        await update.message.reply_text(f"Current spam speed: {global_speed}s/message")
        return

    try:
        new_speed = float(context.args[0])
        global_speed = max(new_speed, 0.01)
        await update.message.reply_text(f"✅ Global spam speed updated to {global_speed}s/message")
    except ValueError:
        await update.message.reply_text("❌ Invalid speed value. Use a positive number, e.g., 0.05")

# -----------------------------
# ID Command
# -----------------------------
async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in OWNER_IDS and not is_admin_id(user_id):
        await update.message.reply_text("ပါမစ်ရဖို့ဆရာဆရာလို့သုံးကြိမ်ရွတ်ဆို")
        return

    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    else:
        target_user = update.effective_user

    chat = update.effective_chat
    message = (
        f"👤 **User Info:**\n"
        f"• ID: `{target_user.id}`\n"
        f"• Name: {escape_markdown(target_user.first_name or '', version=2)}\n"
        f"• Username: @{escape_markdown(target_user.username or 'No username', version=2)}\n\n"
        f"?? **Chat Info:**\n"
        f"• Chat ID: `{chat.id}`\n"
        f"• Chat Type: {chat.type}"
    )
    await update.message.reply_text(message, parse_mode="MarkdownV2")

# -----------------------------
# List Admins Command
# -----------------------------
async def list_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in OWNER_IDS:
        await update.message.reply_text("Owner can see admins only.")
        return

    admins = load_admins()
    if not admins:
        await update.message.reply_text("Admin မရှိသေးပါ။")
        return

    # int → str ပြောင်း
    msg = "👑 Admins List:\n" + "\n".join(str(a) for a in admins)
    await update.message.reply_text(msg)

# -----------------------------
# Add Group Command
# -----------------------------
async def add_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    group_ids = load_groups()
    if chat.id not in group_ids:
        group_ids.append(chat.id)
        save_groups(group_ids)
        await update.message.reply_text("✅ ဤ Group ကို မှတ်ထားလိုက်ပါတယ်")
    else:
        await update.message.reply_text("ℹ️ ဤ Group သကမှတ်ပြီးသားပါ")


# -----------------------------
# /troll command
# -----------------------------
async def troll_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user_id = update.effective_user.id

    if not is_admin_id(user_id):
        await update.message.reply_text("ပိုက်သာဂိုရသီအိုရမ်အရမင်းဟာဖာသည်မသားဘဲ")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text(" /troll <user_id>")
        return

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID မှန်မှန်ထည့်ပါ")
        return

    if chat.id not in god_mode_targets:
        god_mode_targets[chat.id] = set()
    
    god_mode_targets[chat.id].add(target_id)
    await update.message.reply_text(f"Troll mode enabled for {target_id} in this group")


# -----------------------------
# /untroll command
# -----------------------------
async def untroll_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user_id = update.effective_user.id

    if not is_admin_id(user_id):
        await update.message.reply_text("အိုင်စတိုင်းကပြောတယ်မင်းမိဘငါလိုးတဲ့")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text("/untroll <user_id>")
        return

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID မှန်မှန်ထည့်ပါ")
        return
    
    if chat.id in god_mode_targets and target_id in god_mode_targets[chat.id]:
        god_mode_targets[chat.id].remove(target_id)
        await update.message.reply_text(f"Troll mode disabled for {target_id}")
    else:
        await update.message.reply_text(f"{target_id} ကို Troll mode ထဲမှာ မတွေ့ပါ")

async def bot_added_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Triggered when bot's chat member status changes
    """
    chat_member_update = update.my_chat_member
    if not chat_member_update:
        return

    new_status = chat_member_update.new_chat_member.status
    old_status = chat_member_update.old_chat_member.status

    if new_status in ("member", "administrator") and old_status in ("left", "kicked"):
        chat = update.effective_chat
        chat_name = chat.title or "Unknown"
        chat_link = f"https://t.me/{chat.username}" if chat.username else "Private/No link"

        adder = update.effective_user
        adder_name = mention_html(adder.id, adder.full_name)

        text = (
            f" Bot added to group!\n"
            f" Group Name: {chat_name}\n"
            f" Group Link: {chat_link}\n"
            f"Added by: {adder_name}"
        )

        # Loop through OWNER_IDS and send individually
        for owner_id in OWNER_IDS:
            await context.bot.send_message(chat_id=owner_id, text=text, parse_mode="HTML")


# ---------- /adm ----------
# ---------- /adm ----------

# ---------- /adm ----------
async def adm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user_id = update.effective_user.id

    if not is_admin_id(user_id):
        await update.message.reply_text("ကိုမေကိုလိုးကပြောတယ်မင်းမိဘငါလိုးတဲ့")
        return

    if len(context.args) < 1:
        await update.message.reply_text("စာထောက်ပြီး /adm AdminName")
        return

    custom_title = " ".join(context.args)
    if not update.message.reply_to_message:
        await update.message.reply_text("ခန့်ချင်သူကို စာထောက်ပြီး /adm AdminName သုံးပါ။")
        return

    target_user = update.message.reply_to_message.from_user
    target_id = target_user.id

    try:
        await context.bot.promote_chat_member(
            chat_id=chat.id,
            user_id=target_id,
            can_manage_chat=True,
            can_delete_messages=True,
            can_manage_video_chats=True,
            can_restrict_members=False,  #  Ban/Kick permission ပိတ်ထား
            can_invite_users=True,
            can_pin_messages=True,
            can_promote_members=False,
            can_change_info=False,
        )
        await context.bot.set_chat_administrator_custom_title(
            chat_id=chat.id,
            user_id=target_id,
            custom_title=custom_title
        )
        await update.message.reply_text(
            f"✅ {target_user.mention_html()} ကို *{custom_title}* အဖြစ် Admin ခန့်ပြီးပါပြီ။",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(f"မအောင်မြင်ပါ  {e}")


# ---------- /mute ----------
async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user_id = update.effective_user.id

    if not is_admin_id(user_id):
        await update.message.reply_text("လီးမလို့မြုချင်ရတာလားမအေလိုး")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Mute ချင်သူကို စာထောက်ပြီး /mute သုံးပါ။")
        return

    target_user = update.message.reply_to_message.from_user
    target_id = target_user.id

    try:
        await context.bot.restrict_chat_member(
            chat_id=chat.id,
            user_id=target_id,
            permissions=ChatPermissions(can_send_messages=False)
        )
        await update.message.reply_text(
            f"🔇 {target_user.mention_html()} ကို mute လုပ်ပြီးပါပြီ။",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(f"မအောင်မြင်{e}")


# ---------- /unmute ----------
async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user_id = update.effective_user.id

    if not is_admin_id(user_id):
        await update.message.reply_text("စောက်ရှက်လဲမရှိပါလား")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Unmute ချင်သူကို စာထောက်ပြီး /unmute သုံးပါ။")
        return

    target_user = update.message.reply_to_message.from_user
    target_id = target_user.id

    try:
        await context.bot.restrict_chat_member(
            chat_id=chat.id,
            user_id=target_id,
            permissions=ChatPermissions(can_send_messages=True)
        )
        await update.message.reply_text(
            f"🔊 {target_user.mention_html()} ကို unmute ပြန်လုပ်ပြီးပါပြီ။",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(f"မအောင်မြင် {e}")


# ---------- /ban ----------
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user_id = update.effective_user.id

    if not is_admin_id(user_id):
        await update.message.reply_text("ထုတ်ချင်ရင်ဖင်ခံ")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Ban ချင်သူကို စာထောက်ပြီး /ban သုံးပါ။")
        return

    target_user = update.message.reply_to_message.from_user
    target_id = target_user.id

    try:
        await context.bot.ban_chat_member(
            chat_id=chat.id,
            user_id=target_id
        )
        await update.message.reply_text(
            f"{target_user.mention_html()} ကို group မှာ ban လုပ်ပြီးပါပြီ။",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(f"မအောင်မြင်ပါ {e}")

async def dead(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    if not is_authorized(user_id, username):
        return
    if not state.get("alive", True):
        return
    state["alive"] = False
    save_state()
    await context.application.stop()  # Silent stop

async def alive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    if not is_authorized(user_id, username):
        return
    if state.get("alive", True):
        await update.message.reply_text("Bot is already alive.")
        return
    state["alive"] = True
    save_state()
    await update.message.reply_text("Bot is alive again!")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "Bot ကိုသုံးချင်ရင် အောက်က ခလုတ်တွေကိုနှိပ်ပြီး စည်းကမ်းအတိုင်းလိုက်နာပြီး ပါမစ်လာတောင်းပါ"

    # Inline buttons with URLs
    button1 = InlineKeyboardButton(
        text="Permission တောင်းရန်",
        url="https://t.me/teletop1botchannel"  # ပထမ channel link
    )
    button2 = InlineKeyboardButton(
        text="Support Channel",
        url="https://t.me/Problem_Xz"  # ဒုတိယ channel link
    )

    keyboard = InlineKeyboardMarkup([[button1, button2]])  # နှစ်ခု button ကိုတန်းတူတန်းထား

    # Send message with buttons
    await update.message.reply_text(
        text=text,
        reply_markup=keyboard
    )

# Run the bot
# -------------------------
app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("attack", spam))
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("hide", hide))
app.add_handler(CommandHandler("stop_hide", stop_hide))
app.add_handler(CommandHandler("show", show))
app.add_handler(CommandHandler("hell", hell))
app.add_handler(CommandHandler("info", info_handler))
app.add_handler(CommandHandler("kick", kick_handler))
app.add_handler(CommandHandler("stophell", stophell))
app.add_handler(CommandHandler("send", send_handler))
app.add_handler(CommandHandler("funny", funny_command))
app.add_handler(CommandHandler("stopfunny", stop_funny_command))
app.add_handler(CommandHandler("stop", stop))
app.add_handler(CommandHandler("speed", speed))
app.add_handler(CommandHandler("id", id_command))
app.add_handler(CommandHandler("add_admin", add_admin))
app.add_handler(CommandHandler("remove_admin", remove_admin))
app.add_handler(CommandHandler("shutdown", shutdown))
app.add_handler(CommandHandler("multiple", multiple))
app.add_handler(CommandHandler("stop_multiple", stopmultiple))
app.add_handler(CommandHandler("name", set_name))
app.add_handler(CommandHandler("show_send_logs", show_send_logs))
app.add_handler(CommandHandler("add_message", add_message))
app.add_handler(CommandHandler("show_messages", show_messages))
app.add_handler(CommandHandler("add_group", add_group))
app.add_handler(CommandHandler("list_admins", list_admins))
app.add_handler(CommandHandler("add_group", add_group))
app.add_handler(CommandHandler("shownames", show_names))
app.add_handler(CommandHandler("upload", upload_reply_handler))
app.add_handler(CommandHandler("troll", troll_command))
app.add_handler(CommandHandler("untroll", untroll_command))
app.add_handler(CommandHandler("admin", adm))
app.add_handler(CommandHandler("mute", mute))
app.add_handler(CommandHandler("ban", ban))
app.add_handler(CommandHandler("dead", dead))
app.add_handler(CommandHandler("alive", alive))
app.add_handler(CommandHandler("show", show))  # optional
app.add_handler(CommandHandler("unmute", unmute))
app.add_handler(MessageHandler(filters.ALL, combined_message_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fight_message_handler))
app.add_handler(ChatMemberHandler(bot_added_to_group, ChatMemberHandler.MY_CHAT_MEMBER))

if __name__ == "__main__":
    app.run_polling()  # ဒီလိုရေးရင် setup compile အချိန်မှာ run မဖြစ်ပါ

