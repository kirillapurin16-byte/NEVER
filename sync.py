import requests
import json
import base64
import os
import re
from html import unescape

# Настройки твоего проекта
CHANNEL_USERNAME = "NEVERDROID" 
REPO = os.environ.get("GITHUB_REPOSITORY") 
GH_TOKEN = os.environ.get("GH_TOKEN") 

def get_all_telegram_files():
    """ Парсит веб-архив канала и вытаскивает ВСЕ посты, где есть файлы """
    url = f"https://t.me/s/{CHANNEL_USERNAME}"
    response = requests.get(url)
    if response.status_code != 200:
        print("Ошибка доступа к веб-архиву Telegram")
        return []
    
    html_content = response.text
    
    # Регулярка разбивает страницу на отдельные блоки постов
    posts = re.findall(r'<div class="tgme_widget_message_wrap[^"]*">.*?</div>\s*</div>\s*</div>', html_content, re.DOTALL)
    
    file_cards = []
    
    for post in posts:
        # Проверяем, есть ли внутри этого поста блок с документом/файлом
        if "tgme_widget_message_document" in post:
            
            # 1. Извлекаем ID поста, чтобы сделать прямую ссылку на файл в ТГК
            post_id_match = re.search(r'data-post="'+CHANNEL_USERNAME+r'/(\d+)"', post)
            if not post_id_match:
                continue
            post_id = post_id_match.group(1)
            direct_url = f"https://t.me/{CHANNEL_USERNAME}/{post_id}"
            
            # 2. Вытаскиваем реальное название файла
            file_name_match = re.search(r'<div class="tgme_widget_message_document_name[^"]*">(.*?)</div>', post, re.DOTALL)
            file_name = file_name_match.group(1).strip() if file_name_match else "Скрипт / Прошивка"
            # Очищаем от HTML тегов, если они пролезли
            file_name = re.sub(r'<[^>]+>', '', file_name)
            
            # 3. Вытаскиваем описание (комментарий) к файлу
            caption = ""
            caption_match = re.search(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', post, re.DOTALL)
            if caption_match:
                caption = caption_match.group(1).strip()
                # Превращаем ТГ-теги <br/> в обычные переносы строк и убираем лишний HTML
                caption = caption.replace('<br/>', '\n').replace('<br>', '\n')
                caption = re.sub(r'<[^>]+>', '', caption)
                caption = unescape(caption) # Декодируем символы вроде &quot; или &amp;
            
            # Если описания под файлом нет, оставляем пустую строку (сайт сам её скроет)
            if not caption:
                caption = ""
                
            file_cards.append({
                "title": file_name,
                "url": direct_url,
                "desc": caption
            })
            
    # Переворачиваем список, чтобы самые свежие файлы были в самом верху сайта
    file_cards.reverse()
    return file_cards

def update_github_json():
    # Собираем все файлы из ТГК
    tg_files = get_all_telegram_files()
    
    if not tg_files:
        print("Файлы в архиве канала не найдены. Создаем заглушку.")
        tg_files = [{
            "title": "Ожидание файлов",
            "url": f"https://t.me/{CHANNEL_USERNAME}",
            "desc": "Выложите в канал любой файл с описанием, и он тут же отобразится здесь!"
        }]
        
    new_data = {"firmwares": tg_files}

    # Пушим обновленный data.json в репозиторий GitHub
    gh_url = f"https://api.github.com/repos/{REPO}/contents/data.json"
    headers = {"Authorization": f"token {GH_TOKEN}"}

    req_file = requests.get(gh_url, headers=headers).json()
    sha = req_file.get("sha") if isinstance(req_file, dict) else None

    content_bytes = json.dumps(new_data, ensure_ascii=False, indent=2).encode('utf-8')
    content_base64 = base64.b64encode(content_bytes).decode('utf-8')

    data_to_push = {
        "message": "🔄 Полная авто-синхронизация файлов из архива ТГК",
        "content": content_base64
    }
    if sha:
        data_to_push["sha"] = sha

    res = requests.put(gh_url, headers=headers, json=data_to_push)
    if res.status_code in [200, 201]:
        print(f"Успешно добавлено файлов на сайт: {len(tg_files)}")
    else:
        print("Ошибка GitHub API:", res.text)

if __name__ == "__main__":
    update_github_json()
