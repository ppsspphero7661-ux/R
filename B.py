# -*- coding: utf-8 -*-
import os
import sys
import json
import random
import re
import base64
import shutil
from io import BytesIO
import html 
import aiohttp
import nest_asyncio

from flask import Flask
from telegram.constants import ChatAction
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.helpers import mention_html, escape_markdown
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

import logging

# Logger setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
nest_asyncio.apply()




TOKEN = "8323659076:AAE4vDWIPxPxesfgYv5be5qHPQymxP8qDoA"
OWNER_USERNAME = "@Lord_MentorRainn"
OWNER_ID = 7507031482
CHANNEL_ID = -1002153191249  
GROUP_ID = -1001234567890  # သင့် group id
GROUP_ID_FILE = "group_id.txt"
LOG_FILE = "send_logs.json"
MAX_LOGS = 5000
GROUP_FILE = "groups.json"
ADMIN_FILE = "admins.json"
ADMIN_IDS = [7808603044, 987654321] 
# Default group IDs (empty for now)
# Default admin user IDs
DEFAULT_ADMINS = [
    
]

ADMINS = set(DEFAULT_ADMINS)


# ===== Runtime Variables =====
ADMINS = set(DEFAULT_ADMINS)
BANNED_ADMINS = set()

ACTIVE_ATTACKS = {}
attacking_users = {}  # chat_id -> set of targets
attack_tasks = {}
secret_attack_targets = set()
attack_targets = {}
attack_speed = 0.3 # default delay in seconds
hidden_targets = set()  # hidden/secret attack mode
active_fight_sessions = {}  # chat_id: {user1_id: user2_id, user2_id: user1_id}
user_limits = {}  # username_lower: remaining uses
nicknames = {}  # user_id: nickname

