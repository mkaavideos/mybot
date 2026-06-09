import json
import os

from datetime import time, datetime
from zoneinfo import ZoneInfo

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.environ.get("8282611240:AAF9rp4wj0UPRqiXOmB-PeUU8_SKm5XP_GA")

ADMIN_GROUP_ID = -1004299836917
CHANNEL_ID = -1003979710728
REPORTERS_THREAD_ID = 3
ARCHIVE_THREAD_ID = 6
PRE_PUBLISH_THREAD_ID = 17

ALL_REGIONS = [
    "صور", "برج الشمالي", "العباسية", "الحوش", "البازورية", "عين بعال",
    "صديقين", "قانا", "معركة", "دير قانون رأس العين", "دير قانون النهر",
    "الرمادية","البقاع","بيروت","الضاحية الجنوبية","بعلبك","النبطية"
]

REPORTERS_FILE = "reporters.json"
STATS_FILE = "stats.json"
FORWARDS_FILE = "forwards.json"
DAILY_STATS_FILE = "daily_stats.json"


def load_json_file(file_name, default_data):
    if not os.path.exists(file_name):
        return default_data
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default_data


def save_json_file(file_name, data):
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


reporters = load_json_file(REPORTERS_FILE, {})

stats = load_json_file(STATS_FILE, {
    "reports_received": 0,
    "news_published": 0,
    "regions": {},
    "reporters_count": {},
    "last_activity": {}
})

forwards = load_json_file(FORWARDS_FILE, {})


def save_reporters():
    save_json_file(REPORTERS_FILE, reporters)


def save_stats():
    save_json_file(STATS_FILE, stats)


def save_forwards():
    save_json_file(FORWARDS_FILE, forwards)


def increment_stat(key):
    stats[key] = stats.get(key, 0) + 1
    save_stats()


def increment_region(region):
    if "regions" not in stats:
        stats["regions"] = {}
    stats["regions"][region] = stats["regions"].get(region, 0) + 1
    save_stats()


def increment_reporter(user_id):
    if "reporters_count" not in stats:
        stats["reporters_count"] = {}
    user_id = str(user_id)
    stats["reporters_count"][user_id] = stats["reporters_count"].get(user_id, 0) + 1
    save_stats()


keyboard = ReplyKeyboardMarkup(
    [
        ["🚨 خبر عاجل", "📰 إرسال خبر"],
        ["📞 التواصل مع الإدارة"]
    ],
    resize_keyboard=True
)

publish_keyboard = ReplyKeyboardMarkup(
    [
        ["🚨 عاجل", "🔴 تحديث"],
        ["📸 من المكان", "⚠️ تنويه"],
        ["ℹ️ معلومات"]
    ],
    resize_keyboard=True
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحبًا بكم في منصة البلاغات الخاصة بالبيان الإخباري.\n\n"
        "يمكنكم إرسال الأخبار أو التواصل مع الإدارة.\n\n",
        reply_markup=keyboard
    )


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    status = (
        f"🎖 مراسل معتمد - {reporters.get(str(user.id))}"
        if str(user.id) in reporters
        else "مستخدم عادي"
    )
    await update.message.reply_text(
        f"👤 الاسم: {user.full_name}\n"
        f"🔗 اليوزر: @{user.username if user.username else 'لا يوجد'}\n"
        f"🆔 ID: {user.id}\n"
        f"الحالة: {status}"
    )


async def add_reporter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_GROUP_ID:
        return
    try:
        user_id = context.args[0]
        region = " ".join(context.args[1:])
        if not region:
            await update.message.reply_text("استعمال الأمر:\n/addreporter USER_ID المنطقة")
            return
        reporters[str(user_id)] = region
        save_reporters()
        await update.message.reply_text(f"✅ تم إضافة المراسل.\n\n🆔 {user_id}\n📍 {region}")
    except:
        await update.message.reply_text("استعمال الأمر:\n/addreporter USER_ID المنطقة")


async def remove_reporter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_GROUP_ID:
        return
    try:
        user_id = context.args[0]
        if user_id in reporters:
            del reporters[user_id]
            save_reporters()
        await update.message.reply_text(f"❌ تم حذف المراسل {user_id}")
    except:
        await update.message.reply_text("استعمال الأمر:\n/removereporter USER_ID")


async def list_reporters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_GROUP_ID:
        return
    if not reporters:
        await update.message.reply_text("لا يوجد مراسلون معتمدون.")
        return
    text = "🎖 المراسلون المعتمدون\n\n"
    for reporter_id, region in reporters.items():
        text += f"🆔 {reporter_id}\n📍 {region}\n\n"
    await update.message.reply_text(text)


