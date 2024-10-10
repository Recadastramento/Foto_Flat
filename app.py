import os
from flask import Flask, request, redirect, url_for, render_template
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload

app = Flask(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def upload_to_drive(file_path):
    creds = None

    if os.path.exists("Ftoken.json"):
        creds = Credentials.from_authorized_user_file("Ftoken.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        with open("Ftoken.json", 'w') as token:
            token.write(creds.to_json())

    service = build('drive', 'v3', credentials=creds)

    file_metadata = {'name': os.path.basename(file_path)}
    media = MediaFileUpload(file_path, mimetype='image/jpeg')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    file_id = file.get('id')
    service.permissions().create(
        fileId=file_id,
        body={'type': 'anyone', 'role': 'reader'}
    ).execute()

    return f"https://drive.google.com/thumbnail?sz=w500&id={file_id}"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'Nenhum arquivo enviado.'
        
        file = request.files['file']
        if file.filename == '':
            return 'Nenhum arquivo selecionado.'
        
        file_path = os.path.join('uploads', file.filename)
        file.save(file_path)
        
        link = upload_to_drive(file_path)
        return f'Arquivo enviado com sucesso! Link: <a href="{link}">{link}</a>'
    
    return render_template('index.html')

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)
