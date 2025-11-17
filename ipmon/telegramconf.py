import requests
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app as app
from flask_login import login_required
from ipmon.forms import TelegramConfigForm
from ipmon.database import AppConfig
from ipmon import db

bp = Blueprint('telegram', __name__)

@bp.route('/config/telegram', methods=['GET', 'POST'])
@login_required
def config_telegram():
    form = TelegramConfigForm()
    app_conf = AppConfig.query.first()

    if form.validate_on_submit():
        if not app_conf:
            app_conf = AppConfig()
            db.session.add(app_conf)

        app_conf.telegram_token = form.telegram_token.data
        app_conf.telegram_chat_id = form.telegram_chat_id.data
        db.session.commit()

        flash("Configuración de Telegram actualizada correctamente.", "success")
        app.logger.info("✅ Configuración de Telegram actualizada: Token y Chat ID guardados.")
        return redirect(url_for('telegram.config_telegram'))

    # 🔹 Siempre dejar inputs vacíos
    form.telegram_token.data = ""
    form.telegram_chat_id.data = ""

    return render_template('telegramconf.html', form=form, app_conf=app_conf)


@bp.route('/config/telegram/delete', methods=['POST'])
@login_required
def delete_telegram_config():
    app_conf = AppConfig.query.first()
    if app_conf:
        app_conf.telegram_token = None
        app_conf.telegram_chat_id = None
        db.session.commit()
        flash("Datos de Telegram borrados correctamente.", "success")
        app.logger.info("🗑️ Configuración de Telegram eliminada correctamente.")
    else:
        flash("No hay datos de Telegram para borrar.", "warning")
        app.logger.warning("⚠️ Intento de eliminar configuración inexistente.")
    return redirect(url_for('telegram.config_telegram'))


# ✅ Prueba con datos guardados en la BD
@bp.route('/config/telegram/test', methods=['POST'])
@login_required
def test_telegram():
    app_conf = AppConfig.query.first()
    if not app_conf or not app_conf.telegram_token or not app_conf.telegram_chat_id:
        flash("No hay configuración de Telegram para hacer la prueba.", "warning")
        app.logger.warning("⚠️ No hay configuración guardada en la BD para la prueba.")
        return redirect(url_for('telegram.config_telegram'))

    url = f"https://api.telegram.org/bot{app_conf.telegram_token}/sendMessage"
    data = {
        "chat_id": app_conf.telegram_chat_id,
        "text": "Este es un mensaje de prueba desde Centro de Monitoreo (BD)"
    }

    app.logger.info(f"📤 Enviando prueba BD → Chat ID: {data['chat_id']}, Token: {app_conf.telegram_token[:10]}...")

    try:
        response = requests.post(url, data=data)
        app.logger.info(f"📨 Respuesta Telegram (BD): {response.status_code} - {response.text}")
        if response.status_code == 200:
            flash("Mensaje de prueba enviado correctamente (BD).", "success")
        else:
            flash(f"Error al enviar el mensaje (BD). Código: {response.status_code}", "danger")
    except Exception as e:
        flash(f"Error al enviar el mensaje (BD): {e}", "danger")
        app.logger.error(f"❌ Error al enviar mensaje BD: {e}")

    return redirect(url_for('telegram.config_telegram'))


# ✅ Prueba manual con datos ingresados en el formulario
@bp.route('/config/telegram/test_manual', methods=['POST'])
@login_required
def test_telegram_manual():
    token = request.form.get("telegram_token")
    chat_id = request.form.get("telegram_chat_id")
    mensaje = request.form.get("mensaje", "Este es un mensaje de prueba manual desde Centro de Monitoreo")

    app.logger.info(f"📋 Datos recibidos manualmente → Token: {token[:10]}..., Chat ID: {chat_id}, Mensaje: {mensaje}")

    if not token or not chat_id:
        flash("Debes ingresar un token y un chat_id para la prueba manual.", "warning")
        app.logger.warning("⚠️ Prueba manual fallida: faltan token o chat_id.")
        return redirect(url_for('telegram.config_telegram'))

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": mensaje
    }

    try:
        response = requests.post(url, data=data)
        app.logger.info(f"📨 Respuesta Telegram (Manual): {response.status_code} - {response.text}")
        if response.status_code == 200:
            flash("Mensaje manual enviado correctamente.", "success")
        else:
            flash(f"Error al enviar el mensaje manual. Código: {response.status_code}", "danger")
    except Exception as e:
        flash(f"Error al enviar el mensaje manual: {e}", "danger")
        app.logger.error(f"❌ Error al enviar mensaje manual: {e}")

    return redirect(url_for('telegram.config_telegram'))