async def newsroom_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_GROUP_ID:
        return
    text = (
        "📊 إحصائيات غرفة أخبار البيان\n\n"
        f"📨 البلاغات المستلمة: {stats.get('reports_received', 0)}\n"
        f"📰 الأخبار المنشورة: {stats.get('news_published', 0)}\n"
        f"🎖 المراسلون المعتمدون: {len(reporters)}"
    )
    await update.message.reply_text(text)


async def regions_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_GROUP_ID:
        return
    regions = stats.get("regions", {})
    if not regions:
        await update.message.reply_text("لا توجد إحصائيات مناطق حتى الآن.")
        return
    sorted_regions = sorted(regions.items(), key=lambda x: x[1], reverse=True)
    text = "📍 إحصائيات المناطق\n\n"
    for region, count in sorted_regions:
        text += f"• {region}: {count} بلاغ\n"
    await update.message.reply_text(text)


async def top_reporters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_GROUP_ID:
        return
    reporters_count = stats.get("reporters_count", {})
    if not reporters_count:
        await update.message.reply_text("لا توجد إحصائيات للمراسلين حتى الآن.")
        return
    sorted_reporters = sorted(reporters_count.items(), key=lambda x: x[1], reverse=True)
    text = "🏆 ترتيب مراسلي البيان\n\n"
    for index, (reporter_id, count) in enumerate(sorted_reporters, start=1):
        region = reporters.get(str(reporter_id), "منطقة غير محددة")
        medal = "🥇" if index == 1 else "🥈" if index == 2 else "🥉" if index == 3 else "•"
        text += f"{medal} {reporter_id} | {region}\n📨 عدد البلاغات: {count}\n\n"
    await update.message.reply_text(text)


def update_last_activity(user_id):
    if "last_activity" not in stats:
        stats["last_activity"] = {}
    stats["last_activity"][str(user_id)] = datetime.now().isoformat()
    save_stats()


async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message

    if message.text == "🚨 خبر عاجل":
        await message.reply_text(
            "🚨 بلاغ عاجل\n\n"
            "يرجى إرسال المعلومات بالترتيب التالي:\n\n"
            "📍 المكان:\n"
            "📝 ماذا حدث:"
        )
        return

    if message.text == "📰 إرسال خبر":
        await message.reply_text("يرجى كتابة الخبر أو المعلومات التي تريد إيصالها لفريق التحرير.")
        return

    if message.text == "📞 التواصل مع الإدارة":
        await message.reply_text("اكتب رسالتك الآن، وسيتم إرسالها إلى فريق الإدارة.")
        return

    if not message.text:
        await message.reply_text(
            "⚠️ حرصًا على الأمان، يستقبل البوت البلاغات النصية فقط.\n\n"
            "يرجى كتابة البلاغ كنص واضح دون إرسال صور أو فيديوهات أو ملفات."
        )
        return

    increment_stat("reports_received")

    is_reporter = str(user.id) in reporters
    if is_reporter:
        region = reporters[str(user.id)]
        increment_region(region)
        increment_reporter(user.id)
        update_last_activity(user.id)

    forwarded = await context.bot.forward_message(
        chat_id=ADMIN_GROUP_ID,
        from_chat_id=message.chat_id,
        message_id=message.message_id,
        message_thread_id=REPORTERS_THREAD_ID
    )

    forwards[str(forwarded.message_id)] = {
        "user_id": user.id,
        "msg_id": message.message_id
    }
    save_forwards()

    await message.reply_text(
        "✅ تم استلام رسالتكم بنجاح.\n\n"
        "نشكر لكم تواصلكم مع منصة البيان الإخباري. تم تحويل رسالتكم إلى فريق التحرير المختص لمراجعتها والتحقق من المعلومات المرسلة.\n\n"
        "📞 قد يتواصل معكم فريق التحرير عند الحاجة إلى معلومات إضافية.\n\n"
        "شكراً لمساهمتكم في نقل الحقيقة ومواكبة الأحداث.\n\n"
        "📰 فريق البيان الإخباري",
        reply_markup=keyboard
    )


async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if message is None:
        return
    if update.effective_chat.id == ADMIN_GROUP_ID and message.message_thread_id == PRE_PUBLISH_THREAD_ID:
        return
    if not message.reply_to_message:
        return

    reply_to_id = str(message.reply_to_message.message_id)
    if reply_to_id not in forwards:
        return

    user_id = forwards[reply_to_id]["user_id"]
    reply_msg_id = forwards[reply_to_id]["msg_id"]

    try:
        if message.text:
            sent = await context.bot.send_message(
                chat_id=int(user_id),
                text=message.text,
                reply_to_message_id=int(reply_msg_id)
            )
            await message.reply_text(
                "✅ تم إرسال الرد بنجاح.",
                reply_markup=recall_button(user_id, sent.message_id)
            )
            return
        await message.reply_text("⚠️ الردود النصية فقط مفعّلة حاليًا.")
    except Exception as e:
        await message.reply_text(f"❌ حدث خطأ أثناء الإرسال:\n{e}")


