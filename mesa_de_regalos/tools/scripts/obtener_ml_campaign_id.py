import os
import requests
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

CLIENT_ID = os.getenv("ML_APP_ID")
CLIENT_SECRET = os.getenv("ML_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("ML_REFRESH_TOKEN")
USER_ID = os.getenv("ML_USER_ID")

def get_access_token():
    """Genera un nuevo access token utilizando el refresh token"""
    url = "https://api.mercadolibre.com/oauth/token"
    
    payload = {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN
    }
    
    headers = {
        "accept": "application/json",
        "content-type": "application/x-www-form-urlencoded"
    }
    
    response = requests.post(url, data=payload, headers=headers)
    response.raise_for_status() # Lanza excepción si el código HTTP es de error
    return response.json()

def get_campaigns(access_token, user_id):
    """Consulta las campañas de Product Ads del usuario"""
    # Endpoint oficial de Mercado Ads
    url = f"https://api.mercadolibre.com/advertising/product_ads/campaigns?user_id={user_id}"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    try:
        print("1. Autenticando con Mercado Libre...")
        token_data = get_access_token()
        access_token = token_data.get("access_token")
        
        # Guardar el nuevo refresh_token es una buena práctica (opcional en este script)
        nuevo_refresh_token = token_data.get("refresh_token")
        print(f"   [Éxito] Token de acceso obtenido.\n")
        
        print("2. Obteniendo IDs de campañas...")
        campaigns = get_campaigns(access_token, USER_ID)
        
        print("\n--- Resultados de Campañas Activas ---")
        if not campaigns:
            print("No se encontraron campañas para este usuario.")
            
        # Dependiendo de la estructura exacta de retorno, iteramos la lista
        # Usualmente Mercado Libre devuelve una lista directa o un array bajo la llave 'results'
        items = campaigns.get('results', campaigns) if isinstance(campaigns, dict) else campaigns
            
        for campaign in items:
            c_id = campaign.get("id")
            c_name = campaign.get("name", "Sin nombre")
            c_status = campaign.get("status", "Desconocido")
            print(f"ID de Campaña: {c_id} | Nombre: {c_name} | Estado: {c_status}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n[!] Error en la petición a la API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Detalle del error de Mercado Libre: {e.response.text}")