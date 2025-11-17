'''Módulo de HOSTS'''
import os
import sys
import ipaddress
import platform
import subprocess
import json
import cv2
from multiprocessing.pool import ThreadPool

import flask_login
from flask import Blueprint, flash, redirect, render_template, request, url_for, jsonify, current_app, copy_current_request_context

from ipmon import db, log
from ipmon.api import get_all_hosts
from ipmon.database import HostAlerts, Hosts, PollHistory, Images
from ipmon.forms import AddHostsForm
from ipmon.polling import _poll_hosts_threaded, poll_host

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')

hosts = Blueprint('hosts', __name__)

######################
# Routes #############
######################

# Listar hosts 
@hosts.route('/')
def index():
    hosts_list = Hosts.query.all()
    return render_template('index.html', hosts=hosts_list)

# Agregar hosts 
@hosts.route('/addHosts', methods=['GET', 'POST'])
@flask_login.login_required
def add_hosts():
    '''Página para agregar dispositivos'''
    form = AddHostsForm()
    if request.method == 'GET':
        return render_template('addHosts.html', form=form)

    elif request.method == 'POST':
        if form.validate_on_submit():
            pool = ThreadPool(10)  # Ajustar número de threads según tu config
            threads = []

            # Obtener app explícitamente para pasar a los hilos
            app = current_app._get_current_object()

            for line in form.ip_address.data.strip().split('\n'):
                line = line.strip()
                if not line:
                    continue

                parts = line.split(',')
                ip_address = parts[0].strip()
                hostname = parts[1].strip() if len(parts) > 1 else ""
                ciudad = parts[2].strip() if len(parts) > 2 else ""
                cto = parts[3].strip() if len(parts) > 3 else ""
                dispositivo = parts[4].strip() if len(parts) > 4 else ""
                tipo = parts[5].strip() if len(parts) > 5 else ""

                # Validar dirección IP
                try:
                    ipaddress.IPv4Address(ip_address)
                except ipaddress.AddressValueError:
                    flash(f'{ip_address} no es una dirección IP válida.', 'danger')
                    continue

                # Verificar si ya existe
                if Hosts.query.filter_by(ip_address=ip_address).first():
                    flash(f'La dirección IP {ip_address} ya existe!.', 'danger')
                    continue

                # Encolar el proceso pasando app
                threads.append(
                    pool.apply_async(
                        _add_hosts_threaded,
                        (app, ip_address, hostname, ciudad, cto, dispositivo, tipo)
                    )
                )

            pool.close()
            pool.join()

            for thread in threads:
                try:
                    result = thread.get()
                    flash(f"Añadida exitosamente {result['ip_address']} ({result['hostname']})", 'success')
                except Exception as exc:
                    flash(f'Fallo al agregar host. Error: {exc}', 'danger')
                    log.error(f'Failed to add host to database. Exception: {exc}')
                    continue

        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(error, 'danger')

        return redirect(url_for('hosts.add_hosts'))

# Actualizar Hosts
@hosts.route('/updateHosts', methods=['GET', 'POST'])
@flask_login.login_required
def update_hosts():
    if request.method == 'GET':
        hosts_list = json.loads(get_all_hosts())
        tipos = sorted({h.get("tipo").strip() for h in hosts_list if h.get("tipo") and h.get("tipo").strip() != ""})
        log.info(f"Tipos disponibles para filtro: {tipos}")
        return render_template("updateHosts.html", hosts=hosts_list, tipos=tipos)

    elif request.method == 'POST':
        results = request.form.to_dict()
        host = Hosts.query.filter_by(id=int(results['id'])).first()

        try:
            old_ip = host.ip_address
            old_tipo = host.tipo

            host.hostname = results.get('hostname') or host.hostname
            host.ip_address = results.get('ip_address') or host.ip_address
            host.ciudad = results.get('ciudad') or host.ciudad
            host.cto = results.get('cto') or host.cto
            host.dispositivo = results.get('dispositivo') or host.dispositivo
            host.tipo = results.get('tipo') or host.tipo

            manual_url = results.get('snapshot_url', '').strip()
            if manual_url:
                host.snapshot_url = manual_url
            else:
                if host.ip_address != old_ip or host.tipo != old_tipo:
                    host.generar_snapshot_url()

            if 'alerts' in results:
                host.alerts_enabled = results['alerts'] == 'True'

            db.session.commit()
            flash(f'Dispositivo actualizado correctamente: {host.hostname}', 'success')

        except Exception as e:
            flash(f'Fallo al actualizar la información del dispositivo {host.hostname}: {e}', 'danger')

        return redirect(url_for('hosts.update_hosts'))