def hashtag_place(place):
    place = place.strip()
    if place.startswith("#"):
        return place
    return "#" + place.replace(" ", "_")

def place_with_type(place):
    place = place.strip()

    no_type_places = [
        "الضاحية الجنوبية",
        "الضاحية الجنوبيه"
    ]

    city_places = [
        "صور",
        "صيدا",
        "بيروت",
        "بنت جبيل",
        "النبطية"
    ]

    if place in no_type_places:
        return hashtag_place(place)

    if place in city_places:
        return f"مدينة {hashtag_place(place)}"

    return f"بلدة {hashtag_place(place)}"

def area_name(place):
    areas = {
        "الجنوب": "جنوب لبنان",
        "جنوب لبنان": "جنوب لبنان",
        "البقاع": "البقاع",
        "البقاع الغربي": "البقاع الغربي",
        "البقاع الشرقي": "البقاع الشرقي",
        "شمال لبنان": "شمال لبنان",
        "الشمال": "شمال لبنان",
        "بيروت": "بيروت",
        "الضاحية": "الضاحية الجنوبية",
        "الضاحية الجنوبية": "الضاحية الجنوبية",
        "القطاع الغربي": "القطاع الغربي",
        "القطاع الشرقي": "القطاع الشرقي",
        "منطقة صور": "منطقة صور",
        "قضاء صور": "قضاء صور",
        "منطقة النبطية": "منطقة النبطية",
        "قضاء بنت جبيل": "قضاء بنت جبيل",
        "قضاء مرجعيون": "قضاء مرجعيون",
        "جبل لبنان": "جبل لبنان",
        "عكار": "عكار",
        "الهرمل": "الهرمل",
        "طرابلس": "طرابلس",
        "الساحل": "الساحل اللبناني",
        "الساحل الجنوبي": "الساحل الجنوبي",
        "الساحل الشمالي": "الساحل الشمالي",
        "الحدود الجنوبية": "الحدود الجنوبية",
        "الحدود اللبنانية الفلسطينية": "الحدود اللبنانية الفلسطينية"
    }

    return areas.get(place.strip(), None)

def editor_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✈️ غارة", callback_data="quick:غارة"),
            InlineKeyboardButton("🚁 مسيرة", callback_data="quick:غارة مسيرة")
        ],
        [
            InlineKeyboardButton("🚨 إنذار", callback_data="quick:انذار"),
            InlineKeyboardButton("📢 مراسل البيان", callback_data="quick:مراسل البيان:")
        ],
        [
            InlineKeyboardButton("🚗 سيارة", callback_data="quick:استهداف سيارة"),
            InlineKeyboardButton("🏍 دراجة", callback_data="quick:استهداف دراجة")
        ],
        [
            InlineKeyboardButton("🔥 حريق", callback_data="quick:حريق"),
            InlineKeyboardButton("🛣 قطع طريق", callback_data="quick:قطع طريق")
        ],
        [
            InlineKeyboardButton("📡 تحليق", callback_data="quick:تحليق حربي"),
            InlineKeyboardButton("📰 إعلام", callback_data="quick:")
        ]
    ])

def warning_places_format(places_text):
    places_text = places_text.strip()

    places = [
        p.strip()
        for p in places_text.replace("،", ",").split(",")
        if p.strip()
    ]

    if len(places) > 1:
        return "بلدات " + "، ".join([hashtag_place(p) for p in places])

    place = places[0] if places else places_text
    area = area_name(place)

    if area:
        return area

    return place_with_type(place)

