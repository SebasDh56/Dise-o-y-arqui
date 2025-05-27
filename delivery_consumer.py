from connection import Connection
import json
import random

class DeliveryConsumer:
    def __init__(self, connection):
        self.connection = connection

    def process_delivery(self, ch, method, properties, body):
        try:
            order = json.loads(body)
            print(f"Procesando entrega: {order}")

            # Simular entrega y asignar número de orden
            order_number = random.randint(1000, 9999)
            delivery_update = {
                "order_id": order["order_id"],
                "dish": order["dish"],
                "quantity": order["quantity"],
                "customer": order["customer"],
                "status": "Listo",
                "order_number": order_number,
                "remaining_stock": order["remaining_stock"]
            }

            # Publicar mensaje a tracking_queue
            self.connection.connect()
            self.connection.declare_queue("tracking_queue", durable=True)
            self.connection.bind_queue("tracking_queue", "amq.direct", "tracking.update")
            self.connection.publish_message("tracking_queue", delivery_update, "amq.direct", "tracking.update")
            print(f"Pedido {order['order_id']} enviado a tracking_queue con estado 'Listo'")
            self.connection.close()

        except Exception as e:
            print(f"Error al procesar la entrega: {str(e)}")

def main():
    try:
        conn = Connection(virtual_host='produccion')
        consumer = DeliveryConsumer(conn)
        conn.connect()
        conn.declare_queue("delivery_queue", durable=True)
        conn.bind_queue("delivery_queue", "amq.direct", "delivery.request")
        conn.start_consuming("delivery_queue", consumer.process_delivery)
    except Exception as e:
        print(f"Error al iniciar delivery_consumer: {str(e)}")

if __name__ == "__main__":
    main()