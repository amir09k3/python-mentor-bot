# src/bot.py
import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
# --- Importهای سفارشی ---
from src.models.database import (
    init_db, add_user, get_user, update_user_level,
    add_submission, get_user_profile, get_leaderboard
)
from src.utils.code_runner import run_code_safely
from src.utils.exercise_evaluator import evaluate_exercise
from src.utils.code_quality import analyze_code_quality
from src.utils.knowledge_base import understand_and_respond
from src.utils.ai_engine import query_llama3



# --- راهنمایی‌های آموزشی برای هر تمرین ---
HINTS = {
    1: "💡 راهنمایی: تابعی به نام add(a, b) بنویسید که دو پارامتر بگیرد و حاصل‌جمع آن‌ها را return کند.",
    2: "💡 راهنمایی: از دستور if برای مقایسه سه عدد استفاده کنید. می‌توانید از تابع داخلی max(a, b) هم کمک بگیرید.",
    3: "💡 راهنمایی: با حلقه for از ۱ تا n ضرب کنید. فراموش نکنید که fact(0) = 1 است!",
    4: "💡 راهنمایی: از حلقه for و اندیس معکوس (s[i] با i از آخر به اول) استفاده کنید.",
    5: "💡 راهنمایی: دو شرط پایه دارد: fib(0) = 0 و fib(1) = 1. بقیه با فراخوانی بازگشتی محاسبه می‌شوند.",
    6: "💡 راهنمایی: ابتدا مجموع لیست را با sum(lst) پیدا کنید، سپس تقسیم بر تعداد (len(lst)).",
    7: "💡 راهنمایی: از یک لیست جدید و حلقه استفاده کنید. قبل از اضافه کردن، چک کنید که عنصر قبلاً وجود ندارد.",
    8: "💡 راهنمایی: دو حلقه تو در تو نیاز دارید. در هر تکرار، بزرگ‌ترین عنصر به انتهای لیست منتقل می‌شود.",
    9: "💡 راهنمایی: لیست باید مرتب باشد. ابتدا وسط لیست را پیدا کنید، سپس با مقدار مورد نظر مقایسه کنید.",
    10: "💡 راهنمایی: فرمول ریاضی: حداقل تعداد حرکت = 2^n - 1. پس تابع شما فقط محاسبه این فرمول است!"
}

# --- Import ارزیاب تمرین ---
from src.utils.exercise_evaluator import evaluate_exercise
from src.models.database import (
    init_db, add_user, get_user, update_user_level,
    add_submission, get_user_profile, get_leaderboard
)
import json

# --- Import موتور اجرای کد ---
from src.utils.code_runner import run_code_safely

# --- Import لایه داده ---
from src.models.database import init_db, add_user, get_user

# --- تنظیمات ---
load_dotenv()  # بارگذاری .env
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("❌ خطای جدی: BOT_TOKEN در فایل .env یافت نشد!")

# تنظیم لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- هندلرها ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(
        user_id=user.id,
        first_name=user.first_name or "",
        username=user.username or ""
    )
    
    msg = (
        "سلام {}! 🐍\n"
        "من «ربات آموزشی پایتون» هستم.\n"
        "کد پایتونت رو بفرست تا برات اجراش کنم و بازخورد بدم!\n\n"
        "📊 پروفایل شما ذخیره شد: ID={}"
    ).format(user.first_name or 'دوست عزیز', user.id)
    
    await update.message.reply_text(msg)