def auto_format_news(text):
    text = text.strip()

    if text.startswith("/publish"):
        text = text.replace("/publish", "", 1).strip()

    if text == "نشاط مسير":
        return "#نشاط_للطيران_المسيّر في أجواء جنوب لبنان"

    if text == "مسيرات بكثافة":
        return "#تحليق_مكثف للطيران المسيّر في أجواء جنوب لبنان"

    # وسائل إعلام إسرائيلية: الخبر
    if text.startswith("وسائل اعلام اسرائيلية:") or text.startswith("وسائل إعلام إسرائيلية:"):
        content = text.split(":", 1)[1].strip()
        return f"📰 #وسائل_إعلام_إسرائيلية:\n{content}"

    # وسائل إعلام محلية: الخبر
    if text.startswith("وسائل اعلام محلية:") or text.startswith("وسائل إعلام محلية:"):
        content = text.split(":", 1)[1].strip()
        return f"📰 #وسائل_إعلام_محلية:\n{content}"

    # وسائل إعلام لبنانية: الخبر
    if text.startswith("وسائل اعلام لبنانية:") or text.startswith("وسائل إعلام لبنانية:"):
        content = text.split(":", 1)[1].strip()
        return f"📰 #وسائل_إعلام_لبنانية:\n{content}"

    if text.startswith("مراسل البيان:") or text.startswith("مراسل البيان الإخباري:"):
        content = text.split(":", 1)[1].strip()
        formatted_content = auto_format_news(content)
        return f"🎙 #مراسل_البيان_الإخباري:\n{formatted_content}"

    # غارة جديدة من مسيرة
    if text.startswith("غارة جديدة من مسيرة"):
        place = text.replace("غارة جديدة من مسيرة", "", 1).strip()
        return f"💥 #غارة جديدة من الطيران المسيّر تســـتهدف {place_with_type(place)}"

    # غارة جديدة مسيرة
    if text.startswith("غارة جديدة مسيرة"):
        place = text.replace("غارة جديدة مسيرة", "", 1).strip()
        return f"💥 #غارة جديدة من الطيران المسيّر تســـتهدف {place_with_type(place)}"

    # غارة مسيرة
    if text.startswith("غارة مسيرة"):
        place = text.replace("غارة مسيرة", "", 1).strip()
        return f"💥 #غارة من الطيران المسيّر تســـتهدف {place_with_type(place)}"

    # مسيرة
    if text.startswith("مسيرة"):
        place = text.replace("مسيرة", "", 1).strip()
        return f"💥 #غارة من الطيران المسيّر تســـتهدف {place_with_type(place)}"

    # غارة جديدة
    if text.startswith("غارة جديدة"):
        place = text.replace("غارة جديدة", "", 1).strip()
        return f"💥⚠️ #غارة جديدة من الطيران الحربي تســـتهدف {place_with_type(place)}"

    # غارة
    if text.startswith("غارة"):
        place = text.replace("غارة", "", 1).strip()
        return f"💥⚠️ #غارة من الطيران الحربي تســـتهدف {place_with_type(place)}"

    # قصف مدفعي / مدفعي
    if text.startswith("قصف مدفعي"):
        place = text.replace("قصف مدفعي", "", 1).strip()
        return f"💥 #قصف_مدفعي يســـتهدف {place_with_type(place)}"

    if text.startswith("مدفعي"):
        place = text.replace("مدفعي", "", 1).strip()
        return f"💥 #قصف_مدفعي يســـتهدف {place_with_type(place)}"
    
        # استهداف سيارة
    if text.startswith("استهداف سيارة"):
        place = text.replace("استهداف سيارة", "", 1).strip()
        return f"💥 #استهداف سيارة في {place_with_type(place)}"

    # استهداف دراجة
    if text.startswith("استهداف دراجة"):
        place = text.replace("استهداف دراجة", "", 1).strip()
        return f"💥 #استهداف دراجة نارية في {place_with_type(place)}"

    # استهداف آلية
    if text.startswith("استهداف آلية") or text.startswith("استهداف الية"):
        place = text.replace("استهداف آلية", "", 1).replace("استهداف الية", "", 1).strip()
        return f"💥 #استهداف آلية في {place_with_type(place)}"

    if text.startswith("انذار") or text.startswith("إنذار"):
        places_text = text.replace("انذار", "", 1).replace("إنذار", "", 1).strip()
        return f"📢 #إنذار_إسرائيلي يطال {warning_places_format(places_text)}"

    # اخلاء / إخلاء
    if text.startswith("اخلاء") or text.startswith("إخلاء"):
        place = text.replace("اخلاء", "", 1).replace("إخلاء", "", 1).strip()
        return f"📢 #إنذار_إخلاء يطال {place_with_type(place)}"

    # قطع طريق
    if text.startswith("قطع طريق"):
        place = text.replace("قطع طريق", "", 1).strip()
        return f"🚧 #قطع_طريق في {place_with_type(place)}"

    # حريق
    if text.startswith("حريق"):
        place = text.replace("حريق", "", 1).strip()
        return f"🔥 #حريق في {place_with_type(place)}"

    # انفجار / إنفجار
    if text.startswith("انفجار") or text.startswith("إنفجار"):
        place = text.replace("انفجار", "", 1).replace("إنفجار", "", 1).strip()
        return f"#انفجار في {place_with_type(place)}"

    # سقوط صاروخ
    if text.startswith("سقوط صاروخ"):
        place = text.replace("سقوط صاروخ", "", 1).strip()
        return f"#سقوط_صاروخ في {place_with_type(place)}"

    # اطلاق نار / إطلاق نار
    if text.startswith("اطلاق نار") or text.startswith("إطلاق نار"):
        place = text.replace("اطلاق نار", "", 1).replace("إطلاق نار", "", 1).strip()
        return f"#إطلاق_نار في {place_with_type(place)}"

    if text.startswith("تحليق حربي"):
        place = text.replace("تحليق حربي", "", 1).strip()

        area = area_name(place)

        if area:
            return f"#تحليق للطيران الحربي فوق {area}"

        return f"#تحليق للطيران الحربي فوق {place_with_type(place)}"

    if text.startswith("تحليق"):
        place = text.replace("تحليق", "", 1).strip()

        area = area_name(place)

        if area:
            return f"#تحليق للطيران المعادي فوق {area}"

        return f"#تحليق للطيران المعادي فوق {place_with_type(place)}"

    # نشاط مسير
    if text.startswith("نشاط مسير"):
        place = text.replace("نشاط مسير", "", 1).strip()

        area = area_name(place)
        if area:
            return f"#نشاط_للطيران_المسيّر فوق {area}"

        return f"#نشاط_للطيران_المسيّر فوق {place_with_type(place)}"

    # تحليق مسير
    if text.startswith("تحليق مسير"):
        place = text.replace("تحليق مسير", "", 1).strip()

        area = area_name(place)
        if area:
            return f"#تحليق_للطيران_المسيّر فوق {area}"

        return f"#تحليق_للطيران_المسيّر فوق {place_with_type(place)}"

    # مسير معادي
    if text.startswith("مسير"):
        place = text.replace("مسير", "", 1).strip()

        area = area_name(place)
        if area:
            return f"#تحليق_للطيران_المسيّر المعادي فوق {area}"

        return f"#تحليق_للطيران_المسيّر المعادي فوق {place_with_type(place)}"

    # مسيرات بكثافة
    if text.startswith("مسيرات"):
        place = text.replace("مسيرات", "", 1).strip()

        area = area_name(place)
        if area:
            return f"#تحليق_مكثف للطيران المسيّر فوق {area}"

        return f"#تحليق_مكثف للطيران المسيّر فوق {place_with_type(place)}"

    # تمشيط
    if text.startswith("تمشيط"):
        place = text.replace("تمشيط", "", 1).strip()
        return f"#تمشيط_بالأسلحة_الرشاشة باتجاه {place_with_type(place)}"

    return text


