import os
import cv2
import threading
import schedule
import time
from datetime import datetime
from ipmon import db
from ipmon.database import Hosts, Images, SchedulerConfig
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename

imagenes_blueprint = Blueprint("imagenes", __name__, url_prefix="/imagenes")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Carpeta base de imágenes
IMAGE_DIR = os.path.join("static", "images", "hosts")

# Listar hosts e imágenes
@imagenes_blueprint.route("/")
def listar_hosts():
    hosts = Hosts.query.all()
    tipos = sorted({host.tipo for host in hosts if host.tipo and host.tipo.strip() != ""})
    return render_template("imagenes.html", hosts=hosts, tipos=tipos)

# Subida manual
@imagenes_blueprint.route("/<int:host_id>/subir", methods=["POST"])
def subir_imagen(host_id):
    host = Hosts.query.get_or_404(host_id)

    if "imagen" not in request.files or request.files["imagen"].filename == "":
        flash("No se envió ningún archivo", "error")
        return redirect(url_for("imagenes.listar_hosts"))

    file = request.files["imagen"]
    if file and allowed_file(file.filename):
        safe_hostname = "".join(c for c in (host.hostname or host.ip_address)
                                if c.isalnum() or c in ("-", "_")).rstrip()
        file_name = f"{host.ip_address}_{safe_hostname}.jpg"

        full_dir = os.path.join(current_app.root_path, 'static', 'images', 'hosts')
        os.makedirs(full_dir, exist_ok=True)
        absolute_path = os.path.join(full_dir, file_name)

        existing_img = Images.query.filter_by(host_id=host.id).first()
        if existing_img:
            old_path = os.path.join(current_app.root_path, 'static', existing_img.file_path.replace("/", os.sep))
            if os.path.exists(old_path):
                os.remove(old_path)
            db.session.delete(existing_img)
            db.session.commit()

        file.save(absolute_path)

        relative_path = os.path.join("images", "hosts", file_name).replace("\\", "/")
        img_record = Images(file_path=relative_path, host_id=host.id)
        db.session.add(img_record)
        db.session.commit()

        flash("Imagen subida correctamente", "success")
    else:
        flash("Formato de archivo no permitido", "error")

    return redirect(url_for("imagenes.listar_hosts"))


# Captura automática RTSP
@imagenes_blueprint.route("/<int:host_id>/capturar", methods=["POST"])
def capturar_imagen(host_id):
    host = Hosts.query.get_or_404(host_id)

    if not host.snapshot_url:
        flash(f"❌ El host {host.hostname or host.ip_address} no tiene URL de snapshot definida.", "error")
        return redirect(url_for("imagenes.listar_hosts"))

    try:
        cap = cv2.VideoCapture(host.snapshot_url)

        if not cap.isOpened():
            flash(f"❌ No se pudo abrir la URL RTSP: {host.snapshot_url}", "error")
            return redirect(url_for("imagenes.listar_hosts"))

        ret, frame = cap.read()
        cap.release()

        if not ret or frame is None:
            flash(f"❌ No se pudo capturar un frame desde RTSP: {host.snapshot_url}", "error")
            return redirect(url_for("imagenes.listar_hosts"))

        safe_hostname = "".join(c for c in (host.hostname or host.ip_address)
                                if c.isalnum() or c in ("-", "_")).rstrip()
        file_name = f"{host.ip_address}_{safe_hostname}.jpg"

        full_dir = os.path.join(current_app.root_path, 'static', 'images', 'hosts')
        os.makedirs(full_dir, exist_ok=True)
        absolute_path = os.path.join(full_dir, file_name)

        existing_img = Images.query.filter_by(host_id=host.id).first()
        if existing_img:
            old_path = os.path.join(current_app.root_path, 'static', existing_img.file_path.replace("/", os.sep))
            if os.path.exists(old_path):
                os.remove(old_path)
            db.session.delete(existing_img)
            db.session.commit()

        cv2.imwrite(absolute_path, frame)

        relative_path = os.path.join("images", "hosts", file_name).replace("\\", "/")
        img_record = Images(file_path=relative_path, host_id=host.id)
        db.session.add(img_record)
        db.session.commit()

        flash(f"✅ Imagen capturada correctamente para {host.hostname or host.ip_address}", "success")

    except Exception as e:
        flash(f"❌ Error inesperado al capturar RTSP: {e}", "error")

    return redirect(url_for("imagenes.listar_hosts"))


