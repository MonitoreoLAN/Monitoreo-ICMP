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