def preview_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ نشر", callback_data="confirm_publish")],
        [
            InlineKeyboardButton("✏️ تعديل", callback_data="edit_publish"),
            InlineKeyboardButton("❌ إلغاء", callback_data="cancel_publish")
        ]
    ])

async def menu_command(update, context):
    message = update.message

    if update.effective_chat.id != ADMIN_GROUP_ID:
        return

    await message.reply_text(
        "اختر نوع الخبر:",
        reply_markup=editor_menu()
    )

async def send_publish_preview(message, context, final_text):
    context.user_data["pending_publish"] = {
        "type": "text",
        "text": final_text
    }
    await message.reply_text(
        f"📋 معاينة الخبر قبل النشر:\n\n{final_text}",
        reply_markup=preview_buttons()
    )


async def handle_publish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if message is None:
        return
    if update.effective_chat.id != ADMIN_GROUP_ID:
        return

    if message.message_thread_id != PRE_PUBLISH_THREAD_ID:
        return

    if message.text and message.text.startswith("/menu"):
        await message.reply_text(
            "اختر نوع الخبر:",
            reply_markup=editor_menu()
        )
        return

    if context.user_data.get("editing_publish"):
        if not message.text:
            await message.reply_text("⚠️ أرسل التعديل كنص فقط.")
            return
        pending = context.user_data.get("pending_publish")
        if not pending:
            context.user_data["editing_publish"] = False
            await message.reply_text("❌ لا يوجد خبر للتعديل.")
            return
        final_text = auto_format_news(message.text)
        if pending["type"] == "text":
            pending["text"] = final_text
        else:
            pending["caption"] = final_text
        context.user_data["pending_publish"] = pending
        context.user_data["editing_publish"] = False
        await message.reply_text(
            f"📋 المعاينة الجديدة:\n\n{final_text}",
            reply_markup=preview_buttons()
        )
        return

    quick_modes = {
        "✈️ غارة": "غارة",
        "🚁 مسيرة": "غارة مسيرة",
        "🚨 إنذار": "انذار",
        "📢 مراسل البيان": "مراسل البيان:",
        "🚗 سيارة": "استهداف سيارة",
        "🏍 دراجة": "استهداف دراجة",
        "🔥 حريق": "حريق",
        "🛣 قطع طريق": "قطع طريق",
        "📡 تحليق": "تحليق حربي",
        "🎯 استهداف": "استهداف سيارة",
        "📰 إعلام": "وسائل اعلام اسرائيلية:",
        "🔄 تحديث": "تحديث"
    }

    if message.text in quick_modes:
        context.user_data["quick_mode"] = quick_modes[message.text]
        await message.reply_text("اكتب اسم البلدة أو المدينة فقط:")
        return

    quick_mode = context.user_data.get("quick_mode")

    if quick_mode and message.text:
        user_text = message.text.replace("/publish", "", 1).strip()

        final_text = auto_format_news(f"{quick_mode} {user_text}")

        context.user_data["quick_mode"] = None

        await send_publish_preview(message, context, final_text)
        return

    if message.text and message.text.startswith("/publish"):
        news_text = message.text.replace("/publish", "", 1).strip()
        if not news_text:
            await message.reply_text("اكتب الخبر بعد /publish\n\nمثال:\n/publish غارة برج الشمالي")
            return
        final_text = auto_format_news(news_text)
        await send_publish_preview(message, context, final_text)
        return

    if message.text:
        final_text = auto_format_news(message.text)
        await send_publish_preview(message, context, final_text)
        return

    if message.photo:
        caption = message.caption if message.caption else "مشاهد أولية من المكان."
        final_caption = auto_format_news(caption)
        context.user_data["pending_publish"] = {
            "type": "photo",
            "file_id": message.photo[-1].file_id,
            "caption": final_caption
        }
        await message.reply_photo(
            photo=message.photo[-1].file_id,
            caption=f"📋 معاينة الخبر قبل النشر:\n\n{final_caption}",
            reply_markup=preview_buttons()
        )
        return

    if message.video:
        caption = message.caption if message.caption else "مشاهد أولية من المكان."
        final_caption = auto_format_news(caption)
        context.user_data["pending_publish"] = {
            "type": "video",
            "file_id": message.video.file_id,
            "caption": final_caption
        }
        await message.reply_video(
            video=message.video.file_id,
            caption=f"📋 معاينة الخبر قبل النشر:\n\n{final_caption}",
            reply_markup=preview_buttons()
        )
        return

    await message.reply_text("⚠️ نوع الرسالة غير مدعوم للنشر.")