async def handle_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    
    # اگر کاربر در حال انجام تمرین است
    if context.user_data.get("awaiting_exercise") == 1:
        del context.user_data["awaiting_exercise"]
        
        # دریافت تست‌کیس تمرین ۱ (ثابت برای سادگی)
        test_cases = json.dumps([
            {"input": [2, 3], "expected": 5},
            {"input": [0, 0], "expected": 0},
            {"input": [-1, 1], "expected": 0},
            {"input": [100, -50], "expected": 50}
        ])
        
        result = evaluate_exercise(code, test_cases, exercise_id=1)  # بعداً exercise_id پویا می‌شه
        
        if "error" in result:
            msg = f"❌ خطا در تمرین:\n{result['error']}"
        else:
            score = result["score"]
            total = result["total"]
            percentage = (score / total) * 100
            
            # ذخیره سابقه (ساده‌شده)
            msg = (
                f"📊 نتیجه تمرین «جمع دو عدد»:\n"
                f"✅ قبول: {score}/{total}\n"
                f"📈 درصد: {percentage:.0f}%\n"
            )
            if result["failed"]:
                msg += "\n🔴 موارد نادرست:"
                for f in result["failed"]:
                    if "error" in f:
                        msg += f"\n  مورد {f['case']}: خطا → {f['error']}"
                    else:
                        msg += f"\n  مورد {f['case']}: ورودی {f['input']} → انتظار {f['expected']}, دریافت {f['got']}"
            
            # امتیازدهی و به‌روزرسانی سطح
            if score == total:
                update_user_level(user_id, "beginner", exp=10)
                msg += "\n\n🎉 تبریک! 10 امتیاز دریافت کردی."
        
        # ذخیره سابقه (فقط اگر تمرین بود)
            exercise_id = context.user_data.get("awaiting_exercise")
            if exercise_id:
                is_correct = (score == total)
                add_submission(
                    user_id=update.effective_user.id,
                    exercise_id=exercise_id,
                    code=code,
                    is_correct=is_correct,
                    score=score
                )
        
        await update.message.reply_text(msg)
        return
    
    if len(code) < 3:
        await update.message.reply_text("⚠️ کد خیلی کوتاه است! لطفاً حداقل یک دستور کامل وارد کنید.")
        return
    
   # --- درک هوشمند متن (فقط اگر کد نیست) ---
    if not code.strip().startswith(("def ", "for ", "while ", "print(", "import ")):
        from utils.knowledge_base import understand_and_respond
        response = understand_and_respond(code)
        if response:
            await update.message.reply_text(
                "🧠 پاسخ هوشمند:\n" + response,
                parse_mode="Markdown"
            )
            return 
    
    # اجرای ایمن کد
    result = run_code_safely(code)
    
    if result["success"]:
        output = result["output"] or "کد بدون خطا اجرا شد (اما خروجی‌ای تولید نکرد)."
        msg = f"""✅ خروجی:
        {output}
        """
    else:
        error = result["error"] or "خطای نامشخصی رخ داد."
        msg = f"""❌ خطا:
        {error} 
        """
    
    # ارسال پیام (با پشتیبانی برای فرمت‌بندی)
    try:
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception:
        # اگر فرمت کد مشکل داشت، بدون فرمت بفرست
        clean_msg = msg.replace("`", "").replace("✅", "").replace("❌", "").strip()
        await update.message.reply_text(clean_msg)
        
   # --- تحلیل کیفیت کد (فقط برای کدهای موفق) ---
        if result.get("success", False) or "def " in code:
            quality = analyze_code_quality(code)
            if "error" not in quality:
                q_msg = "📝 گزارش کیفیت کد:\n"
                
                # نمره
                q_msg += f"⭐ نمره سبک‌کدنویسی: {quality['score']}/10\n\n"
                
                # هشدارها
                if quality["warnings"]:
                    q_msg += "⚠️ هشدارها:\n" + "\n".join(quality["warnings"][:3]) + "\n\n"
                if quality["conventions"]:
                    q_msg += "📌 پیشنهادات:\n" + "\n".join(quality["conventions"][:2]) + "\n\n"
                if quality["refactor"]:
                    q_msg += "🔧 پیشنهادات بازسازی:\n" + "\n".join(quality["refactor"][:2])
                
                if quality["error_count"] == 0 and quality["score"] >= 9.0:
                    q_msg += "\n\n✅ کد شما از نظر سبک بسیار عالی است!"
                
                # ارسال گزارش کیفیت
                try:
                    await update.message.reply_text(q_msg)
                except:
                    # fallback ساده‌تر
                    simple_msg = f"⭐ نمره سبک: {quality['score']}/10"
                    if quality["warnings"]: simple_msg += f"\n⚠️ {len(quality['warnings'])} هشدار"
                    await update.message.reply_text(simple_msg)     
        
