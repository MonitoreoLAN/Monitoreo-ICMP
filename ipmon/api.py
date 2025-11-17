'''Modulo API '''
import os
import sys
import json

from flask import Blueprint
from ipmon import db
from ipmon.database import Hosts, Polling, PollHistory, WebThemes, Users, SmtpServer, HostAlerts, AppConfig
from ipmon.schemas import Schemas

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')
api = Blueprint('api', __name__)

#####################
# Rutas API ########
#####################
@api.route('/hosts', methods=['GET'])
def get_all_hosts():
    '''Obtener todos los hosts'''
    return json.dumps(Schemas.hosts(many=True).dump(Hosts.query.all()))

@api.route('/hosts/<id>', methods=['GET'])
def get_host(_id):
    '''Obtener Host por ID'''
    return json.dumps(Schemas.hosts(many=False).dump(Hosts.query.filter_by(id=_id).first()))

@api.route('/hostsDataTable', methods=['GET'])
def get_all_hosts_datatable():
    '''Obtener todos los hosts'''
    data = {
        "columns": [
            { "data": "hostname", "title": "Hostname" },
            { "data": "ip_address", "title": "IP Address" },
            { "data": "last_poll", "title": "Last Poll" },
            { "data": "status", "title": "Status" }
        ],
        "data": Schemas.hosts(many=True).dump(Hosts.query.all())
    }
    return json.dumps(data)

@api.route('/hostAlerts', methods=['GET'])
def get_all_host_alerts():
    '''Obtener todas las alertas de los hosts'''
    return json.dumps(Schemas.host_alerts(many=True).dump(HostAlerts.query.join(Hosts).all()))

@api.route('/hostAlerts/new', methods=['GET'])
def get_new_host_alerts():
    '''Obtener nuevas alertas de los hosts'''
    return json.dumps(Schemas.host_alerts(many=True).dump(HostAlerts.query.filter_by(alert_cleared=False)))

@api.route('/pollingConfig', methods=['GET'])
def get_polling_config():
    '''Obtener configuración de consultas'''
    return json.dumps(Schemas.polling_config().dump(Polling.query.filter_by(id=1).first()))

@api.route('/pollHistory/<host_id>', methods=['GET'])
def get_poll_history(host_id):
    '''Obtener el historial de consultas de un solo host'''
    return json.dumps(Schemas.poll_history(many=True).dump(PollHistory.query.filter_by(host_id=host_id)))

# TODO Should check this by user id
@api.route('/alertsEnabled', methods=['GET'])
def get_alerts_enabled():
    '''Get whether alerts are enabled or not'''
    status = Schemas.users(many=False).dump(Users.query.first())['alerts_enabled']
    return json.dumps({'alerts_enabled': status})

@api.route('/smtpConfigured', methods=['GET'])
def get_smtp_configured():
    '''Obtener si SMTP está configurado o no'''
    config = json.loads(get_smtp_config())
    if config['smtp_server'] and config['smtp_port'] and (config['smtp_user'] or config['smtp_password']):
        return json.dumps({'smtp_configured': True})
    return json.dumps({'smtp_configured': False})

@api.route('/smtpConfig', methods=['GET'])
def get_smtp_config():
    '''Obtener configuración SMTP'''
    return json.dumps(Schemas.smtp_config().dump(SmtpServer.query.first()))

@api.route('/webThemes', methods=['GET'])
def get_web_themes():
    '''Obtener todos los temas web'''
    return json.dumps(Schemas.web_themes(many=True).dump(WebThemes.query.all()))

@api.route('/webThemes/active', methods=['GET'])
def get_active_theme():
    '''Obtener el Tema activo'''
    return json.dumps(Schemas.web_themes(many=False).dump(WebThemes.query.filter_by(active=True).first()))

@api.route('/hostCounts', methods=['GET'])
def get_host_counts():
    '''Obtener el total de hosts, hosts disponibles y hosts no disponibles'''
    total = Hosts.query.count()
    num_up = Hosts.query.filter(Hosts.status == 'Up').count()
    num_down = Hosts.query.filter(Hosts.status == 'Down').count()

    return json.dumps({'total_hosts': total, 'available_hosts': num_up, 'unavailable_hosts': num_down})

@api.route('/hosts/all', methods=['DELETE'])
def delete_all_hosts():
    '''Eliminar todos los hosts'''
    Hosts.query.delete()
    HostAlerts.query.delete()
    PollHistory.query.delete()

    db.session.commit()

    return json.dumps({'status': 'success'})