async def edit_publish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["editing_publish"] = True
    await query.message.reply_text("✏️ أرسل النص الجديد للخبر.")


async def publish_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    decision = query.data
    pending = context.user_data.get("pending_publish")

    if not pending:
        await query.edit_message_text("❌ لا يوجد خبر بانتظار النشر.")
        return

    if decision == "cancel_publish":
        if pending["type"] == "text":
            await context.bot.send_message(
                chat_id=ADMIN_GROUP_ID,
                message_thread_id=ARCHIVE_THREAD_ID,
                text=f"🗃 خبر ملغى\n\n{pending['text']}"
            )

        context.user_data["pending_publish"] = None
        context.user_data["publish_mode"] = None
        context.user_data["editing_publish"] = False
        await query.edit_message_text("❌ تم إلغاء النشر ونقل الخبر إلى الأرشيف.")
        return

    try:
        if pending["type"] == "text":
            await context.bot.send_message(chat_id=CHANNEL_ID, text=pending["text"])
            increment_daily_stat(pending["text"])
        elif pending["type"] == "photo":
            await context.bot.send_photo(chat_id=CHANNEL_ID, photo=pending["file_id"], caption=pending["caption"])
        elif pending["type"] == "video":
            await context.bot.send_video(chat_id=CHANNEL_ID, video=pending["file_id"], caption=pending["caption"])

        increment_stat("news_published")
        if pending["type"] == "text":
            await context.bot.send_message(
                chat_id=ADMIN_GROUP_ID,
                message_thread_id=ARCHIVE_THREAD_ID,
                text=f"✅ خبر منشور\n\n{pending['text']}"
            )
        context.user_data["pending_publish"] = None
        context.user_data["editing_publish"] = False
        await query.edit_message_text("✅ تم نشر الخبر في قناة البيان.")

    except Exception as e:
        await query.edit_message_text(f"❌ حدث خطأ أثناء النشر:\n{e}")


async def send_daily_stats(context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📊 التقرير اليومي لغرفة أخبار البيان\n\n"
        f"📨 البلاغات المستلمة: {stats.get('reports_received', 0)}\n"
        f"📰 الأخبار المنشورة: {stats.get('news_published', 0)}\n"
        f"🎖 المراسلون المعتمدون: {len(reporters)}\n\n"
        "🕛 تم إرسال هذا التقرير تلقائيًا."
    )
    await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=text)
    stats["reports_received"] = 0
    stats["news_published"] = 0
    save_stats()


