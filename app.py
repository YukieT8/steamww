import os
import re
import subprocess
import zipfile
import shutil
import requests
from flask import Flask, request, render_template, send_file, jsonify

app = Flask(__name__)

BASE_DIR = "/tmp/workshop_data"

def get_app_id(workshop_id):
    """Автоматически находит App ID игры по ссылке на мод"""
    try:
        url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={workshop_id}"
        response = requests.get(url, timeout=10)
        # Ищем в коде страницы ссылку на магазин, которая содержит App ID
        # Обычно это выглядит так: store.steampowered.com/app/4000
        match = re.search(r'steampowered\.com/app/(\d+)', response.text)
        if match:
            return match[1]
        return None
    except:
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')

    # 1. Извлекаем ID мода
    match = re.search(r'id=(\d+)', url)
    if not match:
        return jsonify({"error": "Некорректная ссылка на Workshop"}), 400
    
    item_id = match[1]

    # 2. Автоматически определяем App ID игры
    app_id = get_app_id(item_id)
    if not app_id:
        return jsonify({"error": "Не удалось определить игру для этого мода. Проверьте ссылку."}), 400
    
    # Очистка папок
    if os.path.exists(BASE_DIR):
        shutil.rmtree(BASE_DIR)
    os.makedirs(BASE_DIR)

    # 3. Скачивание через SteamCMD
    try:
        # Команда загрузки
        cmd = f"steamcmd +login anonymous +workshop_download_item {app_id} {item_id} +quit"
        subprocess.run(cmd, shell=True, check=True)
        
        # Путь скачанных файлов
        steam_path = f"/root/Steam/steamapps/workshop/content/{app_id}/{item_id}"
        
        if not os.path.exists(steam_path):
            return jsonify({"error": "Файлы не найдены. Возможно, анонимное скачивание запрещено для этой игры."}), 500

        zip_filename = f"mod_{item_id}.zip"
        zip_path = os.path.join(BASE_DIR, zip_filename)

        # 4. Упаковка в ZIP
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(steam_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    arcname = os.path.relpath(full_path, steam_path)
                    zipf.write(full_path, arcname=arcname)

        return send_file(zip_path, as_attachment=True)

    except Exception as e:
        return jsonify({"error": f"Ошибка сервера: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
