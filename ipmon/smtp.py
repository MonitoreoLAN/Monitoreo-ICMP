'''Biblioteca SMTP'''
import os
import sys
import smtplib
import json

import flask_login
from email.mime.text import MIMEText
from flask import Blueprint, render_template, redirect, url_for, request, flash

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')
from ipmon import db, log
from ipmon.database import SmtpServer
from ipmon.api import get_smtp_configured, get_smtp_config
from ipmon.forms import SmtpConfigForm
from ipmon.helpers import procesar_imagen_para_email
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

smtp = Blueprint('smtp', __name__)

#### Rutas
@smtp.route("/configureSMTP", methods=['GET', 'POST', 'DELETE'])
@flask_login.login_required
def configure_smtp():
    """Configuración SMTP"""
    form = SmtpConfigForm()

    if request.method == 'GET':
        return render_template('smtpConfig.html', smtp=json.loads(get_smtp_config()), form=form)

    elif request.method == 'POST':
        action = request.form.get('action')
        smtp_conf = SmtpServer.query.first()

        if action == 'delete_server':
            # Elimina SOLO datos de conexión SMTP
            try:
                smtp_conf.smtp_server = ''
                smtp_conf.smtp_port = ''
                smtp_conf.smtp_user = ''
                smtp_conf.smtp_password = ''
                db.session.commit()
                flash('Configuración del servidor SMTP eliminada correctamente', 'success')
                print("[SMTP] Configuración eliminada con éxito.")
            except Exception as e:
                print(f"[SMTP] Error al eliminar servidor: {e}")
                flash('Error al eliminar configuración del servidor SMTP', 'danger')

        elif action == 'delete_recipients':
            # Elimina SOLO destinatarios
            try:
                smtp_conf.smtp_sender1 = ''
                smtp_conf.smtp_sender2 = ''
                db.session.commit()
                flash('Destinatarios SMTP eliminados correctamente', 'success')
                print(f"[SMTP] Error al eliminar servidor: {e}")
            except Exception as e:
                print(f"[SMTP] Error al eliminar destinatarios: {e}")
                flash('Error al eliminar destinatarios SMTP', 'danger')

        elif action == 'update_server':
            # Actualizar solo configuración del servidor SMTP
            if not form.server.data or not form.port.data or not form.user.data or not form.password.data:
                print("[SMTP] Campos incompletos para la actualización del servidor.")
                flash('Todos los campos del servidor SMTP son obligatorios', 'danger')
            else:
                try:
                    # --- Valida conexión SMTP antes de guardar ---
                    import smtplib

                    test_server = form.server.data.strip()
                    test_port = int(form.port.data)
                    test_user = form.user.data.strip()
                    test_password = form.password.data.strip()

                    print(f"[SMTP] Probando conexión a {test_server}:{test_port} como {test_user}")

                    with smtplib.SMTP(test_server, test_port, timeout=10) as server:
                        server.ehlo()
                        server.starttls()
                        server.ehlo()
                        server.login(test_user, test_password)

                    # Si no lanza excepción, guardar en BD
                    smtp_conf.smtp_server = test_server
                    smtp_conf.smtp_port = test_port
                    smtp_conf.smtp_user = test_user
                    smtp_conf.smtp_password = test_password
                    db.session.commit()

                    flash('Configuración de SMTP verificada y guardada correctamente ✅', 'success')
                    print("[SMTP] Configuración verificada y guardada correctamente.")

                except smtplib.SMTPAuthenticationError:
                    flash(' Error de autenticación SMTP: Verifique su usuario o contraseña (use contraseña de aplicación en Gmail).', 'danger')
                    print("[SMTP] Error de autenticación: credenciales no válidas.")

                except Exception as exc:
                    flash(f' Error al conectar con el servidor SMTP: {exc}', 'danger')
                    print(f"[SMTP] Error al probar conexión SMTP: {exc}")


        elif action == 'update_recipients':
            # Actualizar solo destinatarios, sin validar campos de servidor
            try:
                smtp_conf.smtp_sender1 = form.sender1.data
                smtp_conf.smtp_sender2 = form.sender2.data
                db.session.commit()
                flash('Destinatarios SMTP actualizados correctamente', 'success')
                print("[SMTP] Destinatarios actualizados correctamente.")
            except Exception as exc:
                print(f"[SMTP] Error al actualizar destinatarios: {exc}")
                flash(f'Error al actualizar destinatarios SMTP: {exc}', 'danger')

        return redirect(url_for('smtp.configure_smtp'))



        
@smtp.route("/smtpTest", methods=['POST'])
@flask_login.login_required
def smtp_test():
    '''Enviar correo de prueba SMTP'''
    if request.method == 'POST':
        results = request.form.to_dict()
        subject = 'Mensaje de prueba Sistema de Monitoreo'
        message = 'Mensaje de prueba Sistema de Monitoreo'

        try:
            send_smtp_message([results['recipient']],subject=subject, message=message)
            flash('Mensaje de prueba SMTP enviado correctamente', 'success')
        except Exception as exc:
            flash('Error al enviar el mensaje de prueba SMTP: {}'.format(exc), 'danger')

    return redirect(url_for('smtp.configure_smtp'))


# Funciones ##############
def send_smtp_message(recipients, subject, message, images=None):
    """
    Envía un correo vía SMTP. Soporta HTML y opcionalmente imágenes embebidas.
    - recipients: str o lista de destinatarios
    - subject: asunto del correo
    - message: cuerpo del correo (texto o HTML)
    - images: lista opcional de diccionarios con {'path': ruta_imagen, 'cid': id_unico}
    """
    smtp_conf = json.loads(get_smtp_config())
    smtp_ok = json.loads(get_smtp_configured()).get("smtp_configured", False)

    if not smtp_ok:
        log.error('Intentando enviar correo SMTP, pero el servidor SMTP no está configurado.')
        return

    # Asegurar lista de destinatarios
    if isinstance(recipients, str):
        recipients = [recipients]

    # Construcción base del mensaje
    msg = MIMEMultipart("related")
    msg["Subject"] = subject
    msg["From"] = smtp_conf.get("smtp_sender1") or smtp_conf.get("smtp_user")
    msg["To"] = ", ".join(recipients)

    alt = MIMEMultipart("alternative")
    msg.attach(alt)

    # Versión texto plano y HTML
    alt.attach(MIMEText("Mensaje del sistema de monitoreo", "plain", "utf-8"))
    alt.attach(MIMEText(message, "html", "utf-8"))

    # Adjuntar imágenes embebidas (si existen)
    if images:
        for img in images:
            try:
                buffer = procesar_imagen_para_email(img["path"])
                mime_img = MIMEImage(buffer.read(), _subtype="jpeg")
                mime_img.add_header("Content-ID", f"<{img['cid']}>")
                mime_img.add_header("Content-Disposition", "inline", filename=os.path.basename(img["path"]))
                msg.attach(mime_img)
            except Exception as e:
                log.error(f"No se pudo adjuntar imagen {img['path']}: {e}")

    # Envío
    try:
        with smtplib.SMTP(smtp_conf["smtp_server"], int(smtp_conf["smtp_port"]), timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()

            user = smtp_conf.get("smtp_user")
            password = smtp_conf.get("smtp_password")

            if user and password:
                server.login(user, password)

            server.sendmail(msg["From"], recipients, msg.as_string())
            log.info(f"Correo SMTP enviado correctamente a {recipients}")
    except Exception as e:
        log.error(f"Error al enviar correo SMTP: {e}")
        print(f"[SMTP] ❌ Error durante el envío: {e}")
        raise

