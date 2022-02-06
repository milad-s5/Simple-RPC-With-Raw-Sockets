import socket
from threading import Thread

class Server:
    def __init__(self, ip: str, port: int) -> None:
        self.ip = ip
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.ip, self.port))
        self.server_socket.listen(10)

    def handle_client(self, switched_socket, switched_addr):
        message = "123456789123456789123456789123456789123456789123456789"
        l = len(message)

        switched_socket.send(l.to_bytes(8, "big"))
        switched_socket.send(message.encode())
        switched_socket.close()

    def serve_forever(self):
        while True:
            switched_socket, switched_addr =  self.server_socket.accept()
            t = Thread(target=self.handle_client, args=(switched_socket, switched_addr))
            t.setDaemon = True
            t.start()

server = Server("127.0.0.1", 8000)
server.serve_forever()
            