async def exercise_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        # نمایش لیست کامل
        msg = (
            "📚 ۱۰ تمرین آموزشی (طبق سرفصل دانشگاه):\n\n"
            "✅ ساده (۴):\n"
            "1. جمع دو عدد\n"
            "2. بیشینه سه عدد\n"
            "3. فاکتوریل (تکراری)\n"
            "4. معکوس رشته\n\n"
            "🟡 متوسط (۳):\n"
            "5. فیبوناچی (بازگشتی)\n"
            "6. میانگین لیست\n"
            "7. حذف تکراری‌ها\n\n"
            "🔴 سخت (۳):\n"
            "8. مرتب‌سازی حبابی\n"
            "9. جستجوی دودویی\n"
            "10. برج هانوی\n\n"
            "📌 شروع: /exercise [شماره]\n"
            "مثال: /exercise 5"
        )
        await update.message.reply_text(msg)
        return

    if not args[0].isdigit():
        await update.message.reply_text("❌ لطفاً فقط عدد تمرین را وارد کنید.")
        return

    ex_id = int(args[0])
    if ex_id < 1 or ex_id > 10:
        await update.message.reply_text("❌ شماره تمرین باید بین ۱ تا ۱۰ باشد.")
        return

    # توضیحات ثابت (برای سادگی — در آینده از دیتابیس خوانده می‌شه)
    descriptions = {
        1: "تابعی به نام add(a, b) بنویسید که دو عدد را جمع کند.\nمثال: add(2, 3) → 5",
        2: "تابع max3(a, b, c) که بزرگ‌ترین سه عدد را برمی‌گرداند.",
        3: "تابع fact(n) با حلقه (n ≥ 0). مثال: fact(5) → 120",
        4: "تابع reverse(s) بدون استفاده از s[::-1].",
        5: "تابع بازگشتی fib(n). مثال: fib(5) → 5",
        6: "تابع average(lst) برای میانگین اعداد لیست.",
        7: "تابع unique(lst) برای حذف تکراری‌ها (ترتیب حفظ شود).",
        8: "تابع bubble_sort(lst) برای مرتب‌سازی لیست.",
        9: "تابع binary_search(lst, x) که اندیس x را برمی‌گرداند (یا -1).",
        10: "تابع hanoi(n) که حداقل تعداد حرکت برج هانوی را برمی‌گرداند (2^n - 1)."
    }

    title = [
        "جمع دو عدد", "بیشینه سه عدد", "فاکتوریل", "معکوس رشته",
        "فیبوناچی", "میانگین لیست", "حذف تکراری‌ها",
        "مرتب‌سازی حبابی", "جستجوی دودویی", "برج هانوی"
    ][ex_id - 1]

    await update.message.reply_text(
        f"🎯 تمرین {ex_id}: {title}\n\n{descriptions[ex_id]}\n\n"
        "💡 کد تابع را ارسال کنید (فقط تعریف تابع، نه فراخوانی)."
    )
    context.user_data["awaiting_exercise"] = ex_id
 
async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    profile = get_user_profile(user_id)
    
    if not profile:
        await update.message.reply_text("❌ ابتدا با /start ثبت‌نام کنید.")
        return

    # محاسبه درصد موفقیت
    total = profile["total_submissions"]
    correct = profile["correct_submissions"]
    success_rate = (correct / total * 100) if total > 0 else 0

    msg = (
        f"📊 پروفایل شما:\n\n"
        f"نام: {profile['first_name'] or '---'}\n"
        f"سطح: {profile['level']}\n"
        f"امتیاز: {profile['experience']}\n"
        f"عضویت: {profile['join_date']}\n\n"
        f"📈 آمار تمرین‌ها:\n"
        f"ارسال‌ها: {total}\n"
        f"موفق: {correct} ({success_rate:.0f}%)\n"
        f"امتیاز کسب‌شده: {profile['total_score']}"
    )
    await update.message.reply_text(msg) 
 
