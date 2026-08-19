from flask import Flask, send_from_directory
import os

app = Flask(__name__, static_folder='webapp')

AUDIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'webapp', 'assets', 'audio')

@app.route('/audio/<path:filename>')
def audio_file(filename):
    return send_from_directory(AUDIO_DIR, filename)

@app.route('/')
@app.route('/quran')
def index():
    return send_from_directory('webapp', 'index.html')

@app.route('/azkar')
def azkar():
    return send_from_directory('webapp', 'azkar.html')

if __name__ == '__main__':
    try:
        port = int(os.environ.get("PORT", 5000))
    except (TypeError, ValueError):
        port = 5000
    app.run(host="0.0.0.0", port=port)
