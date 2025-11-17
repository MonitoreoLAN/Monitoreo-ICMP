'''Runs the web server on localhost, port 80'''
from ipmon import app

app.config["PREFERRED_URL_SCHEME"] = "http"  # o "https" si usas SSL

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, use_reloader=True)