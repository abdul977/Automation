from flask import Flask, render_template, request
from whatsapp_api_test import send_whatsapp_message
import json

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send', methods=['POST'])
def send():
    phone_number = request.form['phone_number']
    message = request.form['message']
    
    response = send_whatsapp_message(phone_number, message)
    
    if response:
        status_code = response.status_code
        try:
            response_json = response.json()
        except json.JSONDecodeError:
            response_json = {"error": "Invalid JSON response", "text": response.text}
    else:
        status_code = 500
        response_json = {"error": "Failed to send message"}
        
    return render_template('result.html', status_code=status_code, response_json=response_json)

if __name__ == '__main__':
    app.run(debug=True)