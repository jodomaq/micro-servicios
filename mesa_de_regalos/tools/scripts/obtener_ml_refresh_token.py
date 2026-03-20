"""
https://auth.mercadolibre.com.mx/authorization?response_type=code&client_id=3822702905040571&redirect_uri=https://micro-servicios.com.mx
"""


import requests

url = "https://api.mercadolibre.com/oauth/token"

# Reemplaza con tus datos reales
payload = {
    "grant_type": "authorization_code",
    "client_id": "3822702905040571",
    "client_secret": "9JPyNYX4NibjfCxp8BcQEYFdg7VKmTJX",
    "code": "TG-69b309491ffbe8000152a391-15454159", 
    "redirect_uri": "https://micro-servicios.com.mx"
}

headers = {
    "accept": "application/json",
    "content-type": "application/x-www-form-urlencoded"
}

response = requests.post(url, data=payload, headers=headers)
datos = response.json()

print("Tu Access Token es:", datos.get("access_token"))
print("Tu PRIMER Refresh Token es:", datos.get("refresh_token"))