async def request_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_GROUP_ID:
        return
    if not context.args:
        await update.message.reply_text("استعمال الأمر:\n/request اسم المنطقة")
        return
    region_name = " ".join(context.args)
    sent_count = 0
    for reporter_id, reporter_region in reporters.items():
        if reporter_region == region_name:
            try:
                await context.bot.send_message(
                    chat_id=int(reporter_id),
                    text=(
                        "🚨 طلب عاجل من غرفة أخبار البيان\n\n"
                        f"📍 المنطقة: {region_name}\n\n"
                        "يرجى تزويدنا بأي معلومات ميدانية متوفرة، أو تفاصيل دقيقة حول المستجدات في منطقتكم.\n\n"
                        "شكراً لتعاونكم.\n"
                        "📰 فريق البيان الإخباري"
                    )
                )
                sent_count += 1
            except Exception as e:
                print(f"Error sending to {reporter_id}: {e}")
    await update.message.reply_text(f"✅ تم إرسال الطلب إلى {sent_count} مراسل/مراسلين في منطقة: {region_name}")


async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_GROUP_ID:
        return
    if not context.args:
        await update.message.reply_text("استعمال الأمر:\n/broadcast نص الرسالة")
        return
    broadcast_text = " ".join(context.args)
    sent_count = 0
    for reporter_id in reporters.keys():
        try:
            await context.bot.send_message(
                chat_id=int(reporter_id),
                text=(
                    "📢 رسالة من غرفة أخبار البيان\n\n"
                    f"{broadcast_text}\n\n"
                    "📰 البيان الإخباري"
                )
            )
            sent_count += 1
        except Exception as e:
            print(f"Broadcast error: {e}")
    await update.message.reply_text(f"✅ تم إرسال الرسالة إلى {sent_count} مراسل.")


async def reporter_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_GROUP_ID:
        return
    if not context.args:
        await update.message.reply_text("استعمال الأمر:\n/repinfo USER_ID")
        return
    reporter_id = context.args[0]
    if reporter_id not in reporters:
        await update.message.reply_text("❌ هذا المراسل غير موجود.")
        return
    region = reporters.get(reporter_id, "غير محددة")
    reporters_count = stats.get("reporters_count", {})
    count = reporters_count.get(reporter_id, 0)
    total_reports = max(stats.get("reports_received", 0), 1)
    percentage = round((count / total_reports) * 100, 1)
    if count >= 60:
        rank = "💎 مراسل ماسي"
    elif count >= 30:
        rank = "🥇 مراسل ذهبي"
    elif count >= 10:
        rank = "🥈 مراسل فضي"
    else:
        rank = "🥉 مراسل برونزي"
    text = (
        "🎖 بطاقة المراسل\n\n"
        f"🆔 ID: {reporter_id}\n"
        f"📍 المنطقة: {region}\n"
        f"📨 عدد البلاغات: {count}\n"
        f"🏅 الرتبة: {rank}\n"
        f"📊 نسبة المساهمة:\n"
        f"{percentage}% من إجمالي البلاغات"
    )
    await update.message.reply_text(text)


async def active_reporters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_GROUP_ID:
        return
    activities = stats.get("last_activity", {})
    if not activities:
        await update.message.reply_text("لا يوجد نشاط للمراسلين حتى الآن.")
        return
    text = "👥 المراسلون النشطون\n\n"
    now = datetime.now()
    for reporter_id, last_time in activities.items():
        region = reporters.get(reporter_id, "غير محددة")
        try:
            last_dt = datetime.fromisoformat(last_time)
            minutes = int((now - last_dt).total_seconds() / 60)
            if minutes < 60:
                status = f"🟢 منذ {minutes} دقيقة"
            elif minutes < 1440:
                status = f"🟡 منذ {minutes // 60} ساعة"
            else:
                status = f"🔴 منذ {minutes // 1440} يوم"
        except:
            status = "غير معروف"
        text += f"📍 {region}\n{status}\n\n"
    await update.message.reply_text(text)