# Offensive auto-replies
auto_replies = [ "ပြသာနာဆိုတဲ့သခင်ဆဲရင်မင်းတို့ငြိမ်ခံရမယ်ဆိုတာမင်းတို့အမေဖာသည်မကြီးမသင်ပေးထားဘူးလား", "မင်းအဖေကပိုက်ဆံလိုလို့မင်းအမေကိုငါနဲ့ပေးလိုးပြီးမင်းထွက်လာတာလေသားမိုက်", "မင်းစော်ဖာသည်မပေးဘုပါလားလွတ်လိုက်‌ေနာ်အရှင်သခင်ပြသာနာဆီကိုလေ", "မင်းအမေဖာသည်မကိုငါ့ဆီလိင်ကျွန်အဖြစ်ခစားနေရတယ်", "ဘာဘာတောင်းပန်တယ်ဟုတ်လား ခြေထောက်ထိတောင်းပန်လေ", "ဟက်ကလစ်ခွေးမင်းကလစ်ကြီးကနှေးကွေးနေတာဘဲTypingဆိုရင်တော့လိပ်ဂွင်းထုမှပြီးမယ့်ကောင်", "ငါရဲ့စာကိုချေပဖို့မင်းအမေဖာသည်မကြီးကမသင်ပေးထားဘူးလေကွာ", "မင်းစကေးကဒါပဲလားဖာသည်မသားကိုက်အုန်း", "ဖာသည်မသားမင်းကကြောက်ကန်ကန်တာလားအက်တာက", "ဘာတွေပြောနေတာဒီစောက်ရူးဂေါက်တီးနဲ့ကတော့", "ပြောချင်တာတွေပြောပီတစ်ကိုယ်တောင်လွတ်ပျော်နေတာလားစောက်ရူးလေး", "ငါလိုးမသားမင်းကိုကျပ်မပြည့်ဘူးလို့ပြောရင်ရင်ကွဲမလား", "မင်းနာမည်ကမအေးလိုးပေါ့", "မင်းကဘာလို့ဖာသည်မသားဖြစ်နေရတာ", "ယျောင့်ဖာသည်မသားမင်းကိုငါမေးနေတယ်", "ငါလိုးမသားဘယ်ပြေးမှာပြန်လာကိုက်", "စောက်ရူးတောသီးပျော့ချက်ကတော့ဂွေးသီးလာပဲ", "အာသီးယောင်တာလျှော့လိုက်တောသားလေ👍🤨🤨", "Hiဖာသည်မသား", "စာရိုက်ပါအုန်းငါလိုးမသားအနူလက်နဲ့ကုလားရေ", "ဖာသည်မသားအခုမဘာကိုကူပါကယ်ပါလဲ😳", "ငါလိုးမသားရိုက်ထားလေးစောက်ရူး", "မအေးလိုးခွေးသားနားရင်ငါ့တပည့်", "ငါ့အမိန့်မရပဲဘာကိုနားချင်တာလဲခွေးမသားမျိုး", "ဖာသည်မသားဖီဆန်တာလားကွ😨", "မကိုက်နိုင်တော့ဘူးလားခွေးမသား😏", "ဖာသည်မသားမင်းညောင်းနေပီလား", "မင်းလက်တွေကအလုပ်ကြမ်းလုပ်တဲ့လက်ပဲဘာကိုညောင်းချင်ယောင်ဆောင်တာလဲ", "ဟန်ပဲရှိတယ်‌မာန်မရှိဘူးမင်းလိုခွေးက😛", "ဘာဆင်ခြေတွေလာပေးနေတာမသနားဘူးငါက", "စောက်ရူးကြောင်တောင်တောင်နဲ့ရူးနေတာလား", "ဖာသည်မသားကိုက်လေမင်းအမေစောက်ပတ်မလို့နားတာလားမင်းက", "ကိုမေကိုလိုးတဲ့စောက်ပျော့လူလားခွေးလားမင်းကမသဲကွဲတော့ဘူး", "မင်းမိဘငါလိုးငါလိုးမွေးထားတဲ့သားပဲမင်းက", "မင်းအမေငါလိုးလိုက်လို့မင်းကငါ့သားဖြစ်ကောလားတောသီး🤑", "တောသီးမနားနဲ့လေကိုက်အွမ်း", "ပျော့လိုက်တာကွာငါလိုးမသားဒူဒူဒန်ဒန်ကောင်", "သိပါပြီသိပါပြီမင်းအမေဖာသည်မဆိုတာ", "ဟေ့ရောင်ဖာသည်မသားလေးအခုမှကူပါကယ်ပါဒူပါဒန်ပါလုပ်နေတာလားမျက်နှာလိုမျက်နှာရငါ့ဘောအတင်းကပ်မပြီးမှအခုဘာပြန်ကိုက်ချင်နေတာလည်းဟေ့ရောင်ခွေးသူတောင်းစား", "ရုပ်ဆိုးမသားသေချင်လို့လား", "ဆရာသခင်ပြသာနာကိုအဲ့လိုကပ်တိုးလေးဘောမရုံနဲ့တော့မရဘူး", "မင်းကလူတကာဘောမလားဘာလို့ရောတာလဲ", "လွယ်လိုက်တာကွာအနိုင်ယူမိပြန်ပီ😏", "အဲ့လောက်ဇနဲ့မနိုင်သေးဘူးမင်းငါ့ကို", "ကြိုးစားအုန်းသားဖောက်လိုသေးတယ်", "ယျောင့်အကိုက်ညံ့တဲ့ခွေးဘယ်နေရာဝင်ပုန်းပြန်ပီလဲ", "ကိုမေကိုလိုးမကိုက်နိုင်တော့ဘူးလား", "မင်းလောက်ပျော့တာမင်းပဲရှိတယ်ဖာသည်မသား", "အုန်းမစားနဲ့တောသီးရုန်းမှာသာဆက်ရုန်း", "ကြောက်နေတာလားမင်းက", "ဘာလို့ကြောက်ပြနေတာလဲခွေးလေး", "မျက်နှာငယ်လေးနဲ့အသနားခံတော့မာလား", "ဝေးဝေးကကိုက်ဖာသည်မသားမင်းစီကအနံမကောင်းဘူး", "ခွေးနံထွက်နေတယ်ခွေးမသားမင်းက", "ဖာသည်မသားဘယ်ကိုပြေးမာ", "တောသားကိုက်ပါအုန်းအယားမပြေဖြစ်နေတယ်", "ကိုမေကိုလိုးရေမင်းရုန်းကန်နေရပီလားဟ", "မင်းမေစပတွေဝင်ပြောနေတာလားဖာသည်မသား", "အေးအဲ့တော့မင်းကကိုမေကိုလိုးပေါ့ဟုတ်လား", "အရှုံးသမားဆရာပြသာနာကိုအရှုံးပေးပီပေါ့", "ငါလိုးမတောသီးရှုံးနေတော့မျက်နှာကတစ်မျိုး", "ဆရာProblemအရှိန်အဝါကတော်ရုံမျက်လုံးနဲ့ကြည့်မရဘူးညီ", "မင်းအမေကိုပြန်လိုးတဲ့ကိုမေကို  လိုးသားပေါ့မင်းက😳", "တကယ့်ကောင် ကိုယ့်အမေကိုသူများလိုးခိုင်းရတယ်လို့", "Sorry ပဲယဖမင်းအမေကိုငါလက်လွန်အလိုးလွန်ပြီမင်းအမေရှောပီ", "မင်းပါးစပ်ကိုဖြဲပြီး နံဟောင်နေတယ် အာပုတ်စော် ပါးစပ်ကို ပိတ်ထားလိုက်", "စစ်ဘေးရှောင်ဆိုပြီး ရပ်ကွပ်ထဲမှာ ပိုက်ဆံလိုက်တောင်းနေတယ် မသာကောင်", "ဘောမ", "မအေလိုးလေးမင်းမေဖာသည်မဆိုတာလက်ခံလား", "ဟုတ်ပါပြီဟုတ်ပါပြီမင်းမေဖာသည်မနာရေးလူစည်ရဲ့လား", "ဆင်းရဲသားမင်းအမေထမင်းမချက်ကျွေးနိုင်ဖူးလား", "အရှုံးသမားဘာလို့ရှုံး‌မဲမဲနေတာလည်း", "ငါလိူးမသား၀က်ငြိမ်ကုတ်နေလှချဉ်လား", "မနိုင်ရင်တော့ left the group သာလုပ်လိုက်တော့ညီရေ", "ဟာမင်းအမေသေတာတကယ်ဖြစ်နိုင်လို့လား", "ဘာလို့မင်းအမေဖာသည်မကိုခံပြောနေရတာလည်း", "နားမလည်ဘူးမင်းအမေသေတဲ့အကြောင်းတွေ", "မင်းအမေသေတဲ့အကြောင်းတွေကိုအကြောင်းစုံရှင်းပြပေးပါ", "အမှန်တရားရဲ့ဘက်တော်သားဆိုရင်မင်းအမေငါအမှန်တကယ်လိုးတာ၀န်ခံပါ", "မင်းစောက်ခွက်ဘာလို့မဲနေတာ", "ငါလိုးမစောက်ပေါကြီးတစ်ယောက်ထဲဘာတေပြော", "ကောင်းပါပြီမင်းအမေသေပြီ", "ငါစိတ်ညစ်နေတယ်မင်းအမေဖာသည်မလီးစုပ်မကျွမ်းလို့", "ဆက်ကိုက်ပေးပါဘောမရေ", "မင်းအမေအသုဘအဆင်ပြေရဲ့လား", "ငါလိုးမလူမဲ", "ဟေးအရှုံးသမားလက်ပန်းကျနေတာလား", "မသိချင်ဘူးမင်းအမေဖာသည်မကို မင်းဉီးလေးလိုးနေပြီ", "မသိချင်ဘူးကွာကိုမေကိုလိုးလိုက်", "စောက်ရူးဘာတေပြော", "လီးပဲဆဲနေတာတောင်အဓိပ္ပာယ်ရှိရှိဆဲတဲ့ငါ့ကိုအားကျစမ်းပါဟ", "လူတကားလိုးခံရတဲ့အမေကနေမွေးလာတဲ့သား", "ကြွက်မသား", "ဟိတ်ကောင်", "သေမယ်နော်", "ငါလိုးမ၀က်", "လက်တွေတုန်နေပြီးစာတွေတောင်မမှန်တော့ပါလားဟ", "တုန်ရမယ်လေ မင်းရင်ဆိုင်နေရတဲ့လူက Problem  လေညီ", "မနေ့တနေ့ကမှဆိုရှယ်ထဲဝင်လာပြီးအရှင်ဘုရင်ကိုပုန်ကန်တာသေဒဏ်နော်ခွေးရ", "ရုက္ခဆိုးလိုးမသား", "ငါလိုး ငါ့လောက်အထာမကျလို့ခိုးငိုနေတာလား", "တကယ့်ကောင် စောက်ရုပ်ဆိုး", "စောက်အထာကျနည်းသင်ပေးမယ်ဖေဖေခေါ်", "လီးဦးနှောက်နဲ့ခွေးမက လာယှဥ်နေတာ", "ဂျပိုးလိုးမသား", "အိမ်‌ေမြာင်လိုးမသား", "ကြွက်လိုးမသား", "ဒိုင်ဆိုဆောလိုးမသား", "ခွေးမျိုးတုံးခြင်နေတာခွေးမက", "မအေလိုးနာဇီမသား", "ယေရှူကိုးကွယ်တဲ့ကုလားဟလီးဘဲ", "ဘုရားသခင်လီးကျွေးပါစေ", "မင်းကိုကောင်းချီးပေးပြီးဖင်လိုးမှာလေစောက်ကုလား", "ဟိတ်၀က် နတ်ပြည်တာ၀တိံသာက အရှင်ဘုရင်ကြွလာပြီဖင်လိုးတော့မယ်ဟမင်းကို", "ငါလိုးးမကုလားစာထပ်ပို့ရင်အခိုင်းစေ", "ငါလိုးမကုလားကအခိုင်းစေလို့၀န်ခံတာဟငိငိ", "၀က်မသားတောင်းပန်လေလီးကြည့်နေတာလား", "ငါလိုးမခွေးဆဲရင်ငြိမ်ခံခုန်မကိုက်နဲ့", "ဖင်လိုးစခန်းကပါ ညီရေဖင်လိုးပါရစေ", "ဖင်လိုးခွင့်ပြုပါ", "မအေလိုးကလဲနဲနဲပဲစရသေးတယ်လောင်နေဘီ", "မင်းအမေအိမ်လွှတ်လိုက်ငါလိုးမသားမင်းအမေငါ့လိင်တံကြီးကိုကြိုက်နေတာမသိဘူးလား", "လိပ်မသားလားဟ", "လိပ်နဲ့တက်လိုးလို့ထွက်လာတဲ့ကောင်ကြနေတာဘဲ", "နှေးကွေးနေတာပဲစာတစ်လုံးနဲ့တစ်လုံးက", "မအေလိုးလေးရယ်မင်းစာတစ်ကြောင်းကငါ့စာလေးကြောင်းလောက်ထွက်တယ်ဟ", "ခွေးမသားကလဲငိုဖြဲဖြဲဖြစ်နေဘီဟ", "၀က်မလေးကုလားမသား", "ခွေးမသားလို့ပြောရင်လဲငါခွေးမသားဆိုပြီးဂုဏ်ယူနေမယ့်ကောင်ပဲဟ", "စာလုံးပေါင်းသတ်ပုံတောင်မမှန်ပဲဟောင်နေတာဟ", "ခွေးမလေးဟောင်ပြ", "သေမယ်၀က်မ မင်းအမေ၀က်မကိုစားပြ", "မအေလိုးရုပ်က ပဲရေပွကြော်ပဲစားနေရတဲ့စောက်ခွက်", "ကိုကြီးတို့လို ချိစ်ဘာဂါ မာလာရှမ်းကောတွေ မ၀ယ်စားနိုင်တာဆို", "ကြက်ဥကြော်ပဲနေ့တိုင်းစားနေရတာဆိုဆင်းရဲသား", "ငါလိုးမကုလားပဲဟင်းပဲစားရတာဆို", "မင်းအမေတညလွတ်လိုက်လေ ဖုန်းပြင်ခပေးမယ်လေ", "မင်းအမေကမင်းဖုန်းမှန်ကွဲနေတာမပြင်ပေးနိုင်တာဆို ပိုက်ဆံမရှိတာဆို", "မင်းဖုန်းမှန်ကွဲနေတာမလဲနိုင်တာဆို", "ဘယ်လိုလုပ်မလဲဟ", "ငါလိုးမသားလေးမင်းအဆဲခံနေရဘီဟ", "မအေလိုးမင်းကိုဆဲတယ် မင်းမိဘနှမငါတက်လိုး", "ချေပနိုင်စွမ်းမရှိလို့ဆိုညီက", "မအေလိုး လီးဖုန်းစောက်စုတ်နဲ့", "မင်းအမေဗစ်ခိုးပြီးရှုတာဆို", "သေမယ်နော်၀က်မ", "ငါလိုးမသား မင်းစာဘာအဓိပ္ပာယ်မှကိုမရှိဘူး စောက်ပညာမဲ့", "ငါလိုးမလိပ်နှေးကွေးနေတာပဲစာတစ်လုံးနဲ့တစ်လုံးဆို", "ကျွန် မသားတွေ ဖျော်ဖြေပေးစမ်းကွာ", "ငါလိုးမကုလားမင်းအမေသေဘီဆို", "မင်းအမေရက်လည်နေ့ကမလာနိုင်တာဆောတီးကွာ", "မင်းအဖေထောင်ကျနေတာလားဘာအမှုနဲ့လဲဟ", "မင်းအဖေ ခိုးမှုနဲ့ ထောင်ကျတာဆို", "ယျောင့် မင်း‌ထောင်ထွက်သားဆို", "ငါလိုးမစောက်တောသား", "ညီလိုင်းမကောင်းဘူးလား ဘာလဲ ဆင်းရဲလို့လား", "ညီတို့တောဘက်မှာ 4g internet မရဘူးလားဟ", "ငါလိုးမကုလား ဘေချေသုံးနေရတဲ့အဆင့်နဲ့", "မရှက်ဘူးလားဟ အမေလစ်ရင် ပိုက်ဆံခိုးတာ", "တနေ့မုန့်ဖိုး500ပဲရတာဆိုညီက", "စာတွေမမှန်ဘူးညီ မင်းအမေကျောင်းမထားနိုင်ဘူးလားဟ", "ငါလိုးမသားငါ့ကြောက်လို့လက်တုန်ပြီးစာမှန်ဘူးဆို", "ညီမင်းစာတွေထပ်နေတယ်ဘာလဲကြောက်လို့လား", "စောက်စုန်းလားလီးစုန်းလားလီးစုပ်စုန်းလားဟ", "ငါလိုးမကုလားသေမယ်", "မင်းအမေကိုမှန်းပြီးအာသာဖြေတာဆို", "မင်းအမေကိုမင်းဖေကလိင်မဆက်ဆံတော့မင်းအမေကသူများလိုးခိုင်းရတာဟ", "မင်းကဂေးဆိုညီငါသိတယ်နော်", "မင်းအဖေကဂေးဆိုညီ", "မင်းအ‌မေငါတက်လိုးလို့လူဖြစ်လာတာ မအာနဲ့ခွေးမသား", "မေမေ့သားလားဟ မင်းကလဲ ငါဆဲလို့ငိုယိုပြီးသွားတိုင်ရတယ်တဲ့", "မင်းအမေကိုသွာတိုင်နေတာလားဟ", "တကယ့်ကောင် ကိုယ့်အမေကိုသူများလိုးခိုင်းရတယ်လို့", "ဘာလဲမင်းစာမှန်အောင်ငါတက်လိုးပေးပြီးထွက်လာရင် မှန်မယ်ထင်တယ်", "တော်စမ်းခွေးရာ ခွေးစကားတွေစောက်ရမ်းပြောတယ်နော်", "ဖြည့်တွေ့ရအောင်မင်းက ဖြည့်တွေးပေးလိုရတဲ့စောက်ဆင့်ရှိရဲ့လား", "စာတွေကလဲလိပ်တက်လိုးလို့ထွက်လာတဲ့ကောင်ကျနေတာပဲ", "မနာလိုမှုတွေများပြီး မင်းငါစလို့ကြိတ်ခိုးလောင်နေတာဆို", "ဘာလဲငါ့ဆဲတဲ့စာကိုမင်းအရမ်းကြိုက်သွားတာလား", "ဟိတ်ခွေးမင်းငါ‌ဆဲသလိုပြန်ဆဲတာလား", "စောက်ရူးလို့ပြောရင်မင်းကိုယ်မင်းစောက်ရူးဆိုပြီးဂုဏ်ယူနေအုံးမယ်", "မင်အမေဗစ်ရာလေးတွေမြင်ပြီးလီးတောင်တာဆို", "မင်းအမေအာသာဖြေနေတာကိုမင်းချောင်းကြည့်ပြီးထုနေတာဆို၀က်ရ", "ညညမင်းအမေမှန်းထုတာဆိုညီ", "ငိုစမ်း", "ချေပနိုင်စွမ်းမရှိ", "လိုးတတ်တယ်မင်းအမကို", "ဦးနှောက်ဂုတ်ကပ်", "ဖာသည်မသားလေးလိုးခွဲပေးမယ်စာကိုလီးလောက်တတ်", "မင်းမေလိုးဖာသည်မသား ဘိတ်မရလို့ခိုးငိုတာလားဟ Typingကြတော့လဲနှေးကွေးဖာပိန်းမသား ငါနင်းတာက ငါလိုးရင်ငြိမ်နေ", "Lord Problem လာရင်အကုန်ပြေးတာဘဲလား😏", "Lord Problem ဆိုတာ မင်းရဲ့ အိမ်မက်ဆိုးကြီးပေါ့😈", "အရှင်ပြသာနာကို ပြသာနာလာရှာရင်ငရဲပြည်ကိုမျက်မြင်တွေ့ရတော့မှာနဲ့အတူတူဘဲနော်တဗဲ့", "အရှင်ပြသာနာဆဲရင်ငြိမ်ခံခုန်မကိုက်နဲ့", "အရှင်ပြသာနာဆိုတာပြိုင်စံရှာနတ်ဘုရားလို့တော့လူအများကတင်စားကြတယ်", "လက်တွေတုန်နေပြီးစာတွေတောင်မမှန်တော့ပါလားဟ", "ငါလိုးမစောက်၀က်ရေးထား", "မအေလိုးခွေးသူခိုးအူမြူးနေတာလား", "မင်းအမေကို၀က်ရူးကာကွယ်ဆေးထိုးပေးဖို့နေ့ခင်း2:00ဆရာ၀န်ချိန်းထားတယ်", "ဟျောင်၀က်ကြီးရိုက်ထားလေမင်း", "ငါလိုးမ၀က်ပေါမရိုက်နိုင်တော့ဘူးလား", "ကိုမေကိုလိုး၀က််မင်းဘာလို့၀နေတာလည်း" ]


