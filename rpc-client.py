import socket
import json
import sys

# get server ip and port from user
if len(sys.argv) > 1:
    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])
else:
    server_ip = "127.0.0.1"
    server_port = 8181
# set client ip and port
cli_ip = "127.0.0.1"
cli_port = 6000
# initilize service, rpc, ... that our client want to access
# use case 1 (show output)
service = 'service1'
rpc = 'rpc1' # concatinate
args = ['32', 'hello']
arg_types = ['int', 'str']
returns = ['str']
# use case 2 (BONUS) Overloaded RPCs
'''
service = 'service1'
rpc = 'rpc1' # sum
args = ['32', '33']
arg_types = ['int', 'int']
returns = ['int']
'''
# use case 3 (service not found)
'''
service = 'service2'
rpc = 'rpc3' # sum all floats
args = ['2.5', ['2.5','2.5']]
arg_types = ['float', 'List[float]']
returns = ['str']
'''
# use case 4 (rpc not found)
'''
service = 'service1'
rpc = 'rpc4'
args = ['2.5', ['2.5', '2.5']]
arg_types = ['float', 'List[float]']
returns = ['str']
'''
# use case 5 (Client Not Registered): sould del c1 from tenants of service1 and run initializer.py again
'''
service = 'service1'
rpc = 'rpc1'  # sum
args = ['32', '33']
arg_types = ['int', 'int']
returns = ['int']
'''
# use case 6 (invalid arguments)
'''
service = 'service1'
rpc = 'rpc1'  # sum
args = ['32', '33']
arg_types = ['intt', 'int']
returns = ['int']
'''
# for Execution Exception: change in1 to in11 in rpc1. then run initializer and then run this code.
'''
service = 'service1'
rpc = 'rpc1'  # sum
args = ['32', '33']
arg_types = ['int', 'int']
returns = ['int']
'''
# define client socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
client_socket.bind((cli_ip, cli_port))
client_socket.connect((server_ip, server_port))
# create rpc req massage and send to server
rpc_json = {'header': 'RPC_REQ', 
            'value' : {'service': service, 'rpc': rpc, 'args': args, 'arg_types': arg_types, 'returns': returns}}
msg = json.dumps(rpc_json)
client_socket.send(msg.encode())
# recieve response messages from server and check whether is RPC_RES or RPC_EX
len_msg_byte = client_socket.recv(1024)
len_msg = int.from_bytes(len_msg_byte, "big")
msg_byte = b''
chunks = list()
while True:
    chunks.append(client_socket.recv(1024))
    if len(chunks) * 1024 >= len_msg:
        break
msg_byte = b''.join(chunks)
msg = msg_byte[0:len_msg]
msg = json.loads(msg.decode())
# print ouput message
if(msg['header'] == 'RPC_EX'):
    print('exception-type:', msg['value']['type'])
    if(msg['value']['msg']):
        print('exception-message:', msg['value']['msg'])
elif(msg['header'] == 'RPC_RES'):
    print('output:', msg['value']['return values'])
client_socket.close()