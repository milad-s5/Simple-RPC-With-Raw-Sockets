from threading import Thread
import socket
import json
import importlib.util
import sys
import hashlib
import os
import logging

# class Server
class Server:
    def __init__(self, ip: str, port: int) -> None:
        self.ip = ip
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.ip, self.port))
        self.server_socket.listen(10)
        # Gets or creates a logger (BONUS) Logging
        self.logger = logging.getLogger(__name__)  
        # set log level
        self.logger.setLevel(logging.WARNING)
        # define file handler and set formatter
        dirName = './server/'+str(self.ip)+'-'+str(self.port)
        if not os.path.exists(dirName):
            os.makedirs(dirName)
        file_handler = logging.FileHandler(dirName+'/'+'logfile.log')
        formatter    = logging.Formatter('%(asctime)s : %(levelname)s : %(message)s')
        file_handler.setFormatter(formatter)
        # add file handler to logger
        self.logger.addHandler(file_handler)
        # Setting the threshold of logger to DEBUG
        self.logger.setLevel(logging.DEBUG)
    # handle client
    def handle_client(self, switched_socket, switched_addr):
        # receive message
        msg = switched_socket.recv(1024)
        ## should use try for adversial to client 
        msg = json.loads(msg.decode()) # convert str to dict
        # check messages whether is from client or initializer
        if(msg['header'] == 'RPC_INIT'):
            global msg_serv, msg_rpc, msg_cli, service
            [msg_serv, msg_rpc, msg_cli] = msg['value']
            service = [x for y in msg_serv for x in y.keys()] 
            for serv in service:
                for rpc in msg_rpc[serv]:
                    # Create target directory & all intermediate directories if don't exists to save rpcs
                    dirName = './server/'+str(self.ip)+'-'+str(self.port)+'/'+str(serv)+'/' + str(list(rpc.keys())[0])+'/'+ str(list(rpc.values())[0]['args'])+str(list(rpc.values())[0]['returns'])
                    if not os.path.exists(dirName):
                        os.makedirs(dirName)                   
                    rpc_path = dirName+'/'+str(list(rpc.keys())[0])+'.py'
                    # if rpc does't exist in server directory send a ex message to initializer with RPC_NOT_EXIST type
                    if not os.path.exists(rpc_path):
                        print('{} from {} does not exist. Send it to me!'.format(str(list(rpc.keys())[0]), str(serv)))
                        msg1 = self.create_json_msg_ex('RPC_NOT_EXIST',
                                                      {'service': serv,
                                                       'rpc': list(rpc.keys())[0],
                                                       'args': list(rpc.values())[0]['args'],
                                                       'returns': list(rpc.values())[0]['returns']})
                        switched_socket.send(msg1.encode())
                        # get rpc code from initializer
                        len_msg_byte = switched_socket.recv(1024)
                        len_msg = int.from_bytes(len_msg_byte, "big")
                        msg_byte = b''
                        chunks = list()
                        while True:
                            chunks.append(switched_socket.recv(1024))
                            if len(chunks) * 1024 >= len_msg:
                                break
                        msg_byte = b''.join(chunks)
                        msg1 = msg_byte[0:len_msg].decode()
                        msg1 = json.loads(msg1)
                        # save rpc code
                        rpc_code = msg1['value']
                        rpc_file = open(rpc_path, "w")
                        rpc_file.write(rpc_code)
                        rpc_file.close()
                    # if rpc exist in server directory send a ex message to initializer with SHA type with sha256 value of rpc code
                    else:
                        print('{} from {} does exist. I send you SHA256!'.format(str(list(rpc.keys())[0]), str(serv)))
                        rpc_code_file = open(rpc_path, "r")
                        rpc_code = rpc_code_file.read()
                        hash_of_rpc_code = hashlib.sha256(rpc_code.encode()).hexdigest()
                        msg1 = self.create_json_msg_ex('SHA',
                                                      {'service': serv,
                                                       'rpc': list(rpc.keys())[0],
                                                       'args': list(rpc.values())[0]['args'],
                                                       'returns': list(rpc.values())[0]['returns'],
                                                       'SHA256': hash_of_rpc_code
                                                       })
                        switched_socket.send(msg1.encode())
                        # get message that include new rpc or 'OK!' 
                        len_msg_byte = switched_socket.recv(1024)
                        len_msg = int.from_bytes(len_msg_byte, "big")
                        msg_byte = b''
                        chunks = list()
                        while True:
                            chunks.append(switched_socket.recv(1024))
                            if len(chunks) * 1024 >= len_msg:
                                break
                        msg_byte = b''.join(chunks)
                        msg1 = msg_byte[0:len_msg].decode()
                        msg1 = json.loads(msg1)
                        # if hash of two rpcs is not same recieve rpc code and replace with old code
                        if(msg1['value'] != 'This rpc is up to date!'):
                            print('I put new {} from {} in my dirs!'.format(str(list(rpc.keys())[0]), str(serv)))
                            rpc_code = msg1['value']
                            rpc_file = open(rpc_path, "w")
                            rpc_file.write(rpc_code)
                            rpc_file.close()
                        else:
                            print('This rpc is up to date!')
                        
        ## handle RPC_REQ messages that are from clients
        elif(msg['header'] == 'RPC_REQ'):          
            if(msg['value']['service'] in service):
                # rpcs of this service
                rpc = []
                for rpc1 in msg_rpc[msg['value']['service']]:
                    rpc.append(list(rpc1.keys())[0])
                # tenants of this service
                tenants = []
                for serv in msg_serv:
                    if(list(serv.keys())[0] == msg['value']['service']):
                        tenants = serv[msg['value']['service']]['tenants']
                # check the client has access to the service or not
                switched_addr_dict = {'ip': switched_addr[0], 'port': switched_addr[1]}
                cli_reg = False
                for cli in msg_cli:
                    if(list(cli.keys())[0] in tenants) and (list(cli.values())[0] == switched_addr_dict):
                        cli_reg = True
                # set flag for args and returns that they are valid or not
                flag_args = False
                valid_args = []
                valid_returns = []
                for rpc1 in msg_rpc[msg['value']['service']]:
                    if(list(rpc1.keys())[0] == msg['value']['rpc']):
                        if(list(rpc1.values())[0]['args'] == msg['value']['arg_types']) and (list(rpc1.values())[0]['returns'] == msg['value']['returns']):
                            flag_args = True
                        else:
                            valid_args.append(list(rpc1.values())[0]['args'])
                            valid_returns.append(list(rpc1.values())[0]['returns'])
            # our exceptions 
            if(msg['value']['service'] not in service):
                msg1 = self.create_json_msg_ex('Service Not Found')
                l = len(msg1)
                switched_socket.send(l.to_bytes(1024, "big"))
                switched_socket.send(msg1.encode())
                # log
                self.logger.info('Exception: Service({}) Not Found. from {}'.format(
                    str(msg['value']['service']), switched_addr))
            elif(msg['value']['rpc'] not in rpc): 
                msg1 = self.create_json_msg_ex('RPC Not Found')
                l = len(msg1)
                switched_socket.send(l.to_bytes(1024, "big"))
                switched_socket.send(msg1.encode())
                # log
                self.logger.info('Exception: RPC({} from {}) Not Found. from {}'.format(
                    str(msg['value']['rpc']), str(msg['value']['service']), switched_addr))
            elif(cli_reg == False):
                msg1 = self.create_json_msg_ex('Client Not Registered', 'The client is not allowed to access '+str(msg['value']['service']))
                l = len(msg1)
                switched_socket.send(l.to_bytes(1024, "big"))
                switched_socket.send(msg1.encode())
                # log
                self.logger.warning('Unauthorized access by {} to access {}.'.format(switched_addr, str(msg['value']['service'])))
            elif(flag_args == False):
                msg1 = self.create_json_msg_ex('Invalid Arguments', '{} argument types and {} returns may be valid for {}.'
                                           .format(valid_args, valid_returns , msg['value']['rpc']))
                l = len(msg1)
                switched_socket.send(l.to_bytes(1024, "big"))
                switched_socket.send(msg1.encode())
                # log
                self.logger.info('Exception: Invalid Arguments({} from {}) for {}.'.format(
                    str(msg['value']['rpc']), str(msg['value']['service']), switched_addr))
            # we can run rpc because we don't see above exception
            else:            
                args_str = msg['value']['args']
                arg_types = msg['value']['arg_types']
                arguments = []
                for i in range(len(msg['value']['arg_types'])):
                    if(arg_types[i] == 'int'):
                        arguments.append(int(args_str[i]))
                    elif(arg_types[i] == 'float'):
                        arguments.append(float(args_str[i]))
                    elif(arg_types[i] == 'List[int]'):
                        list1 = [int(j) for j in args_str[i]]
                        arguments.append(list1)                    
                    elif(arg_types[i] == 'List[float]'):
                        list1 = [float(j) for j in args_str[i]]
                        arguments.append(list1)
                    else:
                        arguments.append(args_str[i])                    
                # run rpc 
                dirName = './server/'+str(self.ip)+'-'+str(self.port)+'/'+str(msg['value']['service'])+'/' + str(
                    msg['value']['rpc'])+'/' + str(msg['value']['arg_types'])+str(msg['value']['returns'])
                rpc_path = dirName+'/'+str(msg['value']['rpc'])+'.py'
                spec = importlib.util.spec_from_file_location ("test", rpc_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules["test"] = module
                spec.loader.exec_module(module)
                try:
                    # calculate and send rpc outputs
                    outputs = getattr(module, msg['value']['rpc'])(*arguments)
                    msg1 = self.create_json_msg_res(outputs)
                    l = len(msg1)
                    switched_socket.send(l.to_bytes(1024, "big"))
                    switched_socket.send(msg1.encode())
                    # log
                    self.logger.info('Successful RPC({} from {}) for {}.'.format(str(msg['value']['rpc']), str(msg['value']['service']), switched_addr))
                except Exception as e:
                    # If execution fails with an exception
                    msg = self.create_json_msg_ex('Execution Exception', str(e))
                    l = len(msg)
                    switched_socket.send(l.to_bytes(1024, "big"))
                    switched_socket.send(msg.encode())
            print(msg1)
        switched_socket.close()
    # server accept
    def serve_forever(self):
        while True:
            switched_socket, switched_addr = self.server_socket.accept()
            print('Accepted connection from', switched_addr)
            # log
            self.logger.info('An attempt to connect to the server')
            self.logger.info('Accepted connection from ' + str(switched_addr))
            # thread
            t = Thread(target=self.handle_client, args=(switched_socket, switched_addr))
            t.setDaemon = True
            t.start()
    # create exeption message
    def create_json_msg_ex(self, type, ex_msg=[]):
        rpc_json = {'header': 'RPC_EX',
                    'value': {'type': type, 'msg': ex_msg}}
        msg = json.dumps(rpc_json)
        return msg
    # create response message
    def create_json_msg_res(self, ret_val):
        rpc_json = {'header': 'RPC_RES',
                    'value': {'return values': ret_val}}
        msg = json.dumps(rpc_json)
        return msg

# get server ip and port from user
if len(sys.argv) > 1:
    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])
else:
    server_ip = "127.0.0.1"
    server_port = 8181

server = Server(server_ip, server_port)
server.serve_forever()
