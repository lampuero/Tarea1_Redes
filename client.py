import socket
import json
import select
import signal


"""
Excepcion que se levanta cuando el usuario se demora mucho en escribir el comando o los nombres de servidor a enviar el comando.
"""
class TimeoutExpired(Exception):
    pass


def alarm_handler(signum, frame):
    raise TimeoutExpired


"""
Funcion para recibir un input pero con tiempo limite.
"""
def input_with_timeout(prompt, timeout):
    # set signal handler
    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(timeout)  # produce SIGALRM in `timeout` seconds

    try:
        cmd = input(prompt)
        return cmd
    finally:
        signal.alarm(0)  # cancel alarm


"""
Clase que contiene un socket conectado a un servidor telnet y el nombre de ese servidor.
"""
class ClientConnection:
    def __init__(self, name, address, port):
        self.socket = socket.socket()
        self.server_name = name
        self.socket.connect((address, port))

    """
    Lee respuesta de servidor telnet.
    """
    def read_response(self):
        message = ""
        raw_char_message = self.socket.recv(1024)
        while '\n' not in message:
            if not raw_char_message:
                message = "Servidor cerro la conexion a peticion del cliente.\n"
            else:
                char_message = raw_char_message.decode()
                message += char_message
        return "Server {} respondio:\n{}".format(
            self.server_name,
            message)

    """
    Escribe comando a servidor telnet.
    """
    def write_command(self, command):
        command_byte = command.encode()
        self.socket.send(command_byte)

    """
    Necesario para select.
    """
    def fileno(self):
        return self.socket.fileno()


def mainclient():
    servers_dict = dict()
    servers_data = input("Ingrese la informacion de los servers (o la direccion del json) en una linea:\n")
    servers_data_split = servers_data.split(" ")
    # Proceso datos de los servidores
    if len(servers_data_split) == 1:
        # Caso json
        json_data = json.loads(open(servers_data_split[0]).read())
        for server in json_data:
            name = server['nombre']
            address = server['direccion']
            port = int(server['puerto'])
            server_connection = ClientConnection(name, address, port)
            servers_dict[name] = server_connection
    else:
        # Caso manual
        i = 0
        while i < len(servers_data_split):
            name = servers_data_split[i]
            address = servers_data_split[i+1]
            port = int(servers_data_split[i+2])
            server_connection = ClientConnection(name, address, port)
            servers_dict[name] = server_connection
            i += 3
    # Ingreso de los comandos
    while True:
        servers_with_response, _, _ = select.select(servers_dict.values(), [], [], 3)
        for connection in servers_with_response:
            print(connection.read_response())
        try:
            command = input_with_timeout("Ingrese el comando:", 10)
            servers_to_send_command = input_with_timeout("Ingrese el nombre de los servers:", 10)
            servers_names = servers_to_send_command.split(" ")
            if servers_names[0] == "all" and len(servers_names):
                for name in servers_dict.keys():
                    connection = servers_dict[name]
                    connection.write_command(command)
            else:
                for name in servers_names:
                    if name in servers_dict.keys():
                        connection = servers_dict[name]
                        connection.write_command(command)
                    else:
                        print("El nombre de server {} no es valido".format(name))
        except TimeoutExpired:
            print("\n")
            continue
        except KeyboardInterrupt:
            break


mainclient()
