from flask import Flask, jsonify, request
from flask_cors import CORS
from services.reel_to_transcript import processVideo
from dotenv import load_dotenv
import os
from urllib.parse import urlparse

env_file = ".env"
load_dotenv(env_file)

app = Flask(__name__)
CORS(app)

@app.route('/api/hello', methods=['GET'])
def hello_world():
    return jsonify({"message": "Hello from Flask on Vercel!"})

@app.route('/api/get_transcript', methods=['POST'])
def get_transcript():
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    # Validate URL format
    if not is_valid_url(url):
        return jsonify({'error': 'Invalid URL format'}), 400

    # Validate Instagram domain
    if "instagram.com" not in url:
        return jsonify({'error': 'URL must belong to Instagram'}), 400
    
    # transcript = processVideo(url)
    return processVideo(url)

def is_valid_url(url):
    try:
        parsed = urlparse(url)
        return all([parsed.scheme, parsed.netloc])
    except:
        return False
    
app = app
