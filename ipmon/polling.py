'''Biblioteca de sondeo del host con icmplib'''
import os
import sys
import time
import json

from datetime import date, timedelta
from icmplib import multiping, ping
from ipmon import app, db, scheduler, log
from ipmon.database import Hosts, PollHistory, HostAlerts
from ipmon.api import get_all_hosts, get_host, get_polling_config, get_poll_history
from ipmon.helpers import get_stable_cycles, get_hostname 

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')

# --- FUNCION DE COMPATIBILIDAD (para agregar/verificar un solo host) ---
def poll_host(host, new_host=False, count=1):
    """Sondea un host individual usando icmplib"""
    hostname = None
    try:
        res = ping(host, count=count, timeout=1, interval=0.2)
        status = 'Up' if res.is_alive else 'Down'
        if new_host:
            hostname = get_hostname(host)
        return (status, time.strftime('%Y-%m-%d %T'), hostname)
    except Exception:
        return ('Down', time.strftime('%Y-%m-%d %T'), hostname)


def update_poll_scheduler(poll_interval):
    '''Actualiza la programación de sondeo de hosts mediante APScheduler'''
    try:
        scheduler.remove_job('Poll Hosts')
    except Exception:
        pass

    scheduler.add_job(
        id='Poll Hosts',
        func=_poll_hosts_threaded,
        trigger='interval',
        seconds=int(poll_interval),
        max_instances=1
    )


def add_poll_history_cleanup_cron():
    '''Agrega crong job para la limpieza del historial de sondeo'''
    scheduler.add_job(
        id='Poll History Cleanup',
        func=_poll_history_cleanup_task,
        trigger='cron',
        hour='0',
        minute='30'
    )



# Diccionario global (puede ir al inicio de polling.py)
stable_cycles = {}  # clave: host_id, valor: {'status': 'Up'/'Down', 'count': int}

def _poll_hosts_threaded():
    """Sondea hosts por lotes y genera alertas solo cuando el estado se estabiliza."""
    log.debug('Starting host polling (icmplib)')
    s = time.perf_counter()

    import time as t

    REQUIRED_STABLE_CYCLES = get_stable_cycles()
    MAX_BATCH_SIZE = 200
    WAIT_BETWEEN_BATCHES = 1

    def chunk_list(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    def analizar_historial_estados(host_id, current_status):
        """Verifica los últimos N ciclos para determinar estabilidad."""
        history = PollHistory.query.filter_by(host_id=host_id) \
            .order_by(PollHistory.date_created.desc()) \
            .limit(REQUIRED_STABLE_CYCLES).all()
        if len(history) < REQUIRED_STABLE_CYCLES:
            return 0
        estados = [h.poll_status for h in history][::-1]
        stable_count = sum(1 for e in estados if e == current_status)
        return stable_count

    with app.app_context():
        all_hosts = json.loads(get_all_hosts())
        batches = list(chunk_list(all_hosts, MAX_BATCH_SIZE))

        for i, batch in enumerate(batches):
            ips = [h['ip_address'] for h in batch]

            try:
                results = multiping(ips, count=1, timeout=1, interval=0.2, concurrent_tasks=50)
            except Exception as e:
                log.error(f"Error en multiping: {e}")
                continue

            poll_time = time.strftime('%Y-%m-%d %T')

            for host_obj, host_data in zip(results, batch):
                status = 'Up' if host_obj.is_alive else 'Down'
                host = Hosts.query.filter_by(id=int(host_data['id'])).first()
                if not host:
                    continue

                previous_status = host.status
                host.previous_status = previous_status
                host.status = status
                host.last_poll = poll_time

                # Guardar historial
                new_poll_history = PollHistory(
                    host_id=host.id,
                    poll_time=poll_time,
                    poll_status=status
                )
                db.session.add(new_poll_history)
                db.session.commit()  # commit temprano para analizar historial

                # Analizar estabilidad
                stable_count = analizar_historial_estados(host.id, status)

                if stable_count >= REQUIRED_STABLE_CYCLES:
                    # Alertar solo si el último estado alertado es diferente
                    if host.alerts_enabled and host.last_alert_status != status:
                        host_alert = HostAlerts(
                            host_id=host.id,
                            hostname=host.hostname,
                            ip_address=host.ip_address,
                            host_status=status,
                            poll_time=poll_time
                        )
                        db.session.add(host_alert)
                        host.last_alert_status = status
                        db.session.commit()
                        log.info(f"Alerta enviada para {host.hostname}: {status} ({stable_count}/{REQUIRED_STABLE_CYCLES} ciclos estables)")
                else:
                    log.info(f"Cambio descartado para {host.hostname}: {previous_status} -> {status} (solo {stable_count}/{REQUIRED_STABLE_CYCLES} ciclos estables)")

            if i < len(batches) - 1:
                log.debug(f"Esperando {WAIT_BETWEEN_BATCHES}s antes del siguiente lote...")
                t.sleep(WAIT_BETWEEN_BATCHES)

    log.debug("Host polling finished in {} seconds.".format(time.perf_counter() - s))



def _poll_history_cleanup_task():
    log.debug('Starting poll history cleanup')
    s = time.perf_counter()

    with app.app_context():
        retention_days = json.loads(get_polling_config())['history_truncate_days']
        current_date = date.today()

        PollHistory.query.filter(
            PollHistory.date_created < (current_date - timedelta(days=retention_days))
        ).delete()

        db.session.commit()

    log.debug("Poll history cleanup finished in {} seconds.".format(time.perf_counter() - s))