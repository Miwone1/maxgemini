import os
import requests
from flask import Flask, request
from google import genai

app = Flask(__name__)

VK_TOKEN = os.environ.get("VK_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Инициализация клиента Gemini
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def send_vk_message(user_id: int, text: str):
    """Отправка ответа пользователю во ВКонтакте."""
    if not VK_TOKEN:
        return
    url = "https://api.vk.com/method/messages.send"
    params = {
        "user_id": user_id,
        "message": text,
        "random_id": os.urandom(4).hex(),
        "access_token": VK_TOKEN,
        "v": "5.131"
    }
    try:
        requests.post(url, data=params, timeout=15)
    except Exception as e:
        print(f"Ошибка отправки в ВК: {e}")

def ask_gemini(prompt: str) -> str:
    """Запрос к модели Gemini."""
    if not gemini_client:
        return "Gemini API ключ не настроен."
    try:
        response = gemini_client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
        )
        return response.text or "Не удалось сформировать ответ."
    except Exception as e:
        return f"Ошибка Gemini: {e}"

@app.route("/", methods=["GET"])
def index():
    """Эндпоинт для UptimeRobot и проверки жизни сервера."""
    return "VK Callback Bot is running!", 200

@app.route("/webhook", methods=["POST", "GET"])
def webhook():
    """Прием входящих событий и подтверждения от ВКонтакте."""
    data = request.get_json(silent=True) or {}
    
    # Жесткий ответ для подтверждения сервера ВК
    if data.get("type") == "confirmation":
        return "1b572ce4", 200

    # Обработка входящего сообщения от пользователя
    if data.get("type") == "message_new":
        msg_obj = data.get("object", {}).get("message", {})
        user_id = msg_obj.get("from_id")
        text = msg_obj.get("text")

        if user_id and text:
            print(f"Сообщение от {user_id}: {text}")
            reply = ask_gemini(text)
            send_vk_message(user_id, reply)

    return "ok", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