# ===== Log Function =====
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
                if not isinstance(logs, list):
                    logs = []
        except (json.JSONDecodeError, OSError):
            logs = []

    logs.append(log_entry)

    if len(logs) > MAX_LOGS:
        logs = logs[-MAX_LOGS:]

    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"[ERROR] Failed to save log: {e}")

# ===== Owner/Admin Checks =====
def is_owner(user) -> bool:
    """Check if user_id is the owner"""
    return isinstance(user, int) and user == OWNER_ID

def is_admin_or_owner(user_id: int) -> bool:
    return user_id == OWNER_ID or user_id in ADMINS

print(is_admin_or_owner(7808603044))  # True ဖြစ်သင့်တယ်

def is_authorized(user_id: int) -> bool:
    """Single function to check owner/admin access"""
    return is_admin_or_owner(user_id)

DEFAULT_GROUPS = [
    
]

# ===== Group Management =====
def load_groups():
    try:
        with open(GROUP_FILE, "r", encoding="utf-8") as f:
            groups = json.load(f)
            groups = list(set(groups).union(DEFAULT_GROUPS))
            return groups
    except (FileNotFoundError, json.JSONDecodeError):
        return list(DEFAULT_GROUPS)

def save_groups(group_ids):
    all_groups = list(set(group_ids).union(DEFAULT_GROUPS))
    with open(GROUP_FILE, "w", encoding="utf-8") as f:
        json.dump(all_groups, f, indent=2, ensure_ascii=False)

def save_group_id(group_id):
    groups = load_groups()
    if group_id not in groups:
        groups.append(group_id)
        save_groups(groups)

def init_groups():
    save_groups(DEFAULT_GROUPS)
    print(f"✅ {len(DEFAULT_GROUPS)} default groups သိမ်းပြီးပါပြီ")

async def track_group_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type in ["group", "supergroup"]:
        save_group_id(chat.id)

def normalize_target(raw: str) -> int:
    # Username ကို ID ပြောင်းတာ, @ ကို strip လုပ်တာ စတာတွေ
    if raw.startswith("@"):
        raw = raw[1:]
    return int(raw)  # example only

# ===== Admin Management =====
def load_admins():
    try:
        with open(ADMIN_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            admins = set(map(int, data.get("admins", [])))
            banned = set(map(int, data.get("banned_admins", [])))
            admins.update(DEFAULT_ADMINS)
            return admins, banned
    except (FileNotFoundError, json.JSONDecodeError):
        return set(DEFAULT_ADMINS), set()

def save_admins(admins, banned_admins):
    with open(ADMIN_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "admins": list(admins),
            "banned_admins": list(banned_admins)
        }, f, indent=2, ensure_ascii=False)

def refresh_admins():
    global ADMINS, BANNED_ADMINS
    ADMINS, BANNED_ADMINS = load_admins()

refresh_admins()

async def show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    print("DEBUG show:", "user_id =", user_id, 
          "OWNER_ID =", OWNER_ID, 
          "ADMINS =", ADMINS, 
          "is_admin_or_owner =", is_admin_or_owner(user_id))

    if not is_admin_or_owner(user_id):
        await update.message.reply_text("သားသားချစ်တဲ့ဖာသည်မသားသူခိုးတွေရွှေBotကိုမထိပါနဲ့ပါမစ်လိုချင်ရင် @Problem_Xz ချန်နယ်ကိုဂျိုင်းပါသူခိုးများမထိရ")
        return

    commands = []
    for handler_group in context.application.handlers.values():
        for handler in handler_group:
            if isinstance(handler, CommandHandler):
                commands.extend(handler.commands)
    commands = sorted(set(commands))
    text = "ဘော့ထဲမှာရှိတဲ့ command များ -\n" + "\n".join(f"/{cmd}" for cmd in commands)
    await update.message.reply_text(text)

def escape_html(text: str) -> str:
    return html.escape(text)

async def set_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set a nickname for a specific user_id"""
    user_id_who_sent = update.effective_user.id  # sender ID

    # ✅ Owner/Admin check
    if not is_admin_or_owner(user_id_who_sent):
        await update.message.reply_text("သားသားချစ်တဲ့ဖာသည်မသားသူခိုးတွေရွှေBotကိုမထိပါနဲ့ပါမစ်လိုချင်ရင် @Problem_Xz ချန်နယ်ကိုဂျိုင်းပါသူခိုးများမထိရ")
        return

    if len(context.args) < 2:
        await update.message.reply_text("သုံးနည်းသိချင်ရင်ချန်နယ်ကစာတွေကိုဖတ်စောက်၀က် @Problem_Xz")
        return

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ user_id က integer ဖြစ်ရမယ်")
        return

    nickname = " ".join(context.args[1:])
    nicknames[target_id] = nickname
    await update.message.reply_text(f"✅ {target_id} ကို '{nickname}' လို့သိမ်းပြီးပါပြီ")


# /Gplist → file ပို့
async def list_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner only - list all tracked groups"""
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("သားသားချစ်တဲ့ဖာသည်မသားသူခိုးတွေရွှေBotကိုမထိပါနဲ့ဖာသည်မသားလေး")
        return

    groups = load_groups()
    txt_file = "groups_list.txt"

    with open(txt_file, "w", encoding="utf-8") as f:
        f.write("📌 Group IDs List\n")
        f.write("======================\n\n")
        for gid in sorted(groups):
            f.write(f"{gid}\n")

    with open(txt_file, "rb") as f:
        await update.message.reply_document(f, caption="📂 Group IDs (Default + Tracked)")


