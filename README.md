Monitorear direcciones IP mediante solicitudes ICMP (ping) por medio de consultas.
Se proporciona una aplicación web mediante Flask para ver los estados de las direcciones IP y el historial de encuestas.
La encuesta se ejecuta como un servicio como parte de la aplicación web.
Se utiliza una base de datos SQLite para almacenar hosts, resultados de encuestas, cuentas de usuario, etc.

**Configuración**
Los siguientes ajustes deberán realizarse para la configuración:

```Cambiar Politicas (solo Windows)```

 En windows cambiar las politicas, ejecute Powershell como administrdor y ejecute el siguiente comando:

     Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser


```Instalar Python```

1.- Python 3.11+ debe estar instalado.

2.- Dirigase al directorio donde desee instalar el repositorio.


```Clonar el repositorio```
    
3.- Clonar el repositorio
    apt install git
    
    git clone https://github.com/MonitoreoLAN/MONITOREO-TLPG.git 



4.- Ingrese al directorio principal del Proyecto

     cd MONITOREO-TLPG
     

```Entorno Virtual```

5.- Crear el entorno virtual con el siguiente comando:

Sistema Operativo Windows


       Python -m venv .venv

       
 Sistema Operativo  Linux
   
       virtualenv .venv

       
6.- Activar el entorno virtual con el siguiente comando:

 Sistema Operativo Windows
 
         .\.venv\Scripts\activate
         
 Sistema Operativo  Linux     
 
          source .venv/bin/activate
   ```Actualizar PIP```

   
7.-  ejecute el siguiente comando:SOLO PARA WINDOWS

    python.exe -m pip install --upgrade pip
       
8.- Desde el directorio principal de este repositorio, ejecute el siguiente comando:

     pip install -r requirements.txt


   ```Iniciar el Servidor```

9.- poner en marcha el servidor, ejecute el siguiente comando:

    flask run

  Flask corre pór defecto en el puerto 5000 si desea cambiar el puerto ejecute el siguiente comando:

    flask run --port 

  Para aceptar peticiones de otros ordenadores de nuestra red lanzaremos el servidor de la siguiente manera:

     flask run --host  --port 

 Nota: para ejecutar una aplicación Flask en modo de depuración:
 
     flask run --debug






