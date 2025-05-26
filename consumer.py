from connection import Connection
import json

class OrderConsumer:
    def __init__(self, connection):
        self.connection = connection

    def process_order(self, ch, method, properties, body):
        order = json.loads(body)
        print(f"Procesando pedido en {self.connection.virtual_host}: {order}")
        
        # Actualizar inventario
        inventory_update = {"order_id": order["order_id"], "product": order["product"], "quantity": -order["quantity"]}
        self.connection.connect()
        self.connection.declare_queue("dev.inventario", durable=True)
        self.connection.bind_queue("dev.inventario", "amq.direct", "update.inventory")
        self.connection.publish_message("dev.inventario", inventory_update, "amq.direct", "update.inventory")

        # Actualizar logística
        logistics_update = {"order_id": order["order_id"], "message": f"Pedido {order['order_id']} enviado a logística"}
        self.connection.declare_queue("dev.logistica", durable=True)
        self.connection.bind_queue("dev.logistica", "amq.direct", "update.logistics")
        self.connection.publish_message("dev.logistica", logistics_update, "amq.direct", "update.logistics")

        # Enviar notificación
        notification = {"order_id": order["order_id"], "message": f"Pedido {order['order_id']} procesado"}
        self.connection.declare_queue("dev.notificaciones", durable=True)
        self.connection.bind_queue("dev.notificaciones", "amq.direct", "send.notification")
        self.connection.publish_message("dev.notificaciones", notification, "amq.direct", "send.notification")
        self.connection.close()

def main():
    # Consumidor para virtual host "/"
    conn_default = Connection(virtual_host='/')
    consumer_default = OrderConsumer(conn_default)
    conn_default.connect()
    conn_default.declare_queue("order_queue", durable=True)
    conn_default.bind_queue("order_queue", "amq.direct", "new.order")
    consumer_thread_default = threading.Thread(
        target=lambda: conn_default.start_consuming("order_queue", consumer_default.process_order)
    )
    consumer_thread_default.start()

    # Consumidor para virtual host "produccion"
    conn_produccion = Connection(virtual_host='produccion')
    consumer_produccion = OrderConsumer(conn_produccion)
    conn_produccion.connect()
    conn_produccion.declare_queue("order_queue", durable=True)
    conn_produccion.bind_queue("order_queue", "amq.direct", "new.order")
    conn_produccion.start_consuming("order_queue", consumer_produccion.process_order)

if __name__ == "__main__":
    import threading
    main()