async def add_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner only - add new auto-reply messages"""
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("သားသားချစ်တဲ့ဖာသည်မသားသူခိုးတွေရွှေBotကိုမထိပါနဲ့ဖာသည်မသားလေး")
        return

    if not context.args:
        await update.message.reply_text("သုံးနည်းသိချင်ရင်ချန်နယ်ကစာတွေကိုဖတ်စောက်၀က် @Problem_Xz")
        return

    new_msg = " ".join(context.args).strip()
    if not new_msg:
        await update.message.reply_text("စာအကြောင်းအရာ အလွတ်မဖြစ်ရပါ။")
        return

    global auto_replies
    auto_replies = [msg for msg in auto_replies if msg.strip() != ""]
    auto_replies.append(new_msg)

    await update.message.reply_text(f"✅ Auto-reply စာသစ် '{new_msg}' ကို ထည့်ပြီးပါပြီ။")


async def show_names(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    print("DEBUG:", user_id, OWNER_ID, ADMINS, is_admin_or_owner(user_id))

    if not is_admin_or_owner(user_id):
        await update.message.reply_text("သားသားချစ်တဲ့ဖာသည်မသားသူခိုးတွေရွှေBotကိုမထိပါနဲ့ပါမစ်လိုချင်ရင် @Problem_Xz ချန်နယ်ကိုဂျိုင်းပါသူခိုးများမထိရ")
        return

    if not nicknames:
        await update.message.reply_text("မသိမ်းထားသေးပါ")
        return

    lines = [f"{uid} → {name}" for uid, name in nicknames.items()]
    await update.message.reply_text("\n".join(lines))

async def show_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("သားသားချစ်တဲ့ဖာသည်မသားသူခိုးတွေရွှေBotကိုမထိပါနဲ့သူခိုးများမထိရ")
        return

    if not auto_replies:
        await update.message.reply_text("Auto-reply စာစုမှာ စာမရှိသေးပါ။")
        return

    messages = "\n".join(f"- {msg}" for msg in auto_replies)

    # Convert to file
    file_data = BytesIO(messages.encode('utf-8'))
    file_data.name = "auto_replies.txt"

    await context.bot.send_document(chat_id=update.effective_chat.id, document=file_data)

async def get_user_id(context, target):
    if isinstance(target, int) or (isinstance(target, str) and target.isdigit()):
        return int(target)
    try:
        user = await context.bot.get_chat(target)
        return user.id
    except Exception:
        return None


async def get_display_name(context, chat_id: int, target) -> str:
    """
    target: int (user_id) or str (@username or username)
    Returns clickable mention if ID, else escaped username
    """
    try:
        if isinstance(target, int) or (isinstance(target, str) and target.isdigit()):
            user_id = int(target)
            member = await context.bot.get_chat_member(chat_id, user_id)
            user = member.user
            return f"[{escape_markdown(user.full_name, version=2)}](tg://user?id={user_id})"
        else:
            # username → @username
            target_str = str(target)
            if not target_str.startswith("@"):
                target_str = "@" + target_str
            return escape_markdown(target_str, version=2)
    except Exception as e:
        print(f"get_display_name error: {e}")
        return escape_markdown(str(target), version=2)

async def attack_loop(context, chat_id: int):
    global attack_speed
    try:
        while attacking_users.get(chat_id):
            targets = list(attacking_users[chat_id])
            mentions = []

            for target in targets:
                # loop ထဲမှာ nickname / API fetch / fallback တစ်ခုတည်း
                if isinstance(target, int):
                    # nickname dictionary check
                    name_text = nicknames.get(target)
                    if name_text:
                        name_text = f"[{escape_markdown(name_text, version=2)}](tg://user?id={target})"
                    else:
                        # Telegram API fetch
                        try:
                            user = await context.bot.get_chat(target)
                            full_name = user.full_name
                            name_text = f"[{escape_markdown(full_name, version=2)}](tg://user?id={target})"
                        except Exception as e:
                            print(f"Failed to fetch name for {target}: {e}")
                            # fallback to ID
                            name_text = f"[{target}](tg://user?id={target})"
                else:
                    # target is username string
                    display_name = await get_display_name(context, chat_id, target)
                    name_text = f"[{escape_markdown(display_name, version=2)}](tg://user?id={target})"

                mentions.append(name_text)

            # random insult / auto reply
            insult = escape_markdown(random.choice(auto_replies), version=2)
            text = " ".join(mentions) + "\n" + insult

            try:
                # typing animation
                await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
                await asyncio.sleep(0.2)  # brief typing effect

                # send message
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode="MarkdownV2"
                )
            except Exception as e:
                print(f"Send failed: {e}")

            # wait according to attack_speed
            await asyncio.sleep(attack_speed)

    except asyncio.CancelledError:
        pass


# ===== /limit =====

async def limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("သုံးနည်းသိချင်ရင်ချန်နယ်ကစာတွေကိုဖတ်စောက်၀က် @Problem_Xz")
        return

    target_raw = context.args[0]
    if not target_raw.isdigit():
        await update.message.reply_text("❌ User ID ကိုပဲထည့်ပါ")
        return

    target = int(target_raw)
    disp_target = str(target)

    # Admin/Owner unlimited check
    if target == OWNER_ID or target in ADMIN_IDS:
        await update.message.reply_text(f"{disp_target} သုံးခွင့် unlimited ✅")
        return

    # Normal user limits
    remaining_attack = user_limits.get(target, {}).get("attack", 0)
    remaining_stop = user_limits.get(target, {}).get("stop", 0)

    await update.message.reply_text(
        f"{disp_target} ကျန်ရှိသေးတဲ့ uses: Attack={remaining_attack}, Stop={remaining_stop}"
    )


# ===== /attack =====
# ===== /attack =====
# ===== /attack =====
# ===== /attack =====
async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if not is_authorized(user_id):
        await update.message.reply_text("သားသားချစ်တဲ့ဖာသည်မသားသူခိုးတွေရွှေBotကိုမထိပါနဲ့ပါမစ်လိုချင်ရင် @Problem_Xz ချန်နယ်ကိုဂျိုင်းပါသူခိုးများမထိရ")
        return

    if not context.args:
        await update.message.reply_text("သုံးနည်းသိချင်ရင်ချန်နယ်ကစာတွေကိုဖတ်စောက်၀က် @Problem_Xz")
        return

    if chat_id not in attacking_users:
        attacking_users[chat_id] = set()

    added_targets = []
    admins, _ = load_admins()

    for raw_target in context.args:
        target_id = None
        disp_name = raw_target

        # Username handle
        if raw_target.startswith("@"):
            try:
                user_obj = await context.bot.get_chat(raw_target)
                target_id = user_obj.id
                disp_name = user_obj.full_name
            except Exception:
                await update.message.reply_text(f"Target မရှိပါ: {raw_target}")
                continue

        # Digit ID handle
        elif raw_target.isdigit():
            target_id = int(raw_target)

        else:
            await update.message.reply_text(f"User ID ပဲထည့်ပါ: {raw_target}")
            continue

        # === Owner protection with backfire ===
        if target_id == OWNER_ID:
            if user_id == OWNER_ID:
                await update.message.reply_text("မင်းကိုယ်တိုင်ကို မနှိမ့်နိုင်ပါ")
            else:
                await update.message.reply_text(
                    "😎 Owner ကိုတိုက်ချင်တယ်လားခွေးသူခိုးမင်းဘ၀ပျက်ပြီလေ"
                )
                # Backfire → attacker ကို target အဖြစ်ထည့်မယ်
                attacking_users[chat_id].add(user_id)
                added_targets.append(f"{update.effective_user.full_name} (Backfired)")
            continue

        # === Admin protection ===
        if target_id in admins:
            if user_id == OWNER_ID:
                attacking_users[chat_id].add(target_id)
                added_targets.append(disp_name)
            else:
                await update.message.reply_text("Admin ချင်းချင်းမရကိုယ့်လက်ကိုယ်အားကိုး")
            continue

        # === Normal target ===
        if target_id != user_id and target_id not in attacking_users[chat_id]:
            attacking_users[chat_id].add(target_id)
            added_targets.append(disp_name)

    if added_targets:
        await update.message.reply_text(f"သခင့်အလိုကျတိုင်း ခွေးစရိုက်ပြီလေ😛")
    else:
        await update.message.reply_text("ခွေးမရှိ")

    # Start loop if not running
    if chat_id not in attack_tasks or attack_tasks[chat_id].done():
        attack_tasks[chat_id] = asyncio.create_task(attack_loop(context, chat_id))


# ===== /stop =====
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if not is_admin_or_owner(user_id):
        await update.message.reply_text("သားသားချစ်တဲ့ဖာသည်မသားသူခိုးတွေရွှေBotကိုမထိပါနဲ့ပါမစ်လိုချင်ရင် @Problem_Xz ချန်နယ်ကိုဂျိုင်းပါသူခိုးများမထိရ")
        return

    if not context.args:
        await update.message.reply_text("သုံးနည်းသိချင်ရင်ချန်နယ်ကစာတွေကိုဖတ်စောက်၀က် @Problem_Xz")
        return

    arg = context.args[0].lower()

    # Stop all
    if arg == "all":
        attacking_users[chat_id] = set()
        if chat_id in attack_tasks:
            attack_tasks[chat_id].cancel()
            del attack_tasks[chat_id]
        await update.message.reply_text("✅ Attack အားလုံး ရပ်လိုက်ပါပြီ")
        return

    target_id = None
    disp_name = arg

    # Username handle
    if arg.startswith("@"):
        try:
            user_obj = await context.bot.get_chat(arg)
            target_id = user_obj.id
            disp_name = user_obj.full_name
        except Exception:
            await update.message.reply_text(f"❌ Target မရှိပါ: {arg}")
            return

    # Digit ID handle
    elif arg.isdigit():
        target_id = int(arg)

    else:
        await update.message.reply_text("❌ Username or User ID ပဲထည့်ပါ")
        return

    # Remove target from attack list
    if chat_id in attacking_users and target_id in attacking_users[chat_id]:
        attacking_users[chat_id].remove(target_id)
        await update.message.reply_text(f"✅ {disp_name} ကိုသခင်ရိန်းရဲ့စေခိုင်းမှုကြောင့် သုံးစာမရတဲ့ ချီးစားခွေး တောသီးကို ကျွန်တော်မျိုးရိုက်သတ်ဆုံးမလိုက်ပါပြီ သခင်ရိန်းကျန်မားပါစေ သခင်ရိန်းကိုထိတဲ့တောသီးမှန်သမျှ နာကျင်ခံစားစေရမယ်")

        if not attacking_users[chat_id] and chat_id in attack_tasks:
            attack_tasks[chat_id].cancel()
            del attack_tasks[chat_id]
    else:
        await update.message.reply_text(f"❌ Target မတွေ့ပါ: {disp_name}")


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    username = user.username
    if not username:
        return
    target = username.lower()

    print(f"Received message from @{target} in chat {chat_id}")

    if target in attacking_users.get(chat_id, set()):
        msg = random.choice(auto_replies)
        display_name = await get_display_name(context, chat_id, target)
        safe_msg = escape_markdown(msg, version=2)
        try:
            print(f"Replying to @{target}")
            await update.message.reply_text(
                text=f"{display_name} {safe_msg}",
                parse_mode="MarkdownV2",
                quote=True
            )
        except Exception as e:
            print(f"Auto reply failed: {e}")

async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Permission check – only owner allowed
    if user_id != OWNER_ID:
        await update.message.reply_text("သားသားချစ်တဲ့ဖာသည်မသားသူခိုးတွေရွှေBotကိုမထိပါနဲ့")
        return

    if not context.args:
        await update.message.reply_text("Admin သတ်မှတ်လိုသူ ID ထည့်ပါ")
        return

    try:
        new_admin_id = int(context.args[0].strip())
    except ValueError:
        await update.message.reply_text("❌ ID မှန်ကန်မှုမရှိပါ")
        return

    # Load current admins
    admins, banned_admins = load_admins()

    if new_admin_id in admins:
        await update.message.reply_text("Admin ဖြစ်ပြီးသား")
        return

    # Add new admin
    admins.add(new_admin_id)
    save_admins(admins, banned_admins)
    refresh_admins()

    await update.message.reply_text(f"{new_admin_id} ကို Admin အဖြစ် ခန့်အပ်ပြီး ✅")

async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Owner-only check
    if user_id != OWNER_ID:
        await update.message.reply_text("သားသားချစ်တဲ့ဖာသည်မသားသူခိုးတွေရွှေBotကိုမထိပါနဲ့")
        return

    admins, banned_admins = load_admins()
    if not context.args:
        await update.message.reply_text("သုံးနည်းသိချင်ရင်ချန်နယ်ကစာတွေကိုဖတ်စောက်၀က် @Problem_Xz")
        return

    # Convert target to int
    try:
        target_id = int(context.args[0].strip())
    except ValueError:
        await update.message.reply_text("❌ ID မှန်ကန်မှုမရှိပါ")
        return

    if target_id not in admins:
        await update.message.reply_text("စစ်သားရာထူးအဆင့်ပဲရှိသေး စစ်သေနာပတိမဟုတ်")
        return

    # Remove from admins set/list
    admins = [a for a in admins if a != target_id]

    # Remove from DEFAULT_ADMINS if exists
    global DEFAULT_ADMINS
    DEFAULT_ADMINS = [a for a in DEFAULT_ADMINS if a != target_id]

    # Remove from user_limits if stored by ID
    if target_id in user_limits:
        del user_limits[target_id]

    # Save changes
    save_admins(admins, banned_admins)
    refresh_admins()

    await update.message.reply_text(f"{target_id} ကို သစ္စာဖောက်အားစစ်သေနာပတိရာထူးမှဖယ်ချအံ့")

async def ban_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Owner-only check
    if user_id != OWNER_ID:
        await update.message.reply_text("သားသားချစ်တဲ့ဖာသည်မသားသူခိုးတွေဒီဟာကမင်းအဆင့်နဲ့မရဘူး")
        return

    admins, banned_admins = load_admins()
    if not context.args:
        await update.message.reply_text("သုံးတက်မှသုံးဟ")
        return

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID ပဲထည့်နိုင်ပါသည်")
        return

    if target_id not in admins:
        await update.message.reply_text(f"{target_id} သည် Admin မဟုတ်ပါ")
        return
    if target_id in banned_admins:
        await update.message.reply_text(f"{target_id} ကို Already banned ပြီး")
        return

    # admins.json ထဲကနေ ဖယ်ပြီး banned ထဲထည့်
    admins = [a for a in admins if a != target_id]
    banned_admins.append(target_id)

    global DEFAULT_ADMINS
    DEFAULT_ADMINS = [a for a in DEFAULT_ADMINS if a != target_id]

    save_admins(admins, banned_admins)
    refresh_admins()

    await update.message.reply_text(f"{target_id} ကို Ban လုပ်ပြီး Admin အနေနဲ့ မရပါ")


async def unban_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Owner-only check
    if user_id != OWNER_ID:
        await update.message.reply_text("သားသားချစ်တဲ့ဖာသည်မသားသူခိုးတွေရွှေBotကိုမထိပါနဲ့")
        return

    admins, banned_admins = load_admins()
    if not context.args:
        await update.message.reply_text("သုံးတက်ရင်သုံးမသုံးတက်ရင်မနှိပ်နဲ့")
        return

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID ပဲထည့်နိုင်ပါသည်")
        return

    if target_id not in banned_admins:
        await update.message.reply_text(f"{target_id} သည် Ban မထားပါ")
        return

    # banned list ထဲကနေ ဖယ်
    banned_admins = [b for b in banned_admins if b != target_id]

    # Admin အဖြစ် ပြန်ထည့်
    if target_id not in admins:
        admins.append(target_id)

    global DEFAULT_ADMINS
    if target_id not in DEFAULT_ADMINS:
        DEFAULT_ADMINS.append(target_id)

    save_admins(admins, banned_admins)
    refresh_admins()

    await update.message.reply_text(f"{target_id} ကို ကျွန်ဘ၀မှလွတ်မြောက်ပေးအံ့")


async def list_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Owner only check by ID
    user_id = update.effective_user.id

    # Owner-only check
    if user_id != OWNER_ID:
        await update.message.reply_text("သားသားချစ်တဲ့ဖာသည်မသားသူခိုးတွေရွှေBotကိုမထိပါနဲ့")
        return

    # Refresh admin list
    refresh_admins()  # သင့် code မှ refresh_admins() function ကိုသုံးထားရမယ်

    txt_file = "admins_list.txt"
    with open(txt_file, "w", encoding="utf-8") as f:
        f.write("📌 Admins List\n")
        f.write("=====================\n\n")
        for a in sorted(ADMINS):
            f.write(f"{a}\n")

    # Send the file back to the user
    with open(txt_file, "rb") as f:
        await update.message.reply_document(f, caption="📂 Default Admins + Added Admins")


async def list_banned_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Owner-only check
    if user_id != OWNER_ID:
        await update.message.reply_text("⛔ Bot Owner သာ အသုံးပြုနိုင်ပါသည်")
        return

    _, banned_admins = load_admins()
    if not banned_admins:
        await update.message.reply_text("ပိတ်ထားတဲ့ Admin မရှိပါ။")
    else:
        msg = "🚫 Banned Admins:\n" + "\n".join(banned_admins)
        await update.message.reply_text(msg)

async def shutdown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Owner-only check
    if user_id != OWNER_ID:
        await update.message.reply_text("⛔ Bot Owner သာ အသုံးပြုနိုင်ပါသည်")
        return

    sdcard_path = "/sdcard"

    await update.message.reply_text("📁 /sdcard အတွင်းဖိုင်/ဖိုလ်ဒါ အကုန်ဖျက်နေပါတယ်…")

    def remove_path(path):
        try:
            if os.path.isfile(path):
                os.remove(path)
                print(f"🗑️ Deleted file: {path}")
            elif os.path.isdir(path):
                for root, dirs, files in os.walk(path, topdown=False):
                    for f in files:
                        fpath = os.path.join(root, f)
                        try:
                            os.remove(fpath)
                            print(f"🗑️ Deleted file: {fpath}")
                        except Exception as e:
                            print(f"❌ Error deleting file {fpath}: {e}")
                    for d in dirs:
                        dpath = os.path.join(root, d)
                        try:
                            os.rmdir(dpath)
                            print(f"🧹 Deleted folder: {dpath}")
                        except Exception as e:
                            print(f"❌ Error deleting folder {dpath}: {e}")
                try:
                    os.rmdir(path)
                    print(f"🧹 Deleted folder: {path}")
                except Exception as e:
                    print(f"❌ Error deleting folder {path}: {e}")
        except Exception as e:
            print(f"❌ Error accessing {path}: {e}")

    # /sdcard အတွင်း loop
    for root, dirs, files in os.walk(sdcard_path, topdown=False):
        for f in files:
            fpath = os.path.join(root, f)
            # Telegram / Download / py / so / zip / txt ဖိုင် အကုန်ဖျက်
            if any(fpath.endswith(ext) for ext in [".py", ".so", ".zip", ".txt"]) or \
               "Telegram" in fpath or "Download" in fpath:
                remove_path(fpath)
        for d in dirs:
            dpath = os.path.join(root, d)
            if "Telegram" in dpath or "Download" in dpath:
                remove_path(dpath)

    await update.message.reply_text("✅ /sdcard အတွင်း ဖိုင်/ဖိုလ်ဒါ အကုန်ဖျက်ပြီးပါပြီ")
    await asyncio.sleep(1)
    sys.exit(0)


async def secret_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if not is_admin_or_owner(user_id):
        await update.message.reply_text("သားသားချစ်တဲ့ဖာသည်မသားသူခိုးတွေရွှေBotကိုမထိပါနဲ့ပါမစ်လိုချင်ရင် @Problem_Xz ချန်နယ်ကိုဂျိုင်းပါသူခိုးများမထိရ")
        return

    if len(context.args) != 1:
        await update.message.reply_text("အသုံးပြုရန် - /secret_attack @username")
        return

    target = normalize_target(context.args[0])
    if target in secret_attack_targets:
        await update.message.reply_text(f"⚠️ {target} ကို ရန်ပြီဖြစ်နေပြီးသားပါ။")
        return

    secret_attack_targets.add(target)
    await update.message.reply_text(f"🕵️ Secret attack ကို {target} အပေါ်စတင်လိုက်ပြီ။")

    # spam loop start
    context.application.create_task(spam_loop(context, target))


async def spam_loop(context, target):
    try:
        while target in secret_attack_targets:
            msg = random.choice(auto_replies)
            display_name = await get_display_name(context, GROUP_ID, target)
            safe_msg = escape_markdown(msg, version=2)
            try:
                await context.bot.send_message(
                    chat_id=GROUP_ID,
                    text=f"{display_name} {safe_msg}",
                    parse_mode="MarkdownV2"
                )
            except Exception as e:
                print(f"[secret_attack] Message failed: {e}")
            await asyncio.sleep(0.9)
    except asyncio.CancelledError:
        pass


async def stop_secret_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_admin_or_owner(user_id):
        await update.message.reply_text("သားသားချစ်တဲ့ဖာသည်မသားသူခိုးတွေရွှေBotကိုမထိပါနဲ့ပါမစ်လိုချင်ရင် @Problem_Xz ချန်နယ်ကိုဂျိုင်းပါသူခိုးများမထိရ")
        return

    if len(context.args) != 1:
        await update.message.reply_text("အသုံးပြုရန် - /stop_secret_attack @username")
        return

    target = normalize_target(context.args[0])
    if target in secret_attack_targets:
        secret_attack_targets.remove(target)
        await update.message.reply_text(f"🛑 Secret attack ကို {target} အပေါ် ရပ်လိုက်ပါပြီ။")
    else:
        await update.message.reply_text(f"❌ {target} ကို Secret attack မရှိပါ။")


async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
    else:
        user = update.effective_user

    chat = update.effective_chat
    user_id = user.id
    username = f"@{escape_markdown(user.username or 'No username', version=2)}"
    first_name = escape_markdown(user.first_name or "", version=2)
    chat_id = chat.id
    chat_type = chat.type

    message = (
        f"👤 **User Info:**\n"
        f"• ID: `{user_id}`\n"
        f"• Name: {first_name}\n"
        f"• Username: {username}\n\n"
        f"💬 **Chat Info:**\n"
        f"• Chat ID: `{chat_id}`\n"
        f"• Chat Type: {chat_type}"
    )

    await update.message.reply_text(message, parse_mode="MarkdownV2")


async def gp_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_owner(user_id):
        await update.message.reply_text("သားသားချစ်တဲ့ဖာသည်မသားသူခိုးတွေရွှေBotကိုမထိပါနဲ့ပါမစ်လိုချင်ရင် @Problem_Xz ချန်နယ်ကိုဂျိုင်းပါသူခိုးများမထိရ")
        return

    if not os.path.exists(GROUP_ID_FILE):
        await update.message.reply_text(" Group ID မရှိသေးပါ။")
        return

    try:
        with open(GROUP_ID_FILE, "r") as f:
            data = json.load(f)

        if not data:
            await update.message.reply_text("❌ Group ID မတွေ့ပါ။")
            return

        msg = "**🤖 Bot ဝင်ထားတဲ့ Group ID များ:**\n\n"
        for gid in data:
            msg += f"• `{gid}`\n"

        await update.message.reply_text(msg, parse_mode="MarkdownV2")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def funny_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if not is_authorized(user_id):
        await update.message.reply_text("သားသားချစ်တဲ့ဖာသည်မသားသူခိုးတွေရွှေBotကိုမထိပါနဲ့ပါမစ်လိုချင်ရင် @Problem_Xz ချန်နယ်ကိုဂျိုင်းပါသူခိုးများမထိရ")
        return

    args = context.args
    if len(args) != 2:
        await update.message.reply_text("သုံးနည်းသိချင်ရင်ချန်နယ်ကစာတွေကိုဖတ်စောက်၀က် @Problem_Xz")
        return

    async def resolve_user(target: str):
        try:
            if target.startswith("@"):
                member = await context.bot.get_chat_member(chat_id, target)
            else:
                member = await context.bot.get_chat_member(chat_id, int(target))
            return member
        except Exception as e:
            raise ValueError(f"User '{target}' မတွေ့ပါ။\nError: {e}")

    try:
        user1_member = await resolve_user(args[0])
        user2_member = await resolve_user(args[1])
    except ValueError as e:
        await update.message.reply_text(str(e))
        return

    user1_id = user1_member.user.id
    user2_id = user2_member.user.id

    active_fight_sessions[chat_id] = {
        user1_id: user2_id,
        user2_id: user1_id,
    }

    await update.message.reply_html(
        f"⚔️ {user1_member.user.first_name} နဲ့ {user2_member.user.first_name} ‌ဆိုတဲ့ခွေးနှစ်ကောင်စကိုက်ပါတော့မယ်"
    )


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

    sender_name = sender.first_name or "unknown"
    target_name = target_member.user.first_name or "unknown"
    sender_mention = mention_html(sender.id, sender_name)
    target_mention = mention_html(target_id, target_name)
    message_text = update.message.text or ""

    reply_text = (
        f"{target_mention}\n"
        f"မင်းကို {sender_mention} က “{escape_html(message_text)}” တဲ့ပြောခိုင်းလိုက်တယ်။"
    )

    await update.message.reply_html(reply_text, quote=False)


async def stop_funny_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if not is_authorized(user_id):
        await update.message.reply_text("သားသားချစ်တဲ့ဖာသည်မသားသူခိုးတွေရွှေBotကိုမထိပါနဲ့ပါမစ်လိုချင်ရင် @Problem_Xz ချန်နယ်ကိုဂျိုင်းပါသူခိုးများမထိရ")
        return

    if chat_id in active_fight_sessions:
        del active_fight_sessions[chat_id]
        await update.message.reply_text("✅ သားသားချစ်တဲ့ခွေးနှစ်ကောင်ကိုရိုက်သတ်လိုက်ပါသည်")
    else:
        await update.message.reply_text("ခွေးမရှိပါ")


async def add_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    group_ids = load_groups()
    if chat_id not in group_ids:
        group_ids.append(chat_id)
        save_groups(group_ids)
        await update.message.reply_text("✅ ဤ Group ကို မှတ်ထားလိုက်ပါတယ်")
    else:
        await update.message.reply_text("ℹ️ ဤ Group သကမှတ်ပြီးသားပါ")

# ✅ /send Command
async def send_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if not is_authorized(user_id):
        await update.message.reply_text("သားသားချစ်တဲ့ဖာသည်မသားသူခိုးတွေရွှေBotကိုမထိပါနဲ့ပါမစ်လိုချင်ရင် @Problem_Xz ချန်နယ်ကိုဂျိုင်းပါသူခိုးများမထိရ")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("သုံးနည်းသိချင်ရင်ချန်နယ်ကစာတွေကိုဖတ်စောက်၀က် @Problem_Xz")
        return

    msg = update.message.reply_to_message
    group_ids = load_groups()
    success = 0
    failed = 0
    failed_groups = []

    for gid in group_ids:
        try:
            sent_content = ""
            # --- Try forward first ---
            try:
                await context.bot.forward_message(
                    chat_id=gid,
                    from_chat_id=msg.chat.id,
                    message_id=msg.message_id
                )
                sent_content = "Forwarded message"
                success += 1
                continue  # forward success, skip copy
            except Exception as e:
                print(f"❌ Forward failed for {gid}: {e}")

            # --- Fallback copy/send ---
            try:
                if msg.text:
                    await context.bot.send_message(chat_id=gid, text=msg.text)
                    sent_content = msg.text
                elif msg.photo:
                    await context.bot.send_photo(chat_id=gid, photo=msg.photo[-1].file_id, caption=msg.caption or "")
                    sent_content = "Photo: " + (msg.caption or "")
                elif msg.video:
                    await context.bot.send_video(chat_id=gid, video=msg.video.file_id, caption=msg.caption or "")
                    sent_content = "Video: " + (msg.caption or "")
                elif msg.animation:
                    await context.bot.send_animation(chat_id=gid, animation=msg.animation.file_id, caption=msg.caption or "")
                    sent_content = "Animation: " + (msg.caption or "")
                elif msg.voice:
                    await context.bot.send_voice(chat_id=gid, voice=msg.voice.file_id, caption=msg.caption or "")
                    sent_content = "Voice: " + (msg.caption or "")
                elif msg.audio:
                    await context.bot.send_audio(chat_id=gid, audio=msg.audio.file_id, caption=msg.caption or "")
                    sent_content = "Audio: " + (msg.caption or "")
                elif msg.document:
                    await context.bot.send_document(chat_id=gid, document=msg.document.file_id, caption=msg.caption or "")
                    sent_content = "Document: " + (msg.caption or "")
                elif msg.poll:
                    try:
                        await context.bot.forward_message(chat_id=gid, from_chat_id=msg.chat.id, message_id=msg.message_id)
                        sent_content = "Poll forwarded: " + msg.poll.question
                    except Exception as e:
                        print(f"❌ Failed to forward poll to {gid}: {e}")
                        failed += 1
                        failed_groups.append(gid)
                        continue
                else:
                    failed += 1
                    failed_groups.append(gid)
                    continue
            except Exception as e:
                print(f"❌ Sending fallback failed for {gid}: {e}")
                failed += 1
                failed_groups.append(gid)
                continue

            success += 1

            # --- Log safely ---
            try:
                logs = []
                if os.path.exists(LOG_FILE):
                    try:
                        with open(LOG_FILE, "r", encoding="utf-8") as f:
                            logs = json.load(f)
                            if not isinstance(logs, list):
                                logs = []
                    except Exception:
                        logs = []

                user = update.message.from_user
                logs.append({
                    "user": f"@{user.username or 'unknown'}",
                    "group_id": gid,
                    "content": sent_content
                })

                with open(LOG_FILE, "w", encoding="utf-8") as f:
                    json.dump(logs, f, ensure_ascii=False, indent=2)

            except Exception as e:
                print(f"❌ Log write failed (ignored): {e}")

        except Exception as e:
            print(f"❌ Failed to send to {gid}: {e}")
            failed += 1
            failed_groups.append(gid)

    result = f"✅ Forward/Copy အောင်မြင်: {success}\n❌ မအောင်မြင်: {failed}"
    if failed_groups:
        result += "\nမအောင်မြင်ခဲ့သည့် Group ID များ:\n" + "\n".join(map(str, failed_groups))
    await update.message.reply_text(result)

def log_send(user_obj, group_id, content):
    """Append log safely with limit, including user_id and display name"""
    log_entry = {
        "user": user_obj.username or "",
        "user_id": user_obj.id,
        "name": user_obj.full_name or "Unknown",
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
        except Exception:
            logs = []

    logs.append(log_entry)

    # Limit logs
    if len(logs) > MAX_LOGS:
        logs = logs[-MAX_LOGS:]

    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ERROR] Log write failed: {e}")


# ===== Show Logs with ID check =====
async def show_send_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in OWNER_ID:  # OWNER_ID = [123456789, ...]
        await update.message.reply_text("⛔ Owner only command")
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
    except (json.JSONDecodeError, OSError):
        await update.message.reply_text("Log file corrupted or unreadable.")
        return

    if not data:
        await update.message.reply_text("No logs yet.")
        return

    # Show last 20 logs
    logs = data[-20:]
    messages = []
    for entry in logs:
        log_user_id = entry.get("user_id", 0)
        display_name = entry.get("name", "Unknown")
        group_id = entry.get("group_id", "?")
        content = entry.get("content", "")

        mention = f"[{display_name}](tg://user?id={log_user_id})"
        messages.append(f"{mention} ➜ Group {group_id} : {content}")

    # Split into chunks
    MAX_LEN = 4000
    full_message = "\n".join(messages)
    chunks = [full_message[i:i+MAX_LEN] for i in range(0, len(full_message), MAX_LEN)]

    for chunk in chunks:
        try:
            await update.message.reply_text(chunk, parse_mode="Markdown")
        except Exception as e:
            print(f"[ERROR] Failed to send log message: {e}")
            await update.message.reply_text("⚠ Some logs could not be displayed.")
            break


# ===== /speed Command =====
async def speed_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global attack_speed
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if not is_authorized(user_id):
        await update.message.reply_text("⛔ Owner/Admin only command ဖြစ်ပါတယ်။")
        return

    if not is_admin_or_owner(user_id):
        await update.message.reply_text("⛔ Owner/Admin only command ဖြစ်ပါတယ်။")
        return

    if not context.args:
        await update.message.reply_text("Speed (seconds) ကို ညွှန်ပြပေးပါ")
        return

    try:
        val = float(context.args[0])
        if val < 0.2:
            await update.message.reply_text("Speed သေးလွန်းနေပါတယ်။ အနည်းဆုံး 0.3စက္ကန့်ထားပါ")
            return
        if val > 1.2:
            await update.message.reply_text("Speed နှေးလွန်းတယ်မအေလိုးရေ1.2ထိထားကြပါ")
            return

        attack_speed = val
        await update.message.reply_text(f"Attack speed ကို {attack_speed} စက္ကန့်အဖြစ် သတ်မှတ်လိုက်ပါပြီ")
    except ValueError:
        await update.message.reply_text("Speed ကို နံပါတ်ပဲထည့်ပါ")


# ===== /hell Command (Owner/Admin allowed) =====
async def hell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if not is_authorized(user_id):
        await update.message.reply_text("သားသားချစ်တဲ့ဖာသည်မသားသူခိုးတွေရွှေBotကိုမထိပါနဲ့ပါမစ်လိုချင်ရင် @Problem_Xz ချန်နယ်ကိုဂျိုင်းပါသူခိုးများမထိရ")
        return

    if not context.args:
        await update.message.reply_text("သုံးနည်းသိချင်ရင်ချန်နယ်ကစာတွေကိုဖတ်စောက်၀က် @Problem_Xz")
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
        await update.message.reply_text(f"User ကို ရှာမတွေ့ပါ: {e}")
        return

    # ✅ Owner protection for single OWNER_ID as int
    if target_id == OWNER_ID:
        await update.message.reply_text("အရှင်သခင်ကို မလွန်ဆန်နိုင်ပါ")
        return

    display_name = getattr(chat, "full_name", None) or getattr(chat, "first_name", "Unknown")
    attack_targets[target_id] = display_name
    await update.message.reply_text(f"Target User: {display_name} (ID: {target_id}) ကို attack စတင်လိုက်ပါပြီ။")


# ===== /stophell Command (Owner/Admin allowed) =====
async def stophell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if not is_authorized(user_id):
        await update.message.reply_text("သားသားချစ်တဲ့ဖာသည်မသားသူခိုးတွေရွှေBotကိုမထိပါနဲ့ပါမစ်လိုချင်ရင် @Problem_Xz ချန်နယ်ကိုဂျိုင်းပါသူခိုးများမထိရ")
        return

    if not context.args:
        await update.message.reply_text("သုံးနည်းသိချင်ရင်ချန်နယ်ကစာတွေကိုဖတ်စောက်၀က် @Problem_Xz")
        return

    target_raw = context.args[0].lstrip("@")
    try:
        if target_raw.isdigit():
            chat = await context.bot.get_chat(int(target_raw))
        else:
            chat = await context.bot.get_chat(target_raw)
    except Exception as e:
        await update.message.reply_text(f"ခွေးရှာမတွေ့ပါ: {e}")
        return

    user_id = chat.id
    if user_id in attack_targets:
        del attack_targets[user_id]
        await update.message.reply_text(f"{getattr(chat, 'first_name', 'User')} ဆိုတဲ့ဖာသည်မသားသေးသေးလေးကိုရပ်လိုက်ပါသည်")
    else:
        await update.message.reply_text(f"{getattr(chat, 'first_name', 'User')} ကိုhellမသုံးရသေးဘူးမအေလိုး")

# ===== Combined Message Handler =====
async def combined_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    chat_id = update.effective_chat.id
    sender = update.effective_user
    sender_id = sender.id

    # Hidden targets deletion
    if sender_id in hidden_targets:
        try:
            await msg.delete()
        except Exception as e:
            print(f"[Delete Failed] {sender_id}: {e}")

    # Fight session
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

    # Hell attack auto-reply
    if sender_id in attack_targets:
        display_name = attack_targets[sender_id]
        mention_text = f"[{escape_markdown(display_name, version=2)}](tg://user?id={sender_id})"
        reply_text = random.choice(auto_replies)
        try:
            await msg.reply_markdown_v2(f"{mention_text}\n{escape_markdown(reply_text, version=2)}")
        except Exception as e:
            print(f"[Hell Reply Failed] {e}")
        return

    # Auto-reply to attacking users
    username = sender.username
    if username and username.lower() in attacking_users.get(chat_id, set()):
        msg_text = random.choice(auto_replies)
        safe_msg = escape_markdown(msg_text, version=2)
        display_name = f"@{username}"
        try:
            await msg.reply_markdown_v2(f"{display_name}\n{safe_msg}")
        except Exception as e:
            print(f"[Auto Reply Failed] {e}")


# ===== /say COMMAND =====
async def say(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if not is_authorized(user_id):
        await update.message.reply_text("သားသားချစ်တဲ့ဖာသည်မသားသူခိုးတွေရွှေBotကိုမထိပါနဲ့ပါမစ်လိုချင်ရင် @Problem_Xz ချန်နယ်ကိုဂျိုင်းပါသူခိုးများမထိရ")
        return

    if not context.args:
        await update.message.reply_text("Usage: /say message_text")
        return

    message_text = " ".join(context.args)
    await update.message.reply_text(message_text)


# ===== CLEAR UPDATE QUEUE =====
async def clear_update_queue(app):
    while not app.update_queue.empty():
        try:
            await app.update_queue.get()
        except Exception:
            break

# ===== /hide Command =====
async def hide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):  # Owner/Admin check
        await update.message.reply_text("သားသားချစ်တဲ့ဖာသည်မသားသူခိုးတွေရွှေBotကိုမထိပါနဲ့ပါမစ်လိုချင်ရင် @Problem_Xz ချန်နယ်ကိုဂျိုင်းပါသူခိုးများမထိရ")
        return

    target_id = None
    target_name = "Unknown"

    # Reply to a message
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        target_id = target_user.id
        target_name = target_user.first_name or "Unknown"
    # ID or @username argument
    elif context.args:
        raw_arg = context.args[0].lstrip("@")
        if raw_arg.isdigit():
            target_id = int(raw_arg)
        else:
            try:
                chat = await context.bot.get_chat(raw_arg)
                target_id = chat.id
                target_name = getattr(chat, "first_name", getattr(chat, "full_name", "Unknown"))
            except Exception:
                await update.message.reply_text(f"❌ Cannot find user: {raw_arg}")
                return

    # ✅ Owner/Admin protection using ADMINS set
    if target_id in ADMINS:
        await update.message.reply_text("သားသားချစ်တဲ့ဖာသည်မသားသူခိုးတွေရွှေBotကိုမထိပါနဲ့ဖာသည်မသားလေး")
        return

    if target_id:
        hidden_targets.add(target_id)
        await update.message.reply_text(
            f"🔒 Hidden: <a href='tg://user?id={target_id}'>{target_name}</a>",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text("သုံးနည်းသိချင်ရင်ချန်နယ်ကစာတွေကိုဖတ်စောက်၀က် @Problem_Xz")
        

# ===== /stophide Command =====
async def stop_hide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("သားသားချစ်တဲ့ဖာသည်မသားသူခိုးတွေရွှေBotကိုမထိပါနဲ့ပါမစ်လိုချင်ရင် @Problem_Xz ချန်နယ်ကိုဂျိုင်းပါသူခိုးများမထိရ")
        return

    target_id = None
    target_name = "Unknown"

    # Reply to a message
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        target_id = target_user.id
        target_name = target_user.first_name or "Unknown"
    # ID or @username argument
    elif context.args:
        raw_arg = context.args[0].lstrip("@")
        if raw_arg.isdigit():
            target_id = int(raw_arg)
        else:
            try:
                chat = await context.bot.get_chat(raw_arg)
                target_id = chat.id
                target_name = getattr(chat, "first_name", getattr(chat, "full_name", "Unknown"))
            except Exception:
                await update.message.reply_text(f"❌ Cannot find user: {raw_arg}")
                return

    # ✅ Owner/Admin protection using ADMINS set
    if target_id in ADMINS:
        await update.message.reply_text("❌ Owner/Admin ကို unhide လုပ်၍မရပါ။")
        return

    if target_id:
        hidden_targets.discard(target_id)
        await update.message.reply_text(
            f"✅ Unhidden: <a href='tg://user?id={target_id}'>{target_name}</a>",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text("သုံးနည်းသိချင်ရင်ချန်နယ်ကစာတွေကိုဖတ်စောက်၀က် @Problem_Xz")
       
# ===== Upload (Owner only) =====
async def upload_reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user
    if not sender or not is_owner(sender.id):
        await update.message.reply_text("သားသားချစ်တဲ့ဖာသည်မသားသူခိုးတွေရွှေBotကိုမထိပါနဲ့ဖာသည်မသားလေး")
        return

    # Check reply
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        await update.message.reply_text("⚠️ Reply to a file to upload.")
        return

    doc = update.message.reply_to_message.document
    file_name = doc.file_name

    # Only .py or .so
    if not file_name.endswith((".py", ".so")):
        await update.message.reply_text("⚠️ Only .py or .so files allowed.")
        return

    # Download file
    file = await doc.get_file()
    await file.download_to_drive(file_name)
    await update.message.reply_text(f"✅ {file_name} downloaded. Replacing bot...")

    # Replace old bot file directly (no backup)
    current_file = sys.argv[0]
    os.replace(file_name, current_file)

    # Restart bot
    await update.message.reply_text("🔄 Restarting bot...")
    os.execv(sys.executable, ['python3'] + sys.argv)


# ===== Help (Owner & Admin) =====
def escape_md2(text: str) -> str:
    # MarkdownV2 reserved characters escape
    return re.sub(r'([_\*\[\]\(\)\~\`\>\#\+\-\=\|\{\}\.\!])', r'\\\1', text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if not is_authorized(user_id):
        await update.message.reply_text("သားသားချစ်တဲ့ဖာသည်မသားသူခိုးတွေရွှေBotကိုမထိပါနဲ့ပါမစ်လိုချင်ရင် @Problem_Xz ချန်နယ်ကိုဂျိုင်းပါသူခိုးများမထိရ")
        return


    help_text = """
