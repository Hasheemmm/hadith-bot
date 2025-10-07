import google.generativeai as genai

# ⚠️ استبدل هذا المفتاح بمفتاحك الحقيقي من: https://ai.google.dev/
API_KEY = "AIzaSyDO0awd00GHY1_d37Id9Vkc6uKXUAhwjGg"

genai.configure(api_key="AIzaSyDO0awd00GHY1_d37Id9Vkc6uKXUAhwjGg")

# احصل على قائمة النماذج المدعومة (للاختيار من بينها)
print("🔍 النماذج المدعومة:")
try:
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"✅ {model.name}")
except Exception as e:
    print(f"❌ خطأ في جلب النماذج: {e}")
    print("نستخدم نموذجًا افتراضيًا...")

# جرّب نموذجًا مدعومًا
try:
    # نستخدم gemini-pro لأنه مدعوم دائمًا
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    response = model.generate_content("ما هو الحديث النبوي عن الصبر؟ فقط اذكر الحديث والمصدر.")
    
    print("\n✅ الإجابة من Gemini:")
    print(response.text)
    
except Exception as e:
    print(f"❌ خطأ في التوليد: {e}")
