import google.generativeai as genai

# ⚠️ استخدم مفتاحك الحقيقي بين علامتي اقتباس
API_KEY = "AIzaSyDO0awd00GHY1_d37Id9Vkc6uKXUAhwjGg"

genai.configure(api_key="AIzaSyDO0awd00GHY1_d37Id9Vkc6uKXUAhwjGg")

# استخدم نموذجًا مدعومًا (gemini-2.5-flash مثلاً)
model = genai.GenerativeModel("gemini-2.5-flash")

# جرّب البحث في الحديث
response = model.generate_content("ما هو الحديث النبوي عن الصبر؟ فقط اذكر الحديث والمصدر.")
print("\n✅ الإجابة من Gemini:")
print(response.text)
