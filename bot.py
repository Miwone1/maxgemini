import os
import requests
from flask import Flask, request, jsonify
from google import genai

app = Flask(__name__)

# Получаем ключи из переменных окружения Render
VK_TOKEN = os.environ.get("VK_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Инициализация клиента Gemini
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

def send_vk_message(user_id: int, text: str):
    """Отправка ответа пользователю во ВКонтакте."""
    access_token = os.environ.get("VK_TOKEN")
    random_id = int(os.environ.get("RANDOM_ID", 0)) + 1
    
    url = "https://api.vk.com/method/messages.send"
    params = {
        "user_id": user_id,
        "message": text,
        "random_id": random_id,
        "access_token": access_token,
        "v": "5.131"
    }
    try:
        response = requests.post(url, data=params, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Ошибка отправки сообщения в ВК: {e}")

def ask_gemini(prompt: str) -> str:
    """Запрос к модели Gemini."""
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text or "Не удалось сформировать ответ."
    except Exception as e:
        return f"Ошибка при обращении к Gemini API: {e}"

@app.route("/", methods=["GET"])
def health_check():
    """Эндпоинт для UptimeRobot."""
    return "VK Bot is running!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    """Прием входящих событий от ВКонтакте."""
    data = request.json or {}
    
    # Подтверждение сервера для ВК
    if data.get("type") == "confirmation":
        return "1b572e4", 200

    # Обработка входящего сообщения
    if data.get("type") == "message_new":
        object_data = data.get("object", {})
        message = object_data.get("message", {})
        user_id = message.get("from_id")
        user_text = message.get("text")

        if user_id and user_text:
            print(f"Получено сообщение из ВК от {user_id}: {user_text}")
            reply = ask_gemini(user_text)
            send_vk_message(user_id, reply)

    return "ok", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
