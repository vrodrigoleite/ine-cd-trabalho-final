import socket
import threading
import json

HOST = 'localhost'
PORT_CLIENT = 5000

class Sequencer:
    def __init__(self, server_ports):
        self.server_ports = server_ports
        self.tx_id = 0

    def handle_client(self, conn):
        # Recebe dados do cliente
        m = conn.recv(4096)
        if not m:
            return
        
        # Decodifica a transação enviada
        tx = json.loads(m.decode())

        # Apenas mensagens do tipo 'commit' devem ser tratadas
        if tx.get('type') != 'commit':
            return
        
        # Atribui identificador único de transação (tx_id)
        tx['tx_id'] = self.tx_id
        self.tx_id += 1

        # Difusão para todos os servidores replicados
        for port in self.server_ports:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.connect((HOST, port))
                s.sendall(json.dumps(tx).encode())

    def run(self):
        
        # Inicia o socket do sequenciador para escutar conexões de clientes
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, PORT_CLIENT))
            s.listen()
            print("Sequencer ativo...")

            # Laço infinito para aceitar conexões de clientes
            while True:
                conn, _ = s.accept()
                threading.Thread(target=self.handle_client, args=(conn,)).start()