from connection import Connection
import json

# Inventario de ingredientes
ingredients = {
    "Pizza": 10,
    "Hamburguesa": 15,
    "Ensalada": 20
}

class KitchenConsumer:
    def __init__(self, connection):
        self.connection = connection

    def process_order(self, ch, method, properties, body):
        try:
            order = json.loads(body)
            print(f"Procesando pedido en cocina: {order}")

            # Verificar ingredientes
            dish = order["dish"]
            quantity = order["quantity"]
            if dish not in ingredients:
                print(f"Error: Plato {dish} no disponible en el inventario")
                return
            if ingredients[dish] < quantity:
                print(f"Error: No hay suficientes {dish}. Stock actual: {ingredients[dish]}")
                return

            # Preparar pedido
            ingredients[dish] -= quantity
            print(f"Inventario actualizado: {dish} ahora tiene {ingredients[dish]} unidades")
            prep_update = {
                "order_id": order["order_id"],
                "dish": dish,
                "quantity": quantity,
                "customer": order["customer"],
                "status": "En preparación",
                "remaining_stock": ingredients[dish]
            }

            # Publicar mensaje a delivery_queue
            self.connection.connect()
            self.connection.declare_queue("delivery_queue", durable=True)
            self.connection.bind_queue("delivery_queue", "amq.direct", "delivery.request")
            self.connection.publish_message("delivery_queue", prep_update, "amq.direct", "delivery.request")
            self.connection.close()

        except Exception as e:
            print(f"Error al procesar el pedido: {str(e)}")

def main():
    try:
        conn = Connection(virtual_host='produccion')
        consumer = KitchenConsumer(conn)
        conn.connect()
        conn.declare_queue("order_queue", durable=True)
        conn.bind_queue("order_queue", "amq.direct", "new.order")
        conn.start_consuming("order_queue", consumer.process_order)
    except Exception as e:
        print(f"Error al iniciar kitchen_consumer: {str(e)}")

if __name__ == "__main__":
    main()