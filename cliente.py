import socket
import json
import random

HOST = 'localhost'
SERVERS = [6000, 6001]
PORT_CLIENT = 5000

class Client:
    def __init__(self, client_id):
        self.client_id = client_id
        self.rs = []  # conjunto de leitura
        self.ws = []  # conjunto de escrita

    def read(self, x):

        # Verifica se o item já foi escrito localmente
        for item, val in reversed(self.ws):
            if item == x:
                resposta = {'item': x, 'value': val, 'version': -1}
                # Simula versão fictícia para manter consistência
                self.rs.append((x, val, -1))  # versão -1 marca leitura local
                print(f"Cliente {self.client_id} leu {resposta} do ws")
                return val

        # Seleciona um servidor aleatório
        servidor = random.choice(SERVERS)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.connect((HOST, servidor))

            # Envia requisição de leitura
            m = {'type': 'read', 'item': x}
            s.sendall(json.dumps(m).encode())

            # Recebe resposta com valor e versão
            resposta = json.loads(s.recv(4096).decode())
            self.rs.append((resposta['item'], resposta['value'], resposta['version']))
            print(f"Cliente {self.client_id} leu {resposta} do servidor {servidor}")
            return resposta['value']

    def write(self, x, val):

        # Armazena escrita localmente no write set (ainda não comitada)
        self.ws.append((x, val))
        print(f"Cliente {self.client_id} escreveu localmente: ({x}, {val})")

    def commit(self):

        # Monta transação com rs e ws e envia para o sequenciador
        tx = {
            'type': 'commit',
            'client_id': self.client_id,
            'rs': self.rs,
            'ws': self.ws
        }
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.connect((HOST, PORT_CLIENT))
            s.sendall(json.dumps(tx).encode())
        print(f"Cliente {self.client_id} enviou tx para commit.")