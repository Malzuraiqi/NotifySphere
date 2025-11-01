from website import create_app
import signal, sys, webbrowser, os
from threading import Timer

app = create_app()

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

def signal_handler(sig, frame):
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true': 
        Timer(1, open_browser).start()
    
    app.run(debug=True, host='127.0.0.1', port=5000)