import os
from flask import Flask, request, render_template
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

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Upload de Imagem</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 50px;
            }
            form {
                margin-bottom: 20px;
            }
            input[type="file"] {
                margin-bottom: 10px;
            }
        </style>
    </head>
    <body>

    <h1>Upload de Imagem para o Google Drive</h1>
    <form id="uploadForm" enctype="multipart/form-data">
        <input type="file" name="file" accept="image/jpeg" required>
        <button type="submit">Enviar</button>
    </form>

    <div id="result"></div>

    <script>
        document.getElementById('uploadForm').addEventListener('submit', function(event) {
            event.preventDefault();
            const formData = new FormData(this);

            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Erro ao fazer upload');
                }
                return response.json();
            })
            .then(data => {
                document.getElementById('result').innerHTML = `
                    <p>Arquivo enviado com sucesso!</p>
                    <p>Link da foto: ${data.link_foto}</p>
                    <p><a href="${data.link}" target="_blank">Ver imagem</a></p>
                `;
            })
            .catch(error => {
                document.getElementById('result').innerHTML = `<p>${error.message}</p>`;
            });
        });
    </script>

    </body>
    </html>
    '''

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return 'Nenhum arquivo enviado.', 400
    
    file = request.files['file']
    if file.filename == '':
        return 'Nenhum arquivo selecionado.', 400
    
    # Verifica se o diretório "uploads" existe
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    
    file_path = os.path.join('uploads', file.filename)
    file.save(file_path)
    
    try:
        link = upload_to_drive(file_path)
    except Exception as e:
        return f'Erro ao fazer upload para o Google Drive: {e}', 500
    
    return {'link': link}

@app.route('/test')
def test():
    return "Servidor está funcionando!"

if __name__ == '__main__':
    app.run(debug=True)
