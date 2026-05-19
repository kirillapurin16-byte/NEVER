import requests
import json
import base64
import os

# Настройки проекта
# !!! ВНИМАНИЕ: Замени строку ниже на СВОЙ ТОКЕН БОТА из BotFather (например, "712345:AAH...") !!!
TG_BOT_TOKEN = "8764325032:AAFcHOGSK0Qr4PLG15eCtX5GHrhfjtfSDTo"

CHANNEL_USERNAME = "@NEVERDROID" # Юзернейм канала с собачкой (или ID приватного канала)
REPO = os.environ.get("GITHUB_REPOSITORY") 
GH_TOKEN = os.environ.get("GH_TOKEN") 

def get_telegram_files_via_bot():
    """ Получает последние сообщения напрямую через API твоего бота """
    # Используем метод getUpdates, чтобы поймать сообщения из канала, где бот админ
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/getUpdates"
    
    try:
        response = requests.get(url).json()
        if not response.get("ok"):
            # Если getUpdates пустой, попробуем альтернативный вариант получения постов
            return []
            
        results = response.get("result", [])
        file_posts = []
        
        for item in results:
            # Ищем посты из каналов (channel_post)
            post = item.get("channel_post")
            if not post:
                continue
                
            # Проверяем, есть ли в посте документ (файл)
            if "document" in post:
                doc = post["document"]
                file_id = doc.get("file_id")
                file_name = doc.get("file_name", "Скрипт/Прошивка")
                caption = post.get("caption", "Без описания") # Текст к файлу
                message_id = post.get("message_id")
                
                # Формируем ссылку на этот пост в канале
                post_url = f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}/{message_id}"
                
                file_posts.append({
                    "title": file_name,
                    "url": post_url,
                    "desc": caption
                })
        return file_posts
    except Exception as e:
        print("Ошибка запроса к Telegram API:", e)
        return []

def update_github_json():
    # 1. Запрашиваем посты через бота
    files = get_telegram_files_via_bot()
    
    # Запасной вариант: если через бота ничего не пришло, делаем легкий тестовый список,
    # чтобы сайт не выдавал ошибку «нету файлов»
    if not files:
        print("Бот пока не зафиксировал новых файлов. Создаем демо-список.")
        files = [
            {
                "title": "Ожидание новых файлов из ТГ",
                "url": f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}",
                "desc": "Опубликуйте в канале файл (документ) с описанием, и он автоматически появится здесь при следующем запуске!"
            }
        ]

    new_data = {"firmwares": files}

    # 2. Пушим в GitHub
    gh_url = f"https://api.github.com/repos/{REPO}/contents/data.json"
    headers = {"Authorization": f"token {GH_TOKEN}"}

    req_file = requests.get(gh_url, headers=headers).json()
    sha = req_file.get("sha") if isinstance(req_file, dict) else None

    content_bytes = json.dumps(new_data, ensure_ascii=False, indent=2).encode('utf-8')
    content_base64 = base64.b64encode(content_bytes).decode('utf-8')

    data_to_push = {
        "message": "🔄 Авто-обновление файлов через Telegram-бота",
        "content": content_base64
    }
    if sha:
        data_to_push["sha"] = sha

    res = requests.put(gh_url, headers=headers, json=data_to_push)
    if res.status_code in [200, 201]:
        print("Файлы успешно синхронизированы!")
    else:
        print("Ошибка GitHub API:", res.text)

if __name__ == "__main__":
    update_github_json()
