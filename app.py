import os
import re
import subprocess
import zipfile
import shutil
import requests
from flask import Flask, request, render_template, send_file, jsonify

app = Flask(__name__)

BASE_DIR = "/tmp/workshop_data"
STEAM_CONTENT_PATH = "/root/Steam/steamapps/workshop/content"

def get_collection_items(collection_id):
    """Получает список ID всех модов из коллекции через Steam API"""
    url = "https://api.steampowered.com/ISteamRemoteStorage/GetCollectionDetails/v1/"
    data = {'collectioncount': 1, 'publishedfileids[0]': collection_id}
    try:
        r = requests.post(url, data=data, timeout=10)
        details = r.json().get('response', {}).get('collectiondetails', [{}])[0]
        children = details.get('children', [])
        return [item['publishedfileid'] for item in children]
    except:
        return []

def get_app_id(workshop_id):
    """Находит App ID игры (к какой игре относится мод/коллекция)"""
    try:
        url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={workshop_id}"
        response = requests.get(url, timeout=10)
        match = re.search(r'steampowered\.com/app/(\d+)', response.text)
        return match[1] if match else None
    except:
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    match = re.search(r'id=(\d+)', url)
    
    if not match:
        return jsonify({"error": "Некорректная ссылка"}), 400
    
    main_id = match[1]
    app_id = get_app_id(main_id)
    
    if not app_id:
        return jsonify({"error": "Не удалось определить игру"}), 400

    # Очистка старых данных
    if os.path.exists(BASE_DIR): shutil.rmtree(BASE_DIR)
    os.makedirs(BASE_DIR)
    if os.path.exists("/root/Steam"): shutil.rmtree("/root/Steam") # Очистка кэша SteamCMD

    # Проверяем, коллекция это или одиночный мод
    mod_ids = get_collection_items(main_id)
    if not mod_ids:
        mod_ids = [main_id] # Если не коллекция, качаем как одиночный мод

    try:
        # Скачиваем каждый мод из списка
        for m_id in mod_ids:
            cmd = f"steamcmd +login anonymous +workshop_download_item {app_id} {m_id} +quit"
            subprocess.run(cmd, shell=True, check=True)

        # Создаем ZIP
        zip_filename = f"workshop_pack_{main_id}.zip"
        zip_path = os.path.join(BASE_DIR, zip_filename)
        
        source_folder = os.path.join(STEAM_CONTENT_PATH, app_id)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_folder):
                for file in files:
                    full_path = os.path.join(root, file)
                    # Сохраняем структуру папок внутри ZIP (мод_1/файлы, мод_2/файлы)
                    arcname = os.path.relpath(full_path, source_folder)
                    zipf.write(full_path, arcname=arcname)

        return send_file(zip_path, as_attachment=True)

    except Exception as e:
        return jsonify({"error": f"Ошибка при скачивании: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