# Función privada para eliminación centralizada
def _delete_host_with_dependencies(host):
    """Elimina un host y todas sus dependencias (imágenes, historiales, alertas)."""
    try:
        # Eliminar imágenes asociadas
        images = Images.query.filter_by(host_id=host.id).all()
        for img in images:
            try:
                absolute_path = os.path.join(current_app.root_path, 'static', img.file_path)
                if os.path.exists(absolute_path):
                    os.remove(absolute_path)
                    log.info(f"Imagen eliminada: {absolute_path}")
                else:
                    log.warning(f"Archivo no encontrado en disco: {absolute_path}")
            except Exception as e:
                log.warning(f"No se pudo eliminar la imagen {img.file_path}: {e}")

        # Eliminar dependencias en BD
        PollHistory.query.filter_by(host_id=host.id).delete()
        HostAlerts.query.filter_by(host_id=host.id).delete()
        Images.query.filter_by(host_id=host.id).delete()
        Hosts.query.filter_by(id=host.id).delete()

        return True
    except Exception as e:
        log.error(f"Error eliminando host {host.hostname}: {e}")
        return False

# Eliminar hosts
@hosts.route('/deleteHost', methods=['POST'])
@flask_login.login_required
def delete_host():
    results = request.form.to_dict()
    host_id = int(results['id'])
    host = Hosts.query.filter_by(id=host_id).first()
    if not host:
        flash("⚠️ Host no encontrado.", "warning")
        return redirect(url_for('hosts.update_hosts'))

    if _delete_host_with_dependencies(host):
        db.session.commit()
        flash(f"✅ Dispositivo eliminado exitosamente: {results['hostname']}", "success")
        cleanup_orphan_images()
    else:
        flash(f"❌ No se pudo eliminar el dispositivo {results['hostname']}", "danger")

    return redirect(url_for('hosts.update_hosts'))

# Eliminar TODOS los hosts
@hosts.route('/deleteAllHosts', methods=['POST'])
@flask_login.login_required
def delete_all_hosts():
    try:
        all_hosts = Hosts.query.all()
        for host in all_hosts:
            _delete_host_with_dependencies(host)
        db.session.commit()
        flash("✅ Todos los hosts fueron eliminados correctamente.", "success")
        cleanup_orphan_images()
    except Exception as e:
        flash(f"❌ Error al eliminar todos los hosts: {e}", "danger")
    return redirect(url_for('hosts.update_hosts'))

# Eliminar SOLO hosts visibles (según filtro)
@hosts.route('/deleteVisibleHosts', methods=['POST'])
@flask_login.login_required
def delete_visible_hosts():
    try:
        ids = json.loads(request.form.get("ids", "[]"))
        if not ids:
            flash("⚠️ No se recibieron hosts para eliminar.", "warning")
            return redirect(url_for('hosts.update_hosts'))

        for host_id in ids:
            host = Hosts.query.filter_by(id=host_id).first()
            if host:
                _delete_host_with_dependencies(host)

        db.session.commit()
        flash(f"✅ Se eliminaron {len(ids)} hosts visibles.", "success")
        cleanup_orphan_images()
    except Exception as e:
        flash(f"❌ Error al eliminar hosts visibles: {e}", "danger")

    return redirect(url_for('hosts.update_hosts'))

