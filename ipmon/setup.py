'''Configuración de la aplicación web'''
import os
import sys

from flask import Blueprint, render_template, request, flash, redirect, url_for
from sqlalchemy import create_engine
from passlib.hash import sha256_crypt

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')
from ipmon import db, config, app
from ipmon.database import Users, Polling, SmtpServer, WebThemes, AppConfig
from ipmon.forms import FirstTimeSetupForm
from ipmon.main import init_schedulers, database_configured
from ipmon.auth import test_password

bp = Blueprint('setup', __name__)

@bp.route('/setup', methods=['GET', 'POST'])
def setup():
    form = FirstTimeSetupForm()
    if request.method == 'GET':
        if database_configured():
            return redirect(url_for('main.index'))
        return render_template('setup.html', form=form)
    elif request.method == 'POST':
        if form.validate_on_submit():
            errors = 0
            if form.password.data != form.verify_password.data:
                flash('Passwords did not match', '')
                errors += 1

            if test_password(form.password.data):
                reqs = form.password.description
                flash('Password did not meet {}'.format(reqs), 'danger')
                errors += 1

            if errors:
                return redirect(url_for('setup.setup'))

        else:
            for dummy, errors in form.errors.items():
                for error in errors:
                    flash(error, 'danger')
            return redirect(url_for('setup.setup'))

        # Crear base de datos
        database_file = app.config['SQLALCHEMY_DATABASE_URI']
        database_directory = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'database'
        )
        if not os.path.exists(database_directory):
            os.makedirs(database_directory)
        engine = create_engine(database_file, echo=True)
        db.Model.metadata.create_all(engine)

        # Crear usuario administrador
        admin_user = Users(email=form.email.data, username=form.username.data, password=sha256_crypt.hash(form.password.data))
        db.session.add(admin_user)

        # Establecer intervalo de sconsultas
        poll = Polling(poll_interval=form.poll_interval.data, history_truncate_days=form.retention_days.data)
        db.session.add(poll)

        # Configurar el servidor STMP
        smtp = SmtpServer(smtp_server=form.smtp_server.data, smtp_port=form.smtp_port.data, smtp_sender1=form.smtp_sender1.data, smtp_sender2=form.smtp_sender2.data,smtp_user=form.smtp_user.data, smtp_password=form.smtp_password.data)
        db.session.add(smtp)
        
        # Configuración APP
        appconf = AppConfig(telegram_token=form.telegram_token.data, telegram_chat_id=form.telegram_chat_id.data, stable_cycles=form.stable_cycles.data)
        db.session.add(appconf)

        # Agregar temas web
        for i, theme in enumerate(config['Web_Themes']):
            active = False
            if i == 0:
                active = True
            web_theme = WebThemes(theme_name=theme, theme_path=config['Web_Themes'][theme], active=active)
            db.session.add(web_theme)


        # Commit actualizaciones de base de datos
        db.session.commit()

        # Inicializar programadores
        init_schedulers()

        return redirect(url_for('main.index'))
