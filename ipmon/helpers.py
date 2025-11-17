'''Modulo Funciones auxiliares'''
import re
import io
import socket

from ipmon.database import AppConfig, Hosts
from ipmon import app
from PIL import Image



def get_stable_cycles(default_value=3):
    """Devuelve el número de ciclos estables configurado globalmente."""
    with app.app_context():
        conf = AppConfig.query.first()
        return conf.stable_cycles if conf else default_value
    

def strip_html(html):
    """Convierte el mensaje HTML en texto plano pero conserva  para Telegram"""
    text = re.sub(r'<(?!/?b\b)[^>]+>', '', html)
    text = text.replace('&quot;', '"').replace('&nbsp;', ' ')
    return text.strip()

def procesar_imagen_para_email(path, max_width=800, max_height=600, calidad=70):
    """ Redimensiona y comprime la imagen para adjuntar en correos."""
    with Image.open(path) as img:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        img.thumbnail((max_width, max_height))

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=calidad, optimize=True)
        buffer.seek(0)
        return buffer
    
def get_alert_status_message(alert):
    """Devuelve el mensaje en HTML para un solo host"""
    with app.app_context():
        host = Hosts.query.filter_by(id=alert.host_id).first()
        if not host:
            return "<b> Host no encontrado en la BD</b>"

        message = (
            "<b>{}:</b> {}, "
            "<b>IP:</b> {}, "
            "<b>Ciudad:</b> {}, "
            "<b>CTO:</b> {}, "
            "vinculado a <b>{}</b>. "
            "Cambio a estado <b>\"{}\"</b> el {}"
        ).format(
            host.tipo or "Dispositivo",
            host.hostname or "Sin nombre",
            host.ip_address or "N/A",
            host.ciudad or "N/A",
            host.cto or "N/A",
            host.dispositivo or "N/A",
            host.status or "Desconocido",
            host.last_poll or "N/A"
        )
        return message

def get_hostname(ip_address):
    '''Obtiene el FQDN a partir de una dirección IP'''
    try:
        hostname = socket.getfqdn(ip_address)
    except socket.error:
        hostname = 'Unknown'
    return hostname