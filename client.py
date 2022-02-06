from email import message
import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client_socket.connect(("127.0.0.1", 8000))

len_message_byte = client_socket.recv(8)
len_message = int.from_bytes(len_message_byte, "big")

message_byte = b''
chunks = list()
while True:
    chunks.append(client_socket.recv(8))
    if len(chunks) * 8 >= len_message:
        break

message_byte = b''.join(chunks)
message = message_byte[0:len_message].decode()
print(message)