async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /help — نمایش راهنمای کامل"""
    msg = (
        "🤖 راهنمای ربات آموزشی پایتون\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔹 دستورات اصلی:\n"
        "/start — شروع مجدد و ثبت‌نام\n"
        "/exercise [شماره] — شروع تمرین (مثال: /exercise 1)\n"
        "/profile — مشاهده امتیاز و آمار شما\n"
        "/leaderboard — جدول رده‌بندی کاربران\n"
        "/help — نمایش این راهنما\n"
        "/hint — دریافت راهنمایی برای تمرین جاری\n\n"
        "🔹 دستورات هوشمند:\n"
        "/ask [سوال] — پاسخ به سوالات مفهومی پایتون\n"
        "   مثال: /ask تفاوت list و tuple چیه؟\n"
        "   مثال: /ask کد فاکتوریل بازگشتی\n\n"
        "/ai [سوال] — پرسش از استاد مجازی (Llama 3)\n"
        "   پاسخ‌های پیشرفته و دانشگاهی\n"
        "   مثال: /ai چطوری می‌تونم یه decorator بنویسم؟\n\n"
        "🔹 نحوه استفاده:\n"
        "۱. ابتدا /start بزنید\n"
        "۲. سپس /exercise [شماره] برای انتخاب تمرین\n"
        "۳. کد تابع خود را ارسال کنید (فقط تعریف تابع)\n"
        "۴. نتیجه و بازخورد را دریافت کنید\n\n"
        "✅ نکته: کدهای شما در محیطی ایمن اجرا می‌شوند."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")
 
async def hint_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /hint — دریافت راهنمایی برای تمرین جاری"""
    exercise_id = context.user_data.get("awaiting_exercise")
    
    if not exercise_id:
        await update.message.reply_text(
            "ℹ️ راهنمایی فقط هنگام انجام یک تمرین فعال است.\n"
            "ابتدا با /exercise [شماره] تمرینی را شروع کنید."
        )
        return

    hint = HINTS.get(exercise_id, "راهنمایی برای این تمرین در دسترس نیست.")
    await update.message.reply_text(hint)
 
async def leaderboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    leaderboard = get_leaderboard(5)
    if not leaderboard:
        await update.message.reply_text("هنوز کاربری فعالیت نکرده است.")
        return

    msg = "🏆 جدول رده‌بندی (برترین‌ها):\n\n"
    for i, (uid, name, username, exp) in enumerate(leaderboard, 1):
        name_disp = name or (username or f"user{uid}")
        msg += f"{i}. {name_disp} — {exp} امتیاز\n"
    
    await update.message.reply_text(msg)
    
async def ask_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /ask — پرسش از ربات"""
    if not context.args:
        await update.message.reply_text(
            "❓ نحوه استفاده: /ask [سوال]\n"
            "مثال:\n"
            "/ask تفاوت list و tuple چیه؟\n"
            "/ask کد فاکتوریل بازگشتی"
        )
        return
    
    question = " ".join(context.args)
    answer = get_answer(question)
    await update.message.reply_text(answer, parse_mode="Markdown")  
    
    
async def ai_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /ai — پرسش از هوش مصنوعی"""
    if not context.args:
        await update.message.reply_text(
            "🧠 دستور /ai — پرسش از استاد مجازی Llama 3\n\n"
            "مثال:\n"
            "/ai چطوری می‌تونم یه کلاس در پایتون تعریف کنم؟\n"
            "/ai تفاوت init و new چیه؟"
        )
        return
    
    question = " ".join(context.args)
    await update.message.reply_text("⏳ در حال پردازش با Llama 3...")
    
    answer = query_llama3(question)
    await update.message.reply_text(
        f"🤖 پاسخ Llama 3:\n\n{answer}",
        parse_mode="Markdown"
    )  
        
# --- راه‌اندازی ---
def main():
    logger.info("🚀 راه‌اندازی ربات...")
    init_db()  # ✅ ایجاد/باز کردن پایگاه داده
    # ... بقیه کد
    app = Application.builder().token(BOT_TOKEN).build()

    # ثبت هندلرها
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("exercise", exercise_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_code))
    app.add_handler(CommandHandler("profile", profile_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("hint", hint_handler))
    app.add_handler(CommandHandler("leaderboard", leaderboard_handler))
    app.add_handler(CommandHandler("ask", ask_handler))
    app.add_handler(CommandHandler("ai", ai_handler))

    logger.info("✅ ربات آماده است. در حال اتصال به تلگرام...")
    app.run_polling()

if __name__ == "__main__":
    main()
    