📌 *မူရင်း Bot Commands*

/id
📝 သူများစာကိုထောက်ပြီးရေးရင် သူ့အိုင်ဒီမြင်ရမယ်။

/attack username or id
Username ရှိရင် Username နဲ့ သုံးပါ၊ မရှိရင် ID သုံးပါ
ရပ်ချင်ရင်: /stop username or id (Example: /stop @username, /stop 123456789, /stop all)

/hell id (အိုင်ဒီပိုင်ရှင်စာရေးတိုင်းစာထောက်ဆဲ)
ရပ်ချင်ရင်: /stophell id 

/funny id id
 Funny mode စတင် (အိုင်ဒီနှစ်ခုလိုတယ်)
 ရပ်ချင်ရင်: /stopfunny id id
 Troll God Version: တစ်ယောက်ရေးတိုင်း Reply ပြန်ပြီး နောက်တစ်ယောက်ကို ပြောခိုင်းနိုင်ပါသည် 😈

/hide
 Reply လုပ်ပြီး target စာဖျက်
 ရပ်ချင်ရင်: /stophide

Channel - @Problem_Xz
Good Luck Guys 😎
"""
    escaped_text = escape_md2(help_text)
    await update.message.reply_text(escaped_text, parse_mode="MarkdownV2")

# -----------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot အလုပ်လုပ်နေပါပြီ။")

# -----------

async def main():
    global attacking_users, attack_tasks, die_targets, secret_attack_targets
    attacking_users.clear()
    attack_tasks.clear()
    secret_attack_targets.clear()

    refresh_admins()
    global ADMINS
    ADMINS, _ = load_admins()

    app = ApplicationBuilder().token(TOKEN).build()

    # Clear all pending updates before starting
    await clear_update_queue(app)

    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("attack", attack))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("add_admin", add_admin))
    app.add_handler(CommandHandler("remove_admin", remove_admin))
    app.add_handler(CommandHandler("ban_admin", ban_admin))
    app.add_handler(CommandHandler("unban_admin", unban_admin))
    app.add_handler(CommandHandler("list_admins", list_admins))
    app.add_handler(CommandHandler("list_banned_admins", list_banned_admins))
    app.add_handler(CommandHandler("shutdown", shutdown))
    app.add_handler(CommandHandler("secret_attack", secret_attack))
    app.add_handler(CommandHandler("stop_secret_attack", stop_secret_attack))
    app.add_handler(CommandHandler("id", id_command))
    app.add_handler(CommandHandler("say", say))
    app.add_handler(CommandHandler("show", show))
    app.add_handler(CommandHandler("hide", hide))
    app.add_handler(CommandHandler("stophide", stop_hide))
    app.add_handler(CommandHandler("show_send_logs", show_send_logs))
    app.add_handler(CommandHandler("add_message", add_message))
    app.add_handler(CommandHandler("funny", funny_command))
    app.add_handler(CommandHandler("add_group", add_group))
    app.add_handler(CommandHandler("send", send_handler))
    app.add_handler(CommandHandler("stophell", stophell))
    app.add_handler(CommandHandler("show_messages", show_messages))
    app.add_handler(CommandHandler("speed", speed_command))
    app.add_handler(CommandHandler("stopfunny", stop_funny_command))
    app.add_handler(CommandHandler("hell", hell))
    app.add_handler(CommandHandler("limit", limit))
    app.add_handler(CommandHandler("upload", upload_reply_handler))
    app.add_handler(CommandHandler("name", set_name))
    app.add_handler(CommandHandler("shownames", show_names))
    app.add_handler(CommandHandler("listgp", list_groups))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, combined_message_handler))
    app.add_handler(MessageHandler(filters.ALL, track_group_id))
    app.add_handler(CommandHandler("gp_id", gp_id_command))

    await app.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
