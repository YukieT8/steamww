import os
import subprocess
import zipfile
import requests
from flask import Flask, request, send_file, render_template, jsonify

app = Flask(__name__)

# Путь для временного хранения файлов
DOWNLOAD_PATH = "/tmp/steam_mods"
ZIP_PATH = "/tmp/modpack.zip"

def get_collection_ids(collection_id):
    """Получает ID всех модов из коллекции через Steam API"""
    url = "https://api.steampowered.com/ISteamRemoteStorage/GetCollectionDetails/v1/"
    data = {'collectioncount': 1, 'publishedfileids[0]': collection_id}
    r = requests.post(url, data=data)
    items = r.json().get('response', {}).get('collectiondetails', [{}])[0].get('children', [])
    return [item['publishedfileid'] for item in items]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.json.get('url')
    # Извлекаем ID из ссылки
    import re
    id_match = re.search(r'id=(\d+)', url)
    if not id_match:
        return jsonify({"error": "Неверная ссылка"}), 400
    
    workshop_id = id_match[1]
    
    # Создаем директории
    if not os.path.exists(DOWNLOAD_PATH):
        os.makedirs(DOWNLOAD_PATH)

    # Проверяем, коллекция это или один мод
    mod_ids = get_collection_ids(workshop_id)
    if not mod_ids:
        mod_ids = [workshop_id]

    # Скачивание через SteamCMD (пример команды)
    for m_id in mod_ids:
        # ВАЖНО: APP_ID игры (например, 4000 для GMod) нужно знать заранее или парсить
        cmd = f"steamcmd +login anonymous +workshop_download_item 4000 {m_id} +quit"
        subprocess.run(cmd, shell=True)

    # Создание ZIP
    with zipfile.ZipFile(ZIP_PATH, 'w') as zipf:
        for root, dirs, files in os.walk(DOWNLOAD_PATH):
            for file in files:
                zipf.write(os.path.join(root, file), file)

    return send_file(ZIP_PATH, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
