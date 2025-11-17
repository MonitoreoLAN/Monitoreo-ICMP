'''Archivo de base de datos'''
import os
import sys
from datetime import datetime


sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')
from ipmon import db

##########################
# Modelos ###############
##########################

class Users(db.Model):
    """Tabla de Usuarios"""
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.now)
    alerts_enabled = db.Column(db.Boolean, default=True)


class Hosts(db.Model):
    """Tabla de Hosts"""
    __tablename__ = 'hosts'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(15), nullable=False, unique=True)
    hostname = db.Column(db.String(100))
    ciudad = db.Column(db.String(100))
    cto = db.Column(db.String(100))
    dispositivo = db.Column(db.String(100))  
    tipo = db.Column(db.String(100))         
    status = db.Column(db.String(10))
    last_poll = db.Column(db.String(20))
    previous_status = db.Column(db.String(10))
    alerts_enabled = db.Column(db.Boolean, default=True)

    # Puerto RTSP
    rtsp_port = db.Column(db.Integer)
    # Snapshot URL real en BD
    snapshot_url = db.Column(db.String(255), nullable=True)

    # Relaciones
    poll_history = db.relationship("PollHistory", back_populates="host", cascade="all, delete-orphan")
    alerts = db.relationship("HostAlerts", back_populates="host", cascade="all, delete-orphan")
    images = db.relationship("Images", back_populates="host", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Asignar puerto por defecto según tipo
        if self.rtsp_port is None:
            if self.tipo and self.tipo.lower() == "camara":
                self.rtsp_port = 554
            elif self.tipo and self.tipo.lower() == "safecity":
                self.rtsp_port = 555
            else:
                self.rtsp_port = 554  # puerto genérico si no se reconoce el tipo

        # Generar snapshot_url automáticamente
        self.generar_snapshot_url()

    def generar_snapshot_url(self):
        """Genera la URL RTSP y la guarda en snapshot_url"""
        # Valores por defecto
        rtsp_user = "admin"
        rtsp_password = "T3lc0n3tC@m"

        # Solo generamos URL para tipos de cámaras
        if self.tipo and self.tipo.lower() in ["camara", "safecity"]:
            self.snapshot_url = (
                f"rtsp://{rtsp_user}:{rtsp_password}@{self.ip_address}:{self.rtsp_port}/Streaming/Channels/101"
            )
        else:
            self.snapshot_url = None

    last_alert_status = db.Column(db.String(10), default=None)


class PollHistory(db.Model):
    """Historial de sondeo de dispositivos"""
    __tablename__ = 'poll_history'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    poll_time = db.Column(db.String(20))
    poll_status = db.Column(db.String(20))
    date_created = db.Column(db.DateTime, default=datetime.now)
    host_id = db.Column(db.Integer, db.ForeignKey('hosts.id'))

    # Relación inversa
    host = db.relationship("Hosts", back_populates="poll_history")


class HostAlerts(db.Model):
    """Alertas por cambio de estado del host"""
    __tablename__ = 'host_alerts'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    hostname = db.Column(db.String(100))
    ip_address = db.Column(db.String(15))
    host_status = db.Column(db.String(20))
    poll_time = db.Column(db.String(20))
    alert_cleared = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime, default=datetime.now)
    host_id = db.Column(db.Integer, db.ForeignKey('hosts.id'))

    # Relación inversa
    host = db.relationship("Hosts", back_populates="alerts")


class Polling(db.Model):
    """Configuración de sondeos"""
    __tablename__ = 'polling'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    poll_interval = db.Column(db.Integer, default=60, nullable=False)
    history_truncate_days = db.Column(db.Integer, default=10, nullable=False)


class SmtpServer(db.Model):
    """Configuración SMTP"""
    __tablename__ = 'smtp_server'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    smtp_server = db.Column(db.String(100), nullable=False)
    smtp_port = db.Column(db.Integer, nullable=True)
    smtp_user = db.Column(db.String(128), nullable=False, unique=True)
    smtp_password = db.Column(db.String(128), nullable=False)
    smtp_sender1 = db.Column(db.String(100), nullable=False)
    smtp_sender2 = db.Column(db.String(100), nullable=False, default='')


class WebThemes(db.Model):
    """Temas CSS para la web"""
    __tablename__ = 'web_themes'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    theme_name = db.Column(db.String(100), nullable=False)
    theme_path = db.Column(db.String(100), nullable=False)
    active = db.Column(db.Boolean, default=False)


class AppConfig(db.Model):
    """Configuración general de la aplicación"""
    __tablename__ = 'app_config'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    telegram_token = db.Column(db.String(255), nullable=True)
    telegram_chat_id = db.Column(db.String(50), nullable=True)
    stable_cycles = db.Column(db.Integer, nullable=False)


class Images(db.Model):
    """Imágenes asociadas a Hosts"""
    __tablename__ = 'images'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String(255), nullable=False)  # ruta local de la imagen
    host_id = db.Column(db.Integer, db.ForeignKey('hosts.id'), nullable=False)

    # Relación inversa
    host = db.relationship("Hosts", back_populates="images")


class SchedulerConfig(db.Model):
    """Configuracipon Scheduller"""
    __tablename__ = 'scheduler_config'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    enabled = db.Column(db.Boolean, default=True)
    frequency = db.Column(db.String(20), default="daily")   
    time = db.Column(db.String(10), default="00:00")        
    weekdays = db.Column(db.String, default="[]")           