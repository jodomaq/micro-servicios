#!/usr/bin/env python3
"""
Script de prueba para verificar el funcionamiento del sistema SMTP
"""

import sys
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Agregar el directorio actual al path para importar módulos locales
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from smtp_email import SMTPEmailSender

def test_smtp_connection():
    """Prueba la conexión SMTP sin enviar emails"""
    try:
        # Configuración SMTP desde variables de entorno
        smtp_server = os.getenv("SMTP_SERVER", "smtp.ionos.mx")
        smtp_port = int(os.getenv("SMTP_PORT", "465"))
        smtp_username = os.getenv("SMTP_USERNAME", "contacto@micro-servicios.com.mx")
        smtp_password = os.getenv("SMTP_PASSWORD")
        
        # Validar variables requeridas
        if not smtp_password:
            print("❌ Error: SMTP_PASSWORD no está configurado en las variables de entorno")
            return None
        
        print("🔧 Probando conexión SMTP...")
        print(f"   Servidor: {smtp_server}:{smtp_port}")
        print(f"   Usuario: {smtp_username}")
        
        # Crear instancia del cliente SMTP
        email_client = SMTPEmailSender(
            smtp_server=smtp_server,
            port=smtp_port,
            username=smtp_username,
            password=smtp_password
        )
        
        print("✅ Cliente SMTP creado exitosamente")
        return email_client
        
    except Exception as e:
        print(f"❌ Error al crear cliente SMTP: {e}")
        return None

def test_email_sending(email_client, test_mode=True):
    """Prueba el envío de un email de prueba"""
    if not email_client:
        print("❌ No hay cliente SMTP disponible")
        return False
    
    try:
        recipient = os.getenv("RECIPIENT_EMAIL", "contacto@micro-servicios.com.mx")
        subject = "🧪 Prueba de configuración SMTP - Micro-Servicios"
        
        html_body = """
        <html>
            <body>
                <h2>Prueba de Configuración SMTP</h2>
                <p>Este es un email de prueba para verificar que la configuración SMTP está funcionando correctamente.</p>
                <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; background-color: #f9f9f9;"><strong>Servidor:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">smtp.ionos.mx</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; background-color: #f9f9f9;"><strong>Puerto:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">465 (SSL/TLS)</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; background-color: #f9f9f9;"><strong>Estado:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">✅ Funcionando correctamente</td>
                    </tr>
                </table>
                <p><small>Este mensaje fue generado automáticamente por el script de prueba.</small></p>
            </body>
        </html>
        """
        
        text_body = """
        Prueba de Configuración SMTP
        
        Este es un email de prueba para verificar que la configuración SMTP está funcionando correctamente.
        
        Servidor: smtp.ionos.mx
        Puerto: 465 (SSL/TLS)
        Estado: ✅ Funcionando correctamente
        
        ---
        Este mensaje fue generado automáticamente por el script de prueba.
        """
        
        if test_mode:
            print("🧪 Modo de prueba activado")
            print(f"   Destinatario: {recipient}")
            print(f"   Asunto: {subject}")
            print("   ¿Desea enviar el email de prueba? (y/N): ", end="")
            
            respuesta = input().strip().lower()
            if respuesta not in ['y', 'yes', 'sí', 'si']:
                print("❌ Envío cancelado por el usuario")
                return False
        
        print("📧 Enviando email de prueba...")
        
        # Enviar email
        result = email_client.send_html_email(
            to_email=recipient,
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )
        
        if result:
            print("✅ Email de prueba enviado exitosamente")
            return True
        else:
            print("❌ Error al enviar email de prueba")
            return False
            
    except Exception as e:
        print(f"❌ Error al enviar email de prueba: {e}")
        return False

def main():
    """Función principal"""
    print("=" * 60)
    print("🧪 SCRIPT DE PRUEBA SMTP - MICRO-SERVICIOS")
    print("=" * 60)
    
    # Prueba 1: Conexión SMTP
    print("\n1️⃣ Probando conexión SMTP...")
    email_client = test_smtp_connection()
    
    if not email_client:
        print("\n❌ Las pruebas han fallado. Revisa la configuración SMTP.")
        return 1
    
    # Prueba 2: Envío de email (opcional)
    print("\n2️⃣ Probando envío de email...")
    success = test_email_sending(email_client, test_mode=True)
    
    if success:
        print("\n🎉 ¡Todas las pruebas han pasado exitosamente!")
        print("   El sistema SMTP está configurado correctamente.")
        return 0
    else:
        print("\n⚠️  Las pruebas de conexión pasaron, pero hay problemas con el envío.")
        print("   Revisa los logs para más detalles.")
        return 1

if __name__ == "__main__":
    sys.exit(main())