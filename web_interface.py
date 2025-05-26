from flask import Flask, render_template, jsonify
from connection import Connection
import json
import threading
import queue

app = Flask(__name__)

# Colas para almacenar mensajes recibidos
notifications_queue = queue.Queue()
logistics_queue = queue.Queue()

def consume_queue(queue_name, message_queue, virtual_host='produccion'):
    conn = Connection(virtual_host=virtual_host)
    conn.connect()
    conn.declare_queue(queue_name, durable=True)
    conn.bind_queue(queue_name, "amq.direct", f"{'send.notification' if queue_name == 'dev.notificaciones' else 'update.logistics'}")

    def callback(ch, method, properties, body):
        message = json.loads(body)
        message_queue.put(message)

    conn.start_consuming(queue_name, callback)

# Iniciar consumidores en hilos separados
threading.Thread(target=consume_queue, args=("dev.notificaciones", notifications_queue), daemon=True).start()
threading.Thread(target=consume_queue, args=("dev.logistica", logistics_queue), daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/notifications')
def get_notifications():
    messages = []
    try:
        while True:
            message = notifications_queue.get_nowait()
            messages.append(message)
    except queue.Empty:
        pass
    return jsonify(messages)

@app.route('/logistics')
def get_logistics():
    messages = []
    try:
        while True:
            message = logistics_queue.get_nowait()
            messages.append(message)
    except queue.Empty:
        pass
    return jsonify(messages)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)