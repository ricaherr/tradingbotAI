# notificaciones.py
# Notificaciones por WhatsApp (Twilio) y Telegram, activables/desactivables
from dotenv import load_dotenv
import os
import requests

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# --- ACTIVACIÓN DE CANALES ---
NOTIFICAR_WHATSAPP = False
NOTIFICAR_TELEGRAM = True

# --- TWILIO (WhatsApp) ---
TWILIO_SID = os.getenv('TWILIO_SID', '')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_WHATSAPP_FROM = os.getenv('TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')
TWILIO_WHATSAPP_TO = os.getenv('TWILIO_WHATSAPP_TO', '')
try:
    from twilio.rest import Client
    TWILIO_DISPONIBLE = True
except ImportError:
    TWILIO_DISPONIBLE = False

def enviar_whatsapp_mensaje(mensaje):
    if not (NOTIFICAR_WHATSAPP and TWILIO_DISPONIBLE and TWILIO_SID and TWILIO_AUTH_TOKEN and TWILIO_WHATSAPP_TO):
        print(f"[WHATSAPP] No configurado o desactivado. Mensaje: {mensaje}")
        return
    try:
        client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=mensaje,
            from_=TWILIO_WHATSAPP_FROM,
            to=TWILIO_WHATSAPP_TO
        )
        print(f"[WHATSAPP] Notificación enviada: {mensaje}")
    except Exception as e:
        print(f"[WHATSAPP] Error al enviar mensaje: {e}")

# --- TELEGRAM ---
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def enviar_telegram_mensaje(mensaje):
    if not (NOTIFICAR_TELEGRAM and TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        print(f"[TELEGRAM] No configurado o desactivado. Mensaje: {mensaje}")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje}
    try:
        r = requests.post(url, data=data)
        if r.status_code == 200:
            print(f"[TELEGRAM] Notificación enviada: {mensaje}")
        else:
            print(f"[TELEGRAM] Error al enviar mensaje: {r.text}")
    except Exception as e:
        print(f"[TELEGRAM] Error al enviar mensaje: {e}")

# --- FUNCIÓN UNIFICADA ---
def enviar_notificacion(mensaje, evento=None):
    enviar_whatsapp_mensaje(mensaje)
    enviar_telegram_mensaje(mensaje)
