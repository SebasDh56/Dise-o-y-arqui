import pika
import json

class Connection:
    def __init__(self, host='localhost', virtual_host='/'):
        self.host = host
        self.virtual_host = virtual_host
        self.connection = None
        self.channel = None

    def connect(self):
        try:
            credentials = pika.PlainCredentials('guest', 'guest')
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(self.host, virtual_host=self.virtual_host, credentials=credentials)
            )
            self.channel = self.connection.channel()
            print(f"Conexión exitosa a {self.host} en virtual host {self.virtual_host}")
        except Exception as e:
            print(f"Error al conectar: {e}")
            raise

    def declare_queue(self, queue_name, durable=True):
        if self.channel:
            self.channel.queue_declare(queue=queue_name, durable=durable)
            print(f"Cola {queue_name} declarada")

    def bind_queue(self, queue_name, exchange, routing_key):
        if self.channel:
            self.channel.queue_bind(queue=queue_name, exchange=exchange, routing_key=routing_key)
            print(f"Cola {queue_name} vinculada a {exchange} con clave {routing_key}")

    def publish_message(self, queue_name, message, exchange='amq.direct', routing_key=''):
        if self.channel:
            if isinstance(message, dict):
                message = json.dumps(message)
            self.channel.basic_publish(exchange=exchange, routing_key=routing_key or queue_name, body=message)
            print(f"Mensaje enviado a {queue_name}: {message}")

    def start_consuming(self, queue_name, callback):
        if self.channel:
            self.channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
            print(f"Consumiendo mensajes de {queue_name}")
            self.channel.start_consuming()

    def close(self):
        if self.connection:
            self.connection.close()
            print("Conexión cerrada")