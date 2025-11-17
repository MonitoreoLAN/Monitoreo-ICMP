'''Archivo de inicio del paquete'''
import os
import logging
import flask_login
import tempfile
import time
import uuid
import threading

from password_strength import PasswordPolicy
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler

config = {
    'Database_Path': os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'database',
        'ipmon.db'
    ),
    'Web_Themes': {
        'Darkly (Dark/Dark Blue)': '/static/css/darkly.min.css',
        'Cyborg (Dark/Light Blue)': '/static/css/cyborg.min.css',
        'Slate (Dark/Grey)': '/static/css/slate.min.css',
        'Simplix (Light/Red)': '/static/css/simplix.min.css',
        'Flatly (Light/Dark Blue)': '/static/css/flatly.min.css'
    },
    'Password_Policy': {
        'Length': 8,
        'Uppercase': 1,
        'Nonletters': 2
    },
    'Max_Threads': 100
}

# Aplicación web
app = Flask(__name__)
app.secret_key = str(uuid.UUID(int=uuid.getnode()))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}'.format(config['Database_Path'])

# BASE DATOS
db = SQLAlchemy()
db.init_app(app)

# Migración de base de datos
migrate = Migrate(app, db)

# Scheduler
scheduler = BackgroundScheduler()

# Administrador de autenticación
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

# Crear logger
log = logging.getLogger('IPMON')

if not log.handlers:  #  evita duplicar handlers si ya está configurado
    log.setLevel(logging.INFO)

    console = logging.StreamHandler()
    console_format = '%(asctime)s [%(levelname)s] - %(message)s'
    console.setFormatter(logging.Formatter(console_format, '%Y-%m-%d %H:%M:%S'))
    log.addHandler(console)

    logfile = os.path.join(
        tempfile.gettempdir(),
        f'IPMON_{time.strftime("%Y%m%d-%H%M%S")}.log'
    )
    file_handler = logging.FileHandler(logfile)
    logfile_format = '%(asctime)s [%(levelname)s] <%(filename)s:%(lineno)s> - %(message)s'
    file_handler.setFormatter(logging.Formatter(logfile_format, '%Y-%m-%d %H:%M:%S'))
    log.addHandler(file_handler)

# Registrar Blueprints ru
from ipmon.main import main as main_blueprint
from ipmon.auth import auth as auth_blueprint
from ipmon.smtp import smtp as smtp_blueprint
from ipmon.api import api as api_blueprint
from ipmon.hosts import hosts as hosts_blueprint
from ipmon.setup import bp as setup_blueprint
from ipmon.telegramconf import bp as telegramconf_blueprint
from ipmon.imagenes import imagenes_blueprint


app.register_blueprint(main_blueprint)
app.register_blueprint(auth_blueprint)
app.register_blueprint(smtp_blueprint)
app.register_blueprint(api_blueprint)
app.register_blueprint(hosts_blueprint)
app.register_blueprint(setup_blueprint)
app.register_blueprint(telegramconf_blueprint)
app.register_blueprint(imagenes_blueprint)

from ipmon.main import webapp_init
with app.app_context():
    webapp_init()

from ipmon import imagenes
def esperar_bd_y_iniciar_scheduler():
    """Espera a que la BD esté creada antes de iniciar el scheduler"""
    db_path = config['Database_Path']

    # Esperar hasta que exista el archivo físico de la base
    while not os.path.exists(db_path):
        log.warning(f"Esperando que se cree la base de datos: {db_path}")
        time.sleep(2)

    # Opcional: esperar hasta que las tablas estén listas
    try:
        from ipmon.database import Hosts  # o cualquier tabla conocida
        with app.app_context():
            # Ejecuta una consulta mínima para probar la conexión
            Hosts.query.first()
        log.info("Base de datos lista. Iniciando scheduler...")
    except Exception as e:
        log.error(f"La base existe pero no está inicializada: {e}")
        return

    # Ahora sí iniciar el scheduler
    try:
        from ipmon.imagenes import init_scheduler
        init_scheduler()
        scheduler.start()
        imagenes.init_scheduler()
        log.info("Scheduler inicializado correctamente después de crear la BD.")
    except Exception as e:
        log.error(f"Error al iniciar scheduler: {e}")

# Ejecutar en un hilo para no bloquear el arranque de Flask
threading.Thread(target=esperar_bd_y_iniciar_scheduler, daemon=True).start()