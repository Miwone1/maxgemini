import os
import requests
from flask import Flask, request, jsonify
from google import genai

app = Flask(__name__)

# Получаем ключи и порт из переменных окружения Render
MAX_BOT_TOKEN = os.environ.get("MAX_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
PORT = int(os.environ.get("PORT", 10000))

# Инициализация клиента Gemini
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
BASE_URL = "https://platform-api.max.ru"
HEADERS = {
    "Authorization": MAX_BOT_TOKEN,
    "Content-Type": "application/json"
}

def send_message(chat_id: int, text: str):
    """Отправка ответа пользователю в MAX."""
    url = f"{BASE_URL}/messages"
    params = {"chat_id": chat_id}
    payload = {"text": text}
    try:
        response = requests.post(url, headers=HEADERS, params=params, json=payload, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Ошибка отправки сообщения в MAX: {e}")

def ask_gemini(prompt: str) -> str:
    """Запрос к модели Gemini."""
    try:
        response = gemini_client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
        )
        return response.text or "Не удалось сформировать ответ."
    except Exception as e:
        return f"Ошибка при обращении к Gemini API: {e}"

@app.route("/", methods=["GET"])
def health_check():
    """Эндпоинт для UptimeRobot, чтобы бот не засыпал."""
    return "Bot is running!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    """Прием входящих сообщений от мессенджера MAX."""
    data = request.json or {}
    for update in data.get("updates", []):
        if update.update_type == "message_created" or update.get("update_type") == "message_created":
            message = update.get("message", {})
            body = message.get("body", {})
            user_text = body.get("text")
            chat_id = message.get("recipient", {}).get("chat_id")

            if user_text and chat_id:
                print(f"Получено сообщение: {user_text}")
                reply = ask_gemini(user_text)
                send_message(chat_id, reply)

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
