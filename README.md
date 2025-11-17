# 🌐 Monitoreo ICMP / LAN

Monitoreo de direcciones IP mediante solicitudes ICMP (ping), con visualización web, historial, estados en tiempo real y almacenamiento en SQLite.  
Aplicación construida en **Flask**, con scheduler integrado para ejecutar encuestas automáticas.

---

## 🏷️ Badges
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Flask](https://img.shields.io/badge/Flask-App-black)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-success)

---

## 📌 Características Principales

- ✔️ Monitoreo ICMP (ping) para múltiples direcciones IP  
- ✔️ Dashboard web en Flask  
- ✔️ Scheduler para ejecución continua de encuestas  
- ✔️ Registro histórico de resultados  
- ✔️ Base de datos SQLite integrada  
- ✔️ Gestión de hosts, usuarios y configuraciones  
- ✔️ Compatibilidad Windows / Linux  

---

## ⚙️ Requisitos Previos

- Python **3.11+**
- Git instalado
- Permisos ICMP (especialmente en Linux)
- PowerShell (en Windows)

---

## 🔐 1. Cambiar Política de Ejecución (solo Windows)

Abrir PowerShell como administrador y ejecutar:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

📥 2. Clonar el Repositorio

# Clonar por HTTPS
git clone https://github.com/MonitoreoLAN/Monitoreo-ICMP.git

# O clonar por SSH
git clone git@github.com:MonitoreoLAN/Monitoreo_IPS.git

Entrar al proyecto:

cd Monitoreo_IPS

🧪 3. Crear Entorno Virtual
Windows

python -m venv .venv

Linux

virtualenv .venv

Activar entorno

Windows:

.\.venv\Scripts\activate

Linux:

source .venv/bin/activate

📦 4. Instalar Dependencias
Opcional (Windows): actualizar pip

python.exe -m pip install --upgrade pip

Instalar requerimientos

pip install -r requirements.txt

🚀 5. Iniciar el Servidor Flask

flask run

El sistema iniciará en:

http://127.0.0.1:5000

Cambiar el puerto:

flask run --port 5050

Aceptar conexiones desde la red:

flask run --host 0.0.0.0 --port 5000

Modo depuración:

flask run --debug

🗂️ Estructura del Proyecto

Monitoreo_IPS/
│── ipmon/
│   ├── static/           # CSS, JS, imágenes
│   ├── templates/        # Archivos HTML
│   ├── models/           # Modelos SQLAlchemy
│   ├── scheduler/        # Configuración de tareas
│   ├── smtp.py           # Envíos de email
│   ├── alerts.py         # Alertas
│   └── ...
│
├── requirements.txt
├── README.md
└── .gitignore

🛠️ Tecnologías Utilizadas

    Python

    Flask

    SQLite

    SQLAlchemy

    APScheduler

    Pillow / OpenCV

    ICMPLib / Ping nativo

📝 Notas Importantes

    En Linux, ICMP puede requerir permisos especiales o capacidades (CAP_NET_RAW).

    La carpeta instance/ está ignorada para evitar subir configuraciones sensibles.

    La base de datos SQLite se crea automáticamente.

🤝 Contribuir

Abrir un Issue o enviar un Pull Request.
Toda contribución es bienvenida.
📄 Licencia
