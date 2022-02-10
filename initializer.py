from mimetypes import init
import socket
from yaml import load, dump, CLoader as Loader, CDumper as Dumper
import json
import hashlib
# (BONUS) Support For Runtime Update
servers = ['s1', 's2']
# extract datas from yaml file
for server_name in servers:
    data = load(open("./init.yaml"), Loader=Loader)
    for serv in data['network']['servers']:
        if(list(serv.keys())[0] == server_name):
            server_ip = serv[server_name]['ip']
            server_port = serv[server_name]['port']
    # find services of this server
    service = []
    for serv in data['service']:
        for s in list(serv.values())[0]['providers']:
            if(s == server_name):
                service.append(list(serv.keys())[0])
    # make a service without providers to send to servers
    serv_dict = data['service']
    for s in serv_dict:
        del list(s.values())[0]['providers']
    # msg_serv include services, tenants ans rpcs that this server can access
    msg_serv = []
    for serv in serv_dict:
        if list(serv.keys())[0] in service:
            msg_serv.append(serv)
    # rpc message 
    msg_rpc = data['rpc'].copy()
    for serv in data['rpc'].keys():
        if serv not in service:
            del msg_rpc[serv]
    # client names, ips and ports
    msg_cli = data['network']['clients']
    # delete rpc source paths from msg_rpc
    for rpc_list in list(msg_rpc.values())[0]:
        del list(rpc_list.values())[0]['src']
    # final message
    msg_val = [msg_serv, msg_rpc, msg_cli]
    # define initializer socket
    initializer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    initializer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    initializer.bind(("127.0.0.1", 9000))  # initializer ip and port
    initializer.connect((server_ip, server_port))
    # create rpc init massage and send to server
    rpc_json = {'header': 'RPC_INIT',
                'value': msg_val
                } 
    msg = json.dumps(rpc_json)
    initializer.send(msg.encode())
    # recieve response messages from server
    for serv in service:
        for rpc in msg_rpc[serv]:
            msg = initializer.recv(1024)
            msg = json.loads(msg.decode())
            rpc_path = './services/' + str(msg['value']['msg']['service']) + '/' + str(msg['value']['msg']['rpc']) + '/' + \
                str(msg['value']['msg']['args']) + str(msg['value']['msg']['returns']) + '/' + str(msg['value']['msg']['rpc']) + '.py'
            rpc_code_file = open(rpc_path, "r")
            rpc_code = rpc_code_file.read()
            # send rpc to server if not exist in server directories
            if(msg['value']['type'] == 'RPC_NOT_EXIST'):
                print('{} from {} does not exist on {}. I send it!'.format(str(msg['value']['msg']['rpc']), str(msg['value']['msg']['service']), server_name))
                msg1 = {'header': 'RPC_CODE',
                    'value': rpc_code
                    }
                msg1 = json.dumps(msg1)
                l = len(msg1)
                initializer.send(l.to_bytes(1024, "big"))
                initializer.send(msg1.encode())
            else: #(BONUS) Make It More Efficient!
                hash_of_rpc_code = hashlib.sha256(rpc_code.encode()).hexdigest()
                sha_server = msg['value']['msg']['SHA256']
                # if hash of two rpcs is not same send rpc code
                if(hash_of_rpc_code == sha_server):
                    print('{} from {} is up to date for {}.'.format(str(msg['value']['msg']['rpc']), str(msg['value']['msg']['service']), server_name))
                    msg1 = {'header': 'RPC_CODE',
                            'value': 'This rpc is up to date!'
                            }
                    msg1 = json.dumps(msg1)
                    l = len(msg1)
                    initializer.send(l.to_bytes(1024, "big"))
                    initializer.send(msg1.encode())
                else:
                    print('{} from {} does is not up to date for {}. I send it!'.format(str(msg['value']['msg']['rpc']), str(msg['value']['msg']['service']), server_name))                    
                    msg1 = {'header': 'RPC_CODE',
                            'value': rpc_code
                            }
                    msg1 = json.dumps(msg1)
                    l = len(msg1)
                    initializer.send(l.to_bytes(1024, "big"))
                    initializer.send(msg1.encode())
initializer.close()
