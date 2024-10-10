import os
from flask import Flask, request
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload

app = Flask(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive.file']
link_foto = ""

def upload_to_drive(file_path):
    global link_foto
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

    link_foto = f"https://drive.google.com/thumbnail?sz=w500&id={file_id}"
    return link_foto

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return 'Nenhum arquivo enviado.', 400
    
    file = request.files['file']
    if file.filename == '':
        return 'Nenhum arquivo selecionado.', 400
    
    file_path = os.path.join('uploads', file.filename)
    file.save(file_path)
    
    link = upload_to_drive(file_path)
    return {'link': link}

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)
