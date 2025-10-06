import os
import logging
import requests
import json
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== إعدادات البوت ==========
TOKEN = '8376293916:AAEgNYjz2-3DBWj4GU0P_LcPkwAjCi_vhsE'

# Google Gemini API Key (ضعه في متغيرات البيئة في Render)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'YOUR_KEY_HERE')
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-1.5-flash')

# Hadith API
HADITH_API_BASE = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1"

# ========== دوال الذكاء الاصطناعي ==========

def ai_understand_query(user_message):
    """استخدام Gemini لفهم الاستفسار واستخراج الكلمات المفتاحية"""
    try:
        prompt = f"""
أنت مساعد ذكي متخصص في فهم الاستفسارات الإسلامية.

رسالة المستخدم: "{user_message}"

مهمتك:
1. فهم المعنى العام للرسالة
2. استخراج 3-5 كلمات مفتاحية للبحث في الأحاديث
3. إضافة كلمات مشابهة ومرادفات

أرجع JSON فقط بهذا الشكل:
{{
  "keywords": ["كلمة1", "كلمة2", "كلمة3"],
  "intent": "وصف قصير للمقصد"
}}

لا تضف أي شرح، فقط JSON.
"""
        
        response = gemini_model.generate_content(prompt)
        result_text = response.text.strip()
        
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].strip()
        
        data = json.loads(result_text)
        return data

        
    except Exception as e:
        logger.error(f"خطأ في Gemini: {e}")
        return {"keywords": [user_message], "intent": "بحث مباشر"}

def search_hadiths(keywords, max_results=3):
    """البحث في الأحاديث باستخدام الكلمات المفتاحية"""
    try:
        results = []
        
        # تحميل صحيح البخاري
        bukhari_url = f"{HADITH_API_BASE}/editions/ara-sahihbukhari.json"
        response = requests.get(bukhari_url, timeout=15)
        
        if response.status_code == 200:
            bukhari_data = response.json()
            hadiths = bukhari_data.get('hadiths', [])
            
            # البحث في الأحاديث
            for hadith in hadiths:
                hadith_text = hadith.get('text', '').lower()
                
                # تحقق من وجود أي من الكلمات المفتاحية
                found = any(
    keyword.lower().replace('ة', 'ه').replace('أ', 'ا').replace('إ', 'ا') in 
    hadith_text.replace('ة', 'ه').replace('أ', 'ا').replace('إ', 'ا')
    for keyword in keywords if keyword
)
                
                if found:
                    results.append({
                        'text': hadith.get('text', ''),
                        'reference': 'صحيح البخاري',
                        'number': hadith.get('hadithnumber', 'غير محدد')
                    })
                    
                    if len(results) >= max_results:
                        break
        
        return results
        
    except Exception as e:
        logger.error(f"خطأ في البحث: {e}")
        return []

def ai_explain_hadith(hadith_text, user_query):
    """استخدام Gemini لشرح الحديث بطريقة مبسطة"""
    try:
        prompt = f"""
أنت عالم حديث متخصص.

سؤال المستخدم: "{user_query}"
نص الحديث: "{hadith_text}"

قدم شرحاً مختصراً (3 أسطر فقط):
1. معنى الحديث
2. علاقته بسؤال المستخدم

كن مختصراً وواضحاً.
"""
        
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        logger.error(f"خطأ في الشرح: {e}")
        return "الحديث متعلق بموضوع بحثك."

# ========== دوال البوت ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رد على أمر /start"""
    user = update.effective_user
    welcome_message = f"""
🌟 أهلا بك أخي الكريم / أختي الكريمة {user.first_name}

📖 هذا البوت مخصص للبحث عن الأحاديث النبوية إما عن طريق النص المطابق أو المعنى، قم بإرسال أي كلمة أو طلب وسوف أقوم بالرد عليك

🤖 **مدعوم بالذكاء الاصطناعي Google Gemini**

✨ **أمثلة للتجربة:**
• الصلاة
• أحاديث عن بر الوالدين
• ما فضل الصدقة؟

📝 استخدم /help لرؤية الأوامر

🔍 ابدأ الآن بإرسال أي سؤال أو كلمة
    """
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رد على أمر /help"""
    help_text = """
🤖 **الباحث الحديثي الذكي**

📋 **الأوامر:**
/start - بدء المحادثة
/help - عرض المساعدة
/about - معلومات عن البوت

🔍 **كيفية الاستخدام:**
فقط أرسل سؤالك أو الكلمة التي تريد البحث عنها

💡 **أمثلة:**
• الصبر
• أحاديث عن الرحمة
• ما قال الرسول عن العلم؟

