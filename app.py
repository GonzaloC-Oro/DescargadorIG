import os
import zipfile
import json
from flask import Flask, request, send_file, render_template, jsonify
import yt_dlp

app = Flask(__name__)

# Configura yt-dlp
ydl_opts = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    'outtmpl': os.path.join('downloads', '%(id)s.%(ext)s'),
    'quiet': True,
    'no_warnings': True,
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download_video():
    data = request.get_json()
    urls = data.get('urls', [])

    # Obtener las cookies de la variable de entorno
    cookies_json = os.environ.get('INSTAGRAM_COOKIES')

    # Convertir la cadena JSON a una cadena de cookies
    try:
        cookies_list = json.loads(cookies_json)
        cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies_list])
    except Exception as e:
        return jsonify({"error": "Error al procesar las cookies. Revisa el formato."}), 500

    # Crear carpeta de descargas si no existe
    download_dir = 'downloads'
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    downloaded_files = []
    
    # Configurar yt-dlp con las cookies
    ydl_opts['cookie_string'] = cookie_string

    # Iniciar la descarga de los videos
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for url in urls:
            try:
                info_dict = ydl.extract_info(url, download=True)
                video_file = ydl.prepare_filename(info_dict)
                if os.path.exists(video_file):
                    downloaded_files.append(video_file)
            except Exception as e:
                print(f"Error descargando {url}: {e}")
                continue # Continúa con el siguiente video si este falla

    if not downloaded_files:
        return jsonify({'error': 'No se pudo descargar ningún video. Asegúrate de que las URLs son correctas y el contenido es público.'}), 500

    # Crear archivo ZIP y eliminar archivos originales
    zip_path = os.path.join(download_dir, 'videos.zip')
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file in downloaded_files:
            zipf.write(file, os.path.basename(file))
            os.remove(file) # Elimina los archivos originales después de añadirlos al ZIP
    
    return send_file(zip_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)