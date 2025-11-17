'''Modulo Alertas'''
import os
import sys
import json
import requests
import time

from ipmon import db, scheduler, app, log
from ipmon.database import Hosts, HostAlerts, AppConfig, Images
from ipmon.api import get_alerts_enabled, get_smtp_configured, get_smtp_config
from ipmon.helpers import strip_html, get_alert_status_message
from ipmon.smtp import send_smtp_message

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')
   
# ==============================
# 🔹 Programación de alertas
# ==============================
def update_host_status_alert_schedule(alert_interval):
    '''Actualiza la programación de la alerta de cambio de estado del host mediante APScheduler'''
    try:
        scheduler.remove_job('Host Status Change Alert')
    except Exception:
        pass

    scheduler.add_job(
        id='Host Status Change Alert',
        func=_host_status_alerts_threaded,
        trigger='interval',
        seconds=int(alert_interval),
        max_instances=1
    )


def _host_status_alerts_threaded():
    with app.app_context():
        alerts_enabled = json.loads(get_alerts_enabled()).get('alerts_enabled', False)
        smtp_configured = json.loads(get_smtp_configured()).get('smtp_configured', False)
        alerts = HostAlerts.query.filter_by(alert_cleared=False).all()

        if not alerts:
            return  # No hay alertas pendientes

        if alerts_enabled:
            # Lista de mensajes HTML y lista de imágenes globales
            all_messages_html = []
            all_images = []

            # Procesar cada alerta
            for alert in alerts:
                host = Hosts.query.filter_by(id=alert.host_id).first()
                if not host:
                    continue

                # Mensaje principal
                msg_html = get_alert_status_message(alert)

                # Buscar imágenes del host
                imgs = Images.query.filter_by(host_id=host.id).all()
                for idx, img in enumerate(imgs):
                    local_path = os.path.join(app.static_folder, img.file_path)
                    cid = f"host_{host.id}_{idx}"
                    if os.path.exists(local_path):
                        # Incrustar en HTML
                        msg_html += f'<br><img src="cid:{cid}" style="max-width:400px;">'
                        # Guardar para adjuntar después
                        all_images.append({"path": local_path, "cid": cid})

                all_messages_html.append(msg_html)

            # --- Email: concatenar mensajes con separador ---
            message_email = "<hr>".join(all_messages_html)

            # --- Envío por correo ---
            if smtp_configured and message_email:
                try:
                    smtp_conf = json.loads(get_smtp_config())
                    recipients = list(set(filter(None, [
                        smtp_conf.get("smtp_sender1"),
                        smtp_conf.get("smtp_sender2")
                    ])))

                    if recipients:
                        for recipient in recipients:
                            send_smtp_message(
                                recipient,
                                'MONITOREO - Alerta de cambio de estado del servidor/dispositivo',
                                message_email,
                                images=all_images
                            )
                except Exception as exc:
                    log.error(f'❌ Error al enviar alerta SMTP: {exc}')

            # --- Envío por Telegram ---
            for alert in alerts:
                try:
                    _send_telegram_alert(alert)
                except Exception as exc:
                    log.error(f' Error enviando alerta a Telegram: {exc}')
                    time.sleep(1.2)  # Pausa de 1.2 segundos entre mensajes
        # Marcar alertas como enviadas
        for alert in alerts:
            alert.alert_cleared = True

        db.session.commit()

# ==============================
# 🔹 Configuración Telegram
# ==============================
def _send_telegram_alert(alert):
    """Envía una alerta individual a Telegram con foto si existe"""
    host = Hosts.query.filter_by(id=alert.host_id).first()
    if not host:
        return

    message = get_alert_status_message(alert)
    caption = strip_html(message)

    app_conf = AppConfig.query.first()
    if not app_conf or not app_conf.telegram_token or not app_conf.telegram_chat_id:
        log.error(" No hay configuración de Telegram en la BD")
        return

    img = Images.query.filter_by(host_id=host.id).first()

    try:
        if img:
            local_path = os.path.join(app.static_folder, img.file_path)

            url = f"https://api.telegram.org/bot{app_conf.telegram_token}/sendPhoto"
            data = {
                "chat_id": app_conf.telegram_chat_id,
                "caption": caption,
                "parse_mode": "HTML"
            }

            if os.path.exists(local_path):
                with open(local_path, "rb") as photo_file:
                    files = {"photo": photo_file}
                    response = requests.post(url, data=data, files=files, timeout=10)
            else:
                base_url = app.config.get("EXTERNAL_BASE_URL")
                if base_url:
                    data["photo"] = f"{base_url}/static/{img.file_path}"
                    response = requests.post(url, data=data, timeout=10)
                else:
                    log.error(" No se encontró la imagen local ni está configurado EXTERNAL_BASE_URL")
                    return
        else:
            url = f"https://api.telegram.org/bot{app_conf.telegram_token}/sendMessage"
            data = {
                "chat_id": app_conf.telegram_chat_id,
                "text": caption,
                "parse_mode": "HTML"
            }
            response = requests.post(url, data=data, timeout=10)

        if response.status_code != 200:
            if response.status_code == 429:
                try:
                    resp_json = response.json()
                    retry_after = resp_json.get("parameters", {}).get("retry_after", 5)
                    log.error(f" Rate limit de Telegram, esperando {retry_after} segundos...")
                    time.sleep(retry_after)  # esperar lo que pide Telegram
                    return _send_telegram_alert(alert)  # reintentar después de esperar
                except Exception as e:
                    log.error(f" Error procesando retry_after: {e}")
                    time.sleep(5)
                    return _send_telegram_alert(alert)
            else:
                log.error(f" Error de Telegram {response.status_code}: {response.text}")
        else:
            log.info(f" Alerta enviada a Telegram para {host.hostname or host.ip_address}")

    except Exception as exc:
        log.error(f" Error enviando alerta con foto a Telegram: {exc}")
