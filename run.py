import webbrowser
from threading import Timer
from app import create_app
import os

app = create_app()

# Replace 127.0.0.1 with your machine's local IP address (or use 0.0.0.0 to bind to all interfaces)
host_ip = '0.0.0.0'
port = 5000

def open_browser():
   webbrowser.open_new(f'http://10.103.45.57:{port}/')  

if __name__ == '__main__':
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        Timer(1, open_browser).start()

    app.run(debug=True, host=host_ip, port=port)
