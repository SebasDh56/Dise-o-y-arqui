import tkinter as tk
from tkinter import scrolledtext
import threading
import queue
import json
from connection import Connection

class RabbitMQGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de Colas - Tienda en Línea")
        self.message_queue = queue.Queue()
        self.setup_ui()
        self.start_consumer_thread()

    def setup_ui(self):
        # Etiquetas y áreas de texto
        tk.Label(self.root, text="Mensajes Enviados:").pack()
        self.sent_text = scrolledtext.ScrolledText(self.root, height=10, width=50)
        self.sent_text.pack()

        tk.Label(self.root, text="Mensajes Recibidos:").pack()
        self.received_text = scrolledtext.ScrolledText(self.root, height=10, width=50)
        self.received_text.pack()

        # Botón para enviar mensaje
        tk.Button(self.root, text="Enviar Pedido", command=self.send_sample_order).pack()

    def send_sample_order(self):
        conn = Connection()
        producer = OrderProducer(conn)
        producer.send_order("ORD4", "Product_4", 7)
        self.update_sent_text({"order_id": "ORD4", "product": "Product_4", "quantity": 7})

    def update_sent_text(self, message):
        self.sent_text.insert(tk.END, f"Enviado: {json.dumps(message)}\n")
        self.sent_text.see(tk.END)

    def update_received_text(self, message):
        self.received_text.insert(tk.END, f"Recibido: {json.dumps(message)}\n")
        self.received_text.see(tk.END)

    def consume_messages(self):
        conn = Connection()
        conn.connect()
        conn.declare_queue("notification_queue", durable=True)
        conn.bind_queue("notification_queue", "amq.direct", "send.notification")

        def callback(ch, method, properties, body):
            message = json.loads(body)
            self.message_queue.put(message)

        conn.start_consuming("notification_queue", callback)

    def start_consumer_thread(self):
        consumer_thread = threading.Thread(target=self.consume_messages, daemon=True)
        consumer_thread.start()
        self.update_gui()

    def update_gui(self):
        try:
            while True:
                message = self.message_queue.get_nowait()
                self.update_received_text(message)
        except queue.Empty:
            self.root.after(100, self.update_gui)

if __name__ == "__main__":
    from producer import OrderProducer
    root = tk.Tk()
    app = RabbitMQGUI(root)
    root.mainloop()