from connection import Connection
import json
import time

class OrderProducer:
    def __init__(self, connection):
        self.connection = connection

    def send_order(self, order_id, product, quantity):
        order = {"order_id": order_id, "product": product, "quantity": quantity}
        self.connection.connect()
        self.connection.declare_queue("order_queue", durable=True)
        self.connection.bind_queue("order_queue", "amq.direct", "new.order")
        self.connection.publish_message("order_queue", order, "amq.direct", "new.order")
        self.connection.close()

def main():
    # Productor para virtual host "/"
    conn_default = Connection(virtual_host='/')
    producer_default = OrderProducer(conn_default)
    # Productor para virtual host "produccion"
    conn_produccion = Connection(virtual_host='produccion')
    producer_produccion = OrderProducer(conn_produccion)

    for i in range(3):
        producer_default.send_order(f"ORD{i+1}", f"Product_{i+1}", 10 - i)
        producer_produccion.send_order(f"ORD_PROD{i+1}", f"Product_PROD_{i+1}", 10 - i)
        time.sleep(2)

if __name__ == "__main__":
    main()