async def coverage_map(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_GROUP_ID:
        return
    coverage = {region: 0 for region in ALL_REGIONS}
    for reporter_id, region in reporters.items():
        coverage[region] = coverage.get(region, 0) + 1
    text = "📍 خريطة تغطية مراسلي البيان\n\n"
    for region, count in coverage.items():
        status = "🟢" if count >= 2 else "🟡" if count == 1 else "🔴"
        text += f"{status} {region}: {count} مراسل\n"
    text += "\n🟢 تغطية جيدة\n🟡 تغطية ضعيفة\n🔴 لا يوجد مراسلون"
    await update.message.reply_text(text)


async def threadid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    thread_id = update.message.message_thread_id
    await update.message.reply_text(f"CHAT ID: {chat_id}\nTHREAD ID: {thread_id}")


def recall_button(user_id, sent_message_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🗑 استرداد الرسالة", callback_data=f"recall:{user_id}:{sent_message_id}")]
    ])


async def recall_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        _, user_id, sent_message_id = query.data.split(":")
        await context.bot.delete_message(chat_id=int(user_id), message_id=int(sent_message_id))
        await query.edit_message_text("🗑 تم استرداد الرسالة بنجاح.")
    except Exception as e:
        await query.edit_message_text(f"❌ تعذر استرداد الرسالة:\n{e}")

async def quick_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    mode = query.data.split(":", 1)[1]

    if mode:
        context.user_data["quick_mode"] = mode
        await query.message.reply_text("اكتب اسم البلدة أو المدينة أو نص الخبر:")
    else:
        context.user_data["quick_mode"] = None
        await query.message.reply_text("اكتب الخبر كما تريد نشره:")

async def report_command(update, context):
    stats = load_daily_stats()

    report = (
        "📊 تقرير اليوم\n\n"
        f"✈️ الغارات: {stats['airstrikes']}\n"
        f"🚁 المسيرات: {stats['drones']}\n"
        f"💥 القصف المدفعي: {stats['artillery']}\n"
        f"📢 الإنذارات: {stats['warnings']}\n"
        f"🚗 استهداف السيارات: {stats['cars']}\n"
        f"🔥 الحرائق: {stats['fires']}"
    )

    await update.message.reply_text(report)

def load_daily_stats():
    try:
        with open(DAILY_STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "airstrikes": 0,
            "drones": 0,
            "artillery": 0,
            "warnings": 0,
            "cars": 0,
            "fires": 0
        }


def save_daily_stats(stats):
    with open(DAILY_STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=4)

def increment_daily_stat(news_text):
    stats = load_daily_stats()

    if "#غارة" in news_text:
        stats["airstrikes"] += 1

    elif "#قصف_مدفعي" in news_text:
        stats["artillery"] += 1

    elif "#إنذار_إسرائيلي" in news_text:
        stats["warnings"] += 1

    elif "#استهداف_سيارة" in news_text:
        stats["cars"] += 1

    elif "#حريق" in news_text:
        stats["fires"] += 1

    if "#الطيران_المسيّر" in news_text or "#نشاط_للطيران_المسيّر" in news_text:
        stats["drones"] += 1

    save_daily_stats(stats)

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("threadid", threadid))
    app.add_handler(CommandHandler("addreporter", add_reporter))
    app.add_handler(CommandHandler("removereporter", remove_reporter))
    app.add_handler(CommandHandler("reporters", list_reporters))
    app.add_handler(CommandHandler("stats", newsroom_stats))
    app.add_handler(CommandHandler("regions", regions_stats))
    app.add_handler(CommandHandler("topreporters", top_reporters))
    app.add_handler(CommandHandler("repinfo", reporter_info))
    app.add_handler(CommandHandler("request", request_region))
    app.add_handler(CommandHandler("broadcast", broadcast_message))
    app.add_handler(CommandHandler("active", active_reporters))
    app.add_handler(CommandHandler("coverage", coverage_map))
    app.add_handler(CommandHandler("report", report_command))
    app.add_handler(CommandHandler("menu", menu_command, filters.Chat(ADMIN_GROUP_ID)))

    app.add_handler(CallbackQueryHandler(recall_message, pattern="^recall:"))
    app.add_handler(CallbackQueryHandler(quick_menu_callback, pattern="^quick:"))
    app.add_handler(CallbackQueryHandler(publish_decision, pattern="^(confirm_publish|cancel_publish)$"))
    app.add_handler(CallbackQueryHandler(edit_publish, pattern="^edit_publish$"))

    app.add_handler(
        MessageHandler(filters.Chat(ADMIN_GROUP_ID) & filters.UpdateType.MESSAGE, handle_publish),
        group=0
    )

    app.add_handler(
        MessageHandler(filters.ChatType.GROUPS & filters.REPLY, handle_admin_reply),
        group=1
    )

    app.add_handler(
        MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, handle_private_message),
        group=0
    )

    print("Bot is running...")

    app.job_queue.run_daily(
        send_daily_stats,
        time=time(hour=23, minute=59, tzinfo=ZoneInfo("Asia/Beirut"))
    )

    app.run_polling()


if __name__ == "__main__":
    main()
