# Simple RPC With Raw Sockets
Repository for the Data network course project:

---

## Introduction

In this project, you will attempt to code a simple implementation of an RPC toolkit (based loosely on some widely used implementations, like Google's gRPC).
A Remote Procedure Call (RPC) is any protocol that allows for a machine to trigger a procedure on a remote machine, as if it was a local call. More specifically, RPCs abstract away transport layers between two machines, and allows two machines to execute code purely in the application layer.
The main purpose of RPC protocols is to allow for simple application development, without needing to worry about the intricacies of how two machines communicate in the transport layer with a protocol like TCP. Instead, software developers can focus on things that are purely related to the application layer.

See the project PDF for more information.`project.pdf`

## Files:
* `init.yaml`: To setup this connection pattern (and some other things) we will use an initializer file that we will call `init.yaml`.
* `rpc-server.py`: This code will implement the RPC server on each node. Note that this exact, same code should be executed on every server node. So make sure that you allow inputs for things like IP addresses and ports.
* `rpc-client.py`: Similar to `rpc-server.py` , this code must be able to reach any of the servers given the server name, and call for an RPC, then return the result to the code that called it.
* `initializer.py`: Reads the `init.yaml` file and distributes the RPCs among the servers.

### Execute: 

1. Run two servers on two different terminals: Implement the RPC server on each node.

```
python rpc-server.py "127.0.0.1" 8282
python rpc-server.py "127.0.0.1" 8181
```

2. Run initializer: Distribute the RPCs among the servers.

```
python initializer.py
```

3. Run client: Reach any of the servers given the server name, and call for an RPC, then return the result to the code that called it.

```
python rpc-client.py
```