import requests
import json
import base64
import os
import re

CHANNEL_USERNAME = "NEVERDROID" 
REPO = os.environ.get("GITHUB_REPOSITORY") 
GH_TOKEN = os.environ.get("GH_TOKEN") 

def get_latest_telegram_posts():
    url = f"https://t.me/s/{CHANNEL_USERNAME}"
    response = requests.get(url)
    if response.status_code != 200:
        return []
    # Находим все ссылки на посты/файлы в публичном веб-интерфейсе канала
    links = re.findall(r'href="(https://t\.me/[^"]+)"', response.text)
    return list(set(links))

def update_github_json():
    tg_links = get_latest_telegram_posts()
    if not tg_links:
        print("Новых ссылок не найдено.")
        return

    new_firmwares = []
    for index, link in enumerate(tg_links[:6]): 
        new_firmwares.append({
            "title": f"Скрипт из ТГ #{index+1}",
            "status": "TG-Канал",
            "statusClass": "success",
            "url": link,
            "desc": "Скрипт или прошивка автоматически подтянуты из официального Telegram-канала NEVERDROID."
        })
        
    new_data = {"firmwares": new_firmwares}
    gh_url = f"https://api.github.com/repos/{REPO}/contents/data.json"
    headers = {"Authorization": f"token {GH_TOKEN}"}

    req_file = requests.get(gh_url, headers=headers).json()
    sha = req_file.get("sha") if isinstance(req_file, dict) else None

    content_bytes = json.dumps(new_data, ensure_ascii=False, indent=2).encode('utf-8')
    content_base64 = base64.b64encode(content_bytes).decode('utf-8')

    data_to_push = {
        "message": "🔄 Авто-синхронизация скриптов из Telegram-канала",
        "content": content_base64
    }
    if sha:
        data_to_push["sha"] = sha

    res = requests.put(gh_url, headers=headers, json=data_to_push)
    if res.status_code in [200, 201]:
        print("Сайт обновлен!")
    else:
        print("Ошибка:", res.text)

if __name__ == "__main__":
    update_github_json()
