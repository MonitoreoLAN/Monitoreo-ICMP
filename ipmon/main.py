'''Aplicación web principal'''
import os
import sys
import json
import atexit

import flask_login
from flask import Blueprint, render_template, request, flash, redirect, url_for, send_from_directory
from werkzeug.exceptions import HTTPException

from ipmon.imagenes import reload_schedule

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')
from ipmon import db, app, scheduler, config, log
from ipmon.api import get_web_themes, get_polling_config, get_active_theme
from ipmon.database import Polling, SchedulerConfig, WebThemes,AppConfig
from ipmon.forms import PollingConfigForm, UpdatePasswordForm, UpdateEmailForm, TelegramConfigForm
from ipmon.polling import update_poll_scheduler, add_poll_history_cleanup_cron
from ipmon.alerts import update_host_status_alert_schedule
from wtforms.validators import NumberRange

main = Blueprint('main', __name__)

#####################
# Programar tareas #####
#####################
def webapp_init():
    # Gestionar el error al registrar
    for cls in HTTPException.__subclasses__():
        app.register_error_handler(cls, handle_error)

    if not database_configured():
        return

    init_schedulers()

#####################
# Rutas de la App #######
#####################
@main.route('/favicon.ico')
def favicon():
    '''Favicon'''
    return send_from_directory(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static', 'Iconos'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@main.route('/')
def index():
    '''Pagina Principal'''
    if not os.path.exists(config['Database_Path']):
        return redirect(url_for('setup.setup'))
    return render_template('index.html', refresh_interval=30000)

@main.route("/account")
@flask_login.login_required
def account():
    '''Cuenta de Usuario'''
    password_form = UpdatePasswordForm()
    email_form = UpdateEmailForm()
    return render_template('account.html', password_form=password_form, email_form=email_form)

@main.route("/configuracion", methods=["GET", "POST"])
@flask_login.login_required
def configuracion_general():
    config = SchedulerConfig.query.first()

    if request.method == "POST":
        form_type = request.form.get("form_type")

        if form_type == "theme":
            # Lógica de cambio de tema
            try:
                results = request.form.to_dict()
                for theme in json.loads(get_web_themes()):
                    theme_obj = WebThemes.query.filter_by(id=int(theme['id'])).first()
                    theme_obj.active = (theme_obj.id == int(results['id']))
                db.session.commit()
                flash("Tema actualizado correctamente", "success")
            except Exception as e:
                flash(f"Error al actualizar el tema: {e}", "danger")

        elif form_type == "scheduler":
            enabled = bool(request.form.get("enabled"))
            frequency = request.form.get("frequency", "daily")
            time_value = request.form.get("time", "09:00").strip()
            weekdays = request.form.getlist("weekdays")

            if not config:
                config = SchedulerConfig()

            config.enabled = enabled
            config.frequency = frequency
            config.time = time_value
            config.weekdays = ",".join(weekdays)

            db.session.add(config)
            db.session.commit()

            reload_schedule()
            flash("✅ Configuración guardada en BD y scheduler actualizado.", "success")

        return redirect(url_for("main.configuracion_general"))

    return render_template("configuracion.html",
                           themes=json.loads(get_web_themes()),
                           config=config)

@main.route('/configurePolling', methods=['GET', 'POST'])
@flask_login.login_required
def configure_polling():
    """Intervalo de sondeo"""
    form = PollingConfigForm()

    if request.method == 'GET':
        polling_config = json.loads(get_polling_config())
        app_config = AppConfig.query.first()
        return render_template(
            'pollingConfig.html',
            polling_config=polling_config,
            app_config=app_config,
            form=form
        )

    elif request.method == 'POST':
        if form.validate_on_submit():
            polling_config = Polling.query.first()
            app_config = AppConfig.query.first()
            try:
                # Actualizar solo los campos que vienen con datos
                if form.interval.data:
                    polling_config.poll_interval = int(form.interval.data)
                if form.retention_days.data:
                    polling_config.history_truncate_days = int(form.retention_days.data)
                if form.stable_cycles.data:
                    app_config.stable_cycles = int(form.stable_cycles.data)

                db.session.commit()

                # ⚡ Actualizar el scheduler en caliente
                if form.interval.data:
                    new_interval = int(form.interval.data)
                    update_poll_scheduler(new_interval)
                    log.info(f" Intervalo de sondeo actualizado dinámicamente a {new_interval} segundos.")
                else:
                    current_interval = polling_config.poll_interval
                    update_poll_scheduler(current_interval)
                    log.info(f" Reprogramado con intervalo actual de {current_interval} segundos (sin cambios).")

                flash('Intervalo de sondeo actualizado correctamente', 'success')

            except Exception as e:
                log.error(f"Error al actualizar el intervalo de sondeo: {e}")
                flash('Error al actualizar el intervalo de sondeo', 'danger')
                return redirect(url_for('main.configure_polling'))

        else:
            for dummy, errors in form.errors.items():
                for error in errors:
                    flash(error, 'danger')

        return redirect(url_for('main.configure_polling'))

##########################
# Funciones ##############
##########################
def handle_error(error):
    '''Controlador global de errores'''
    code = 500
    desc = 'Internal Server Error'
    if isinstance(error, HTTPException):
        code = error.code
        desc = error.description
    return render_template('error.html', code=code, desc=desc)

def init_schedulers():
    # Register scheduler jobs
    update_poll_scheduler(int(json.loads(get_polling_config())['poll_interval']))
    update_host_status_alert_schedule(int(json.loads(get_polling_config())['poll_interval']) / 2)
    add_poll_history_cleanup_cron()
    atexit.register(scheduler.shutdown)

##########################
# Custom Jinja Functions #
##########################
def get_active_theme_path():
    '''Obtener la ruta del archivo del tema activo'''
    if not database_configured():
        return '/static/css/darkly.min.css'
    return json.loads(get_active_theme())['theme_path']
app.add_template_global(get_active_theme_path, name='get_active_theme_path')

def database_configured():
    '''Comprobar si la base de datos está configurada.'''
    return os.path.exists(config['Database_Path'])
app.add_template_global(database_configured, name='database_configured')

