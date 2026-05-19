import requests
import json
import base64
import os
import re

# Настройки проекта
CHANNEL_USERNAME = "NEVERDROID" 
REPO = os.environ.get("GITHUB_REPOSITORY") 
GH_TOKEN = os.environ.get("GH_TOKEN") 

def get_telegram_files():
    """ Парсит публичный веб-виджет канала и вытаскивает только посты с файлами """
    url = f"https://t.me/s/{CHANNEL_USERNAME}"
    response = requests.get(url)
    if response.status_code != 200:
        print("Ошибка доступа к Telegram")
        return []
    
    # Регулярное выражение ищет ссылки на скачивание файлов из веб-версии Telegram (tgme_widget_message_document)
    # Telegram упаковывает файлы в ссылки вида t.me/NEVERDROID/123?download=1 или прямые пути к медиа-серверам
    file_links = re.findall(r'href="(https://t\.me/[^"]+(?:\?download=1|[^"]+\.(?:bin|zip|rar|txt|py)))"', response.text, re.IGNORECASE)
    
    # Если прямые скачивания не поймались, собираем ссылки на сами посты, содержащие документы
    if not file_links:
        # Ищем ID постов, у которых есть блок документа в верстке
        # Это позволит пользователю перейти в ТГ прямо к кнопке «Скачать файл»
        post_ids = re.findall(r'data-post="NEVERDROID/(\d+)"', response.text)
        for pid in post_ids:
            # Проверяем, есть ли в этом посте упоминание файла/документа
            if f'NEVERDROID/{pid}' in response.text and 'widget_message_document' in response.text:
                file_links.append(f"https://t.me/NEVERDROID/{pid}")

    return list(set(file_links))

def update_github_json():
    # 1. Получаем ссылки на файлы
    file_urls = get_telegram_files()
    if not file_urls:
        print("Новых файлов в канале пока не найдено.")
        return

    # 2. Формируем карточки только для файлов
    new_firmwares = []
    for index, url in enumerate(file_urls[:8]): # Берем до 8 последних файлов
        # Пробуем сделать красивое имя. Если это ссылка на пост, пишем номер поста
        post_num = url.split('/')[-1].split('?')[0]
        
        new_firmwares.append({
            "title": f"Скачать файл (Пост #{post_num})",
            "status": "Файл .BIN / ZIP",
            "statusClass": "success",
            "url": url,
            "desc": "Этот файл был автоматически обнаружен и перенесен из свежих публикаций Telegram-канала NEVERDROID."
        })
        
    new_data = {"firmwares": new_firmwares}

    # 3. Пушим обновленный data.json в репозиторий GitHub
    gh_url = f"https://api.github.com/repos/{REPO}/contents/data.json"
    headers = {"Authorization": f"token {GH_TOKEN}"}

    req_file = requests.get(gh_url, headers=headers).json()
    sha = req_file.get("sha") if isinstance(req_file, dict) else None

    content_bytes = json.dumps(new_data, ensure_ascii=False, indent=2).encode('utf-8')
    content_base64 = base64.b64encode(content_bytes).decode('utf-8')

    data_to_push = {
        "message": "🔄 Авто-синхронизация файлов из Telegram",
        "content": content_base64
    }
    if sha:
        data_to_push["sha"] = sha

    res = requests.put(gh_url, headers=headers, json=data_to_push)
    if res.status_code in [200, 201]:
        print("Сайт успешно переведен на синхронизацию файлов!")
    else:
        print("Ошибка обновления:", res.text)

if __name__ == "__main__":
    update_github_json()