🧠 **التقنيات:**
• Google Gemini AI - للفهم والشرح
• Hadith API - قاعدة بيانات الأحاديث
• بحث ذكي في صحيح البخاري

🌐 **اللغات:** العربية والإنجليزية
    """
    await update.message.reply_text(help_text)

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رد على أمر /about"""
    about_text = """
📱 **الباحث الحديثي الذكي**
🤖 @Search4Hadith_Bot

📖 **الوصف:**
بمجرد إرسالك لكلمة واحدة سوف أقوم بإرسال الأحاديث التي تحتوي على هذه المفردة

🧠 **التقنيات:**
• Google Gemini 1.5 Flash
• Hadith API Database
• Python + Telegram Bot API

📚 **المصادر:**
• صحيح البخاري ✅
• المزيد قريباً...

👨‍💻 **المطور:**
هاشم صالح شرف الدين
مكة المكرمة، السعودية

🎯 **الهدف:**
تسهيل الوصول للأحاديث النبوية الشريفة باستخدام الذكاء الاصطناعي

🆓 **مجاني 100%** - خدمة للأمة الإسلامية
    """
    await update.message.reply_text(about_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة رسائل المستخدمين بالذكاء الاصطناعي"""
    user_message = update.message.text.strip()
    
    # رسالة انتظار
    waiting_msg = await update.message.reply_text(
        "🤖 جاري فهم استفسارك بالذكاء الاصطناعي...\n"
        "⏳ قد يستغرق 5-10 ثوانٍ"
    )
    
    try:
        # الخطوة 1: فهم الاستفسار بـ Gemini
        logger.info(f"فهم الاستفسار: {user_message}")
        query_data = ai_understand_query(user_message)
        keywords = query_data.get('keywords', [user_message])
        intent = query_data.get('intent', 'بحث في الأحاديث')
        
        # الخطوة 2: البحث في الأحاديث
        logger.info(f"البحث بالكلمات: {keywords}")
        results = search_hadiths(keywords)
        
        # الخطوة 3: بناء الرد
        if results:
            response = f"🎯 **فهم استفسارك:**\n_{intent}_\n\n"
            response += f"🔑 **الكلمات المفتاحية:** {', '.join(keywords)}\n"
            response += "\n" + "═" * 30 + "\n\n"
            response += f"📚 **وجدت {len(results)} حديث:\n\n**"
            
            # عرض الأحاديث مع الشرح
            for i, result in enumerate(results, 1):
                response += f"📖 **الحديث {i}:**\n"
                response += f"{result['text']}\n\n"
                
                # شرح الحديث بـ Gemini
                explanation = ai_explain_hadith(result['text'], user_message)
                response += f"💡 **الشرح:**\n_{explanation}_\n\n"
                
                response += f"📚 المصدر: {result['reference']}\n"
                response += f"🔢 رقم: {result['number']}\n"
                response += "─" * 30 + "\n\n"
            
            response += "✨ للبحث عن موضوع آخر، أرسل سؤالك مباشرة"
        else:
            response = f"⚠️ لم أجد أحاديث مطابقة لـ: \"{user_message}\"\n\n"
            response += "💡 **اقتراحات:**\n"
            response += "• جرب كلمات أوضح\n"
            response += "• استخدم كلمات مختلفة\n"
            response += "• اسأل بطريقة أخرى\n\n"
            response += "🔍 مثال: \"الصلاة\" أو \"فضل الصدقة\""
        
        # حذف رسالة الانتظار وإرسال الرد
        await waiting_msg.delete()
        
        # تقسيم الرد إذا كان طويلاً
        if len(response) > 4096:
            parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for part in parts:
                await update.message.reply_text(part, parse_mode='Markdown')
        else:
            await update.message.reply_text(response, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"خطأ في معالجة الرسالة: {e}")
        await waiting_msg.delete()
        await update.message.reply_text(
            "❌ عذراً، حدث خطأ في معالجة طلبك.\n"
            "يرجى المحاولة مرة أخرى.\n\n"
            "💡 تأكد من كتابة سؤال واضح أو كلمة للبحث."
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الأخطاء"""
    logger.error(f'حدث خطأ: {context.error}')

def main():
    """بدء البوت"""
    logger.info('🚀 بدء الباحث الحديثي الذكي...')
    logger.info('🤖 Google Gemini: متصل')
    logger.info('📚 Hadith API: جاهز')
    
    # إنشاء التطبيق
    application = Application.builder().token(TOKEN).build()

    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about))
    
    # معالج الرسائل النصية
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # معالج الأخطاء
    application.add_error_handler(error_handler)

    logger.info('✅ البوت جاهز ويعمل!')
    
    # بدء البوت
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