# Forzar ping a host
@hosts.route('/forzar_ping/<int:host_id>', methods=['GET'])
def forzar_ping(host_id):
    host = Hosts.query.get_or_404(host_id)
    try:
        if platform.system().lower() == 'windows':
            comando = ['ping', '-n', '1', '-w', '1000', host.ip_address]
        else:
            comando = ['ping', '-c', '1', '-W', '1', host.ip_address]

        response = subprocess.run(comando, capture_output=True, text=True)
        salida = response.stdout.lower()

        if platform.system().lower() == 'windows':
            exito = "ttl=" in salida
        else:
            exito = (response.returncode == 0)

        if exito:
            return jsonify({"success": True, "message": f"Ping exitoso a {host.ip_address}"}), 200
        else:
            return jsonify({"success": False, "message": f"❌ Error al hacer ping a {host.ip_address}"}), 400

    except Exception as e:
        log.error(f"Error en forzar_ping para host {host.ip_address}: {e}")
        return jsonify({"success": False, "message": f"Excepción al hacer ping: {e}"}), 500


######################
# Funciones Privadas ##
######################
def _add_hosts_threaded(app, ip_address, hostname, ciudad, cto, dispositivo, tipo):
    """Crea un host, genera snapshot_url y captura imagen usando OpenCV"""
    with app.app_context():
        # Obtener estado inicial del host
        status, current_time, resolved_hostname = poll_host(ip_address, new_host=True)
        hostname = hostname if hostname else resolved_hostname

        # Crear el host
        new_host = Hosts(
            ip_address=ip_address,
            hostname=hostname,
            ciudad=ciudad,
            cto=cto,
            dispositivo=dispositivo,
            tipo=tipo,
            status=status,
            last_poll=current_time
        )
        db.session.add(new_host)
        db.session.commit()

        # Captura snapshot si existe URL
        if new_host.snapshot_url:
            try:
                cap = cv2.VideoCapture(new_host.snapshot_url)
                ret, frame = cap.read()
                cap.release()

                if ret:
                    safe_hostname = "".join(c for c in hostname if c.isalnum() or c in ("-", "_")).rstrip()
                    file_name = f"{ip_address}_{safe_hostname}.jpg"

                    image_dir = os.path.join(app.root_path, 'static', 'images', 'hosts')
                    os.makedirs(image_dir, exist_ok=True)
                    absolute_file_path = os.path.join(image_dir, file_name)

                    cv2.imwrite(absolute_file_path, frame)

                    relative_path = os.path.join("images", "hosts", file_name).replace("\\", "/")
                    img_record = Images(file_path=relative_path, host_id=new_host.id)
                    db.session.add(img_record)
                    db.session.commit()

                    log.info(f"Snapshot capturado para {ip_address}: {relative_path}")
                else:
                    log.warning(f"No se pudo capturar frame de {ip_address}")
            except Exception as e:
                log.error(f"Error al capturar snapshot de {ip_address}: {e}")
        else:
            log.warning(f"Host {ip_address} no tiene snapshot_url definido")

        return {"ip_address": new_host.ip_address, "hostname": new_host.hostname}


def cleanup_orphan_images():
    """Elimina imágenes físicas que ya no tengan registro en la BD"""
    try:
        image_dir = os.path.join(current_app.root_path, 'static', 'images', 'hosts')
        if not os.path.exists(image_dir):
            return

        files_in_disk = set(os.listdir(image_dir))
        files_in_db = set(os.path.basename(img.file_path) for img in Images.query.all())
        orphan_files = files_in_disk - files_in_db

        for orphan in orphan_files:
            try:
                abs_path = os.path.join(image_dir, orphan)
                os.remove(abs_path)
                log.info(f"Imagen huérfana eliminada: {abs_path}")
            except Exception as e:
                log.warning(f"No se pudo eliminar imagen huérfana {orphan}: {e}")

    except Exception as e:
        log.error(f"Error en cleanup_orphan_images: {e}")
