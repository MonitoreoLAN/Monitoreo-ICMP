# 🌐 Monitoreo ICMP / LAN

**Configuración**

Monitoreo de direcciones IP mediante solicitudes ICMP (ping), con visualización web, historial y almacenamiento en SQLite.  
Aplicación construida en **Flask**, con scheduler integrado para ejecutar escaneos automáticos.

---

## 🏷️ Badges
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Flask](https://img.shields.io/badge/Flask-App-black)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-success)

---

## 📌 Características

- ✔️ Monitoreo ICMP continuo  
- ✔️ Dashboard web  
- ✔️ Registro histórico  
- ✔️ Base SQLite integrada  
- ✔️ Compatible Windows / Linux  

---

## ⚙️ Requisitos Previos

- Python **3.11+**
- Git
- Permisos administrativos para ICMP

---

## 🔐 1. Cambiar Política de Ejecución (Windows)

Abrir PowerShell como administrador y ejecutar:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

📥 2. Clonar el Repositorio
Opción HTTPS:

git clone https://github.com/MonitoreoLAN/Monitoreo-ICMP.git

Opción SSH:

git clone git@github.com:MonitoreoLAN/Monitoreo_IPS.git

Entrar al directorio:

cd Monitoreo_IPS

🧪 3. Crear el Entorno Virtual
Windows:

python -m venv .venv

Linux:

virtualenv .venv

Activar entorno

Windows:

.\.venv\Scripts\activate

Linux:

source .venv/bin/activate

📦 4. Instalar Dependencias
(Opcional en Windows) Actualizar pip:

            python.exe -m pip install --upgrade pip

Instalar dependencias:

pip install -r requirements.txt

🚀 5. Iniciar el Servidor Flask
Ejecutar:

flask run

Se abrirá en:

http://127.0.0.1:5000

Cambiar el puerto:

flask run --port 5050

Permitir conexiones desde la red:

flask run --host 0.0.0.0 --port 5000

Modo depuración:

flask run --debug

🗂️ Estructura del Proyecto

Monitoreo_IPS/
│── ipmon/
│   ├── static/
│   ├── templates/
│   ├── models/
│   ├── scheduler/
│   ├── smtp.py
│   ├── alerts.py
│   └── ...
│
├── requirements.txt
├── README.md
└── .gitignore

🛠️ Tecnologías

    Python

    Flask

    SQLite

    SQLAlchemy

    APScheduler

    ICMPLib / Ping





