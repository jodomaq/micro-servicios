import os
import requests
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Reemplaza con tu access token temporal
ACCESS_TOKEN = os.getenv("ML_ACCESS_TOKEN")

url = "https://api.mercadolibre.com/users/me"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

response = requests.get(url, headers=headers)
datos_usuario = response.json()

print(f"Tu USER_ID es: {datos_usuario.get('id')}")