# Eliminar imagen
@imagenes_blueprint.route("/<int:host_id>/eliminar", methods=["POST"])
def eliminar_imagen(host_id):
    img = Images.query.filter_by(host_id=host_id).first()
    if not img:
        flash("No hay imagen para eliminar", "error")
        return redirect(url_for("imagenes.listar_hosts"))

    absolute_path = os.path.join(current_app.root_path, 'static', img.file_path.replace("/", os.sep))
    if os.path.exists(absolute_path):
        os.remove(absolute_path)

    db.session.delete(img)
    db.session.commit()
    flash("Imagen eliminada", "success")
    return redirect(url_for("imagenes.listar_hosts"))


# Captura automática diaria
def captura_diaria():
    from ipmon import app
    with app.app_context():
        hosts = Hosts.query.all()
        for host in hosts:
            try:
                if not host.snapshot_url:
                    print(f"❌ Host {host.hostname or host.ip_address} no tiene snapshot_url")
                    continue

                cap = cv2.VideoCapture(host.snapshot_url)
                if not cap.isOpened():
                    print(f"❌ No se pudo abrir RTSP de {host.hostname or host.ip_address}")
                    continue

                ret, frame = cap.read()
                cap.release()
                if not ret or frame is None:
                    print(f"❌ No se pudo capturar imagen de {host.hostname or host.ip_address}")
                    continue

                safe_hostname = "".join(c for c in (host.hostname or host.ip_address)
                                        if c.isalnum() or c in ("-", "_")).rstrip()
                file_name = f"{host.ip_address}_{safe_hostname}.jpg"

                full_dir = os.path.join(current_app.root_path, 'static', 'images', 'hosts')
                os.makedirs(full_dir, exist_ok=True)
                absolute_path = os.path.join(full_dir, file_name)

                existing_img = Images.query.filter_by(host_id=host.id).first()
                if existing_img:
                    old_path = os.path.join(current_app.root_path, 'static', existing_img.file_path.replace("/", os.sep))
                    if os.path.exists(old_path):
                        os.remove(old_path)
                    db.session.delete(existing_img)
                    db.session.commit()

                cv2.imwrite(absolute_path, frame)
                relative_path = os.path.join("images", "hosts", file_name).replace("\\", "/")
                img_record = Images(file_path=relative_path, host_id=host.id)
                db.session.add(img_record)
                db.session.commit()

                print(f"✅ Imagen capturada para {host.hostname or host.ip_address} a las {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            except Exception as e:
                print(f"❌ Error host {host.hostname or host.ip_address}: {e}")


# Scheduler con BD
def reload_schedule():
    from ipmon import app
    with app.app_context():
        schedule.clear()
        cfg = SchedulerConfig.query.first()

        if not cfg or not cfg.enabled:
            print("⏸️ Scheduler desactivado en BD.")
            return

        t = cfg.time or "09:00"
        freq = cfg.frequency or "daily"
        weekdays = [(d.strip() or "") for d in (cfg.weekdays or "").split(",") if d.strip()]

        if freq == "daily":
            schedule.every().day.at(t).do(captura_diaria)
            print(f"📅 Scheduler programado diario a las {t}")
        elif freq == "weekly":
            dow_map = {
                "lunes": schedule.every().monday,
                "martes": schedule.every().tuesday,
                "miércoles": schedule.every().wednesday,
                "jueves": schedule.every().thursday,
                "viernes": schedule.every().friday,
                "sábado": schedule.every().saturday,
                "domingo": schedule.every().sunday,
            }

            dias_programados = []
            for d in weekdays:
                func = dow_map.get(d.lower())
                if func:
                    func.at(t).do(captura_diaria)
                    dias_programados.append(d)

            if dias_programados:
                dias_str = ", ".join(dias_programados)
                print(f"📅 Scheduler programado semanal ({dias_str}) a las {t}")
            else:
                # Ningún día seleccionado → se desactiva
                print("⏸️ Scheduler semanal no tiene días seleccionados. Desactivado.")
                return

        else:
            print("⚠️ Frecuencia desconocida:", freq)
            return

        # Mensaje común final
        print("⏳ Scheduler iniciado. Esperando tareas programadas...")


def start_scheduler():
    reload_schedule()
    print("⏳ Scheduler iniciado. Esperando tareas programadas...")
    while True:
        schedule.run_pending()
        time.sleep(1)


def init_scheduler():
    t = threading.Thread(target=start_scheduler, daemon=True)
    t.start()

