'''Esquemas utilizados para APIs'''
from marshmallow import Schema, fields, pre_dump

class UsersSchema(Schema):
    '''Esquema de usuarios'''
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)
    email = fields.Email(required=True)
    date_created = fields.DateTime(dump_only=True)
    alerts_enabled = fields.Bool(load_default=True)  

class HostsSchema(Schema):
    '''Esquema de Hosts'''
    id = fields.Int(dump_only=True)
    ip_address = fields.Str(required=True)
    hostname = fields.Str()
    ciudad = fields.Str()
    cto = fields.Str()
    dispositivo = fields.Str()
    tipo = fields.Str()
    snapshot_url = fields.Url(allow_none=True)
    status = fields.Str(dump_only=True)
    last_poll = fields.Str(dump_only=True)
    status_change_alert = fields.Bool(load_default=False)  
    previous_status = fields.Str(dump_only=True)
    alerts_enabled = fields.Bool(load_default=True)  
    last_alert_status = fields.Str(dump_only=True)

class PollHistorySchema(Schema):
    '''Esquema del historial de sondeos'''
    id = fields.Int(dump_only=True)
    host_id = fields.Int(required=True)
    poll_time = fields.Str(required=True)
    poll_status = fields.Str(required=True)
    date_created = fields.DateTime(dump_only=True)

class HostAlertsSchema(Schema):
    '''Esquema de alertas del host'''
    id = fields.Int(dump_only=True)
    hostname = fields.Str(required=True)
    ip_address = fields.Str(required=True)
    host_status = fields.Str(required=True)
    poll_time = fields.Str(required=True)
    alert_cleared = fields.Bool(load_default=False)  # ← Cambiado
    date_created = fields.DateTime(dump_only=True)
    host_id = fields.Int(required=True)

class PollingConfigSchema(Schema):
    '''Esquema de sondeo'''
    id = fields.Int(dump_only=True)
    poll_interval = fields.Int(required=True)
    history_truncate_days = fields.Int(required=True)

class SmtpConfigSchema(Schema):
    '''Esquema SMTP'''
    id = fields.Int(dump_only=True)
    smtp_server = fields.Str(required=True)
    smtp_port = fields.Int(required=True)
    smtp_user = fields.Str(required=True)
    smtp_password = fields.Str(required=True)
    smtp_sender1 = fields.Email(required=True)
    smtp_sender2 = fields.Email(allow_none=True)
    @pre_dump
    def handle_smtp_port(self, data, **kwargs):
        """Convertir smtp_port vacío a None antes de serializar"""
        if hasattr(data, 'smtp_port') and data.smtp_port == '':
            data.smtp_port = None
        return data

class WebThemesSchema(Schema):
    '''Esquema Temas Web'''
    id = fields.Int(dump_only=True)
    theme_name = fields.Str(required=True)
    theme_path = fields.Str(required=True)
    active = fields.Bool(load_default=False)  # ← Cambiado

class AppConfigSchema(Schema):
    """Esquema para configuración general"""
    id = fields.Int(dump_only=True)
    telegram_token = fields.Str(allow_none=True)
    telegram_chat_id = fields.Str(allow_none=True)
    stable_cycles = fields.Int(load_default=3)  # ← Cambiado

class SchedulerConfigSchema(Schema):
    """Esquema de configuración del scheduler"""
    id = fields.Int(dump_only=True)
    enabled = fields.Bool(load_default=True)  # ← Cambiado
    frequency = fields.Str(required=True)
    time = fields.Str(allow_none=True)
    weekdays = fields.Str(allow_none=True)

class Schemas():
    '''Métodos estáticos para acceder a esquemas'''

    @staticmethod
    def users(many=True):
        return UsersSchema(many=many)

    @staticmethod
    def hosts(many=True):
        return HostsSchema(many=many)

    @staticmethod
    def poll_history(many=True):
        return PollHistorySchema(many=many)

    @staticmethod
    def host_alerts(many=True):
        return HostAlertsSchema(many=many)

    @staticmethod
    def polling_config():
        return PollingConfigSchema()

    @staticmethod
    def smtp_config():
        return SmtpConfigSchema()

    @staticmethod
    def web_themes(many=True):
        return WebThemesSchema(many=many)
    
    @staticmethod
    def app_config():
        return AppConfigSchema()
    
    @staticmethod
    def scheduler_config():
        return SchedulerConfigSchema()