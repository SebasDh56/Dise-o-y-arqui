from flask import Flask, render_template, request
from flask_socketio import SocketIO
from connection import Connection
import json
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app, async_mode='threading')

# Inventario de ingredientes
ingredients = {
    "Pizza": 10,
    "Hamburguesa": 15,
    "Ensalada": 20
}

# Historial de pedidos
orders_history = []

# Mensajes de seguimiento
tracking_messages = []

def consume_tracking_queue():
    conn = Connection(virtual_host='produccion')
    try:
        conn.connect()
        conn.declare_queue("tracking_queue", durable=True)
        conn.bind_queue("tracking_queue", "amq.direct", "tracking.update")
        print("Consumidor de tracking_queue iniciado")

        def callback(ch, method, properties, body):
            try:
                message = json.loads(body)
                print(f"Mensaje recibido de tracking_queue: {message}")
                tracking_messages.append(message)

                # Actualizar inventario
                if "remaining_stock" in message:
                    ingredients[message["dish"]] = message["remaining_stock"]
                    print(f"Inventario actualizado: {message['dish']} = {message['remaining_stock']}")

                # Actualizar historial (mantener el dish original)
                updated = False
                for order in orders_history:
                    if order["order_id"] == message["order_id"]:
                        order["status"] = message["status"]
                        if "order_number" in message:
                            order["order_number"] = message["order_number"]
                        # No cambiamos el dish, solo actualizamos status y order_number
                        updated = True
                        print(f"Historial actualizado: {order}")
                        break
                if not updated:
                    # Si no existe, agregar el pedido completo
                    new_order = {
                        "order_id": message["order_id"],
                        "dish": message["dish"],
                        "quantity": message["quantity"],
                        "customer": message["customer"],
                        "status": message["status"],
                        "order_number": message.get("order_number", ""),
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    orders_history.append(new_order)
                    print(f"Nuevo pedido agregado al historial: {new_order}")

                socketio.emit('update_tracking', message)
                socketio.emit('update_orders', orders_history)
                socketio.emit('update_inventory', ingredients)
                print("Eventos WebSocket emitidos")
            except Exception as e:
                print(f"Error al procesar mensaje de tracking_queue: {str(e)}")

        conn.start_consuming("tracking_queue", callback)
    except Exception as e:
        print(f"Error al iniciar consumidor de tracking_queue: {str(e)}")

# Iniciar consumidor en un hilo
threading.Thread(target=consume_tracking_queue, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html', ingredients=ingredients, orders_history=orders_history, tracking_messages=tracking_messages)

@app.route('/create_order', methods=['POST'])
def create_order():
    order_id = request.form.get('order_id')
    dish = request.form.get('dish')
    quantity = int(request.form.get('quantity'))
    customer = request.form.get('customer')

    # Validar ingredientes
    if dish not in ingredients:
        socketio.emit('order_error', {"message": f"Plato {dish} no disponible"})
        return '', 400
    if ingredients[dish] < quantity:
        socketio.emit('order_error', {"message": f"No hay suficientes {dish}. Stock: {ingredients[dish]}"})
        return '', 400

    # Enviar pedido
    conn = Connection(virtual_host='produccion')
    order = {"order_id": order_id, "dish": dish, "quantity": quantity, "customer": customer}
    try:
        conn.connect()
        conn.declare_queue("order_queue", durable=True)
        conn.bind_queue("order_queue", "amq.direct", "new.order")
        conn.publish_message("order_queue", order, "amq.direct", "new.order")
        orders_history.append({
            "order_id": order_id,
            "dish": dish,
            "quantity": quantity,
            "customer": customer,
            "status": "Pendiente",
            "order_number": "",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        socketio.emit('order_created', {"message": f"Pedido {order_id} recibido"})
        socketio.emit('update_orders', orders_history)
        print(f"Pedido {order_id} enviado a order_queue")
    except Exception as e:
        socketio.emit('order_error', {"message": f"Error: {str(e)}"})
        return '', 500
    finally:
        conn.close()

    return '', 204

@app.route('/clear_history', methods=['POST'])
def clear_history():
    global orders_history, tracking_messages
    orders_history = []
    tracking_messages = []
    socketio.emit('update_orders', orders_history)
    socketio.emit('update_tracking', {"message": "Historial limpiado"})
    return '', 204

@socketio.on('connect')
def handle_connect():
    socketio.emit('update_inventory', ingredients)
    socketio.emit('update_orders', orders_history)
    print("Cliente conectado, enviando inventario y historial inicial")

if __name__ == "__main__":
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)