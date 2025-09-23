import pickle
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def generate_token():
    """Genera token OAuth localmente para subir al servidor"""
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES)
    
    # Esto abrirá el navegador local
    creds = flow.run_local_server(port=0)
    
    # Guardar token
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)
    
    print("✅ Token generado exitosamente en 'token.pickle'")
    print("📁 Sube este archivo al servidor junto con 'credentials.json'")

if __name__ == '__main__':
    generate_token()