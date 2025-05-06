# Protótipo DUR com protocolo robusto de mensagens (sem cabeçalho separado)
# Mensagens diferenciadas por chave JSON 'type': 'read' ou 'commit'

# ============================
# COMPONENTES:
# ----------------------------
# - Sequencer: recebe transações dos clientes e difunde via broadcast ordenado para todos os servidores replicados
# - Servidor: recebe transações e leituras, certifica com base no read_set e aplica escritas se válidas
# - Cliente: inicia transações, realiza leituras (read_set) e escritas (write_set), e envia commit para o sequenciador
# ============================

import socket
import threading
import json
import time
import random

HOST = 'localhost'
PORT_CLIENT = 5000
PORT_DB_BASE = 6000
SERVERS = [PORT_DB_BASE, PORT_DB_BASE + 1]

# ============ SEQUENCIADOR ============
# Responsável por receber commits dos clientes e garantir ordenação global dos commits
# através de broadcast (via envio sequencial para todos os servidores replicados)
class Sequencer:
    def __init__(self, server_ports):
        self.server_ports = server_ports
        self.tx_id = 0

    def handle_client(self, conn):
        data = conn.recv(4096)
        if not data:
            return
        tx_msg = json.loads(data.decode())
        if tx_msg.get('type') != 'commit':
            return
        tx_msg['tx_id'] = self.tx_id
        self.tx_id += 1

        for port in self.server_ports:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.connect((HOST, port))
                s.sendall(json.dumps(tx_msg).encode())

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, PORT_CLIENT))
            s.listen()
            print("Sequencer ativo...")
            while True:
                conn, _ = s.accept()
                threading.Thread(target=self.handle_client, args=(conn,)).start()

# ============ SERVIDOR ============
# Mantém uma cópia da base de dados (replicada)
# Responde a leituras e certifica/aplica commits conforme o protocolo DUR
class Server:
    def __init__(self, port):
        self.db = {}
        self.lock = threading.Lock()
        self.port = port

    def certify_and_apply(self, tx):
        with self.lock:
            for item, val, ver in tx['rs']:
                if item in self.db and self.db[item][1] != ver:
                    return 'abort'
            for item, val in tx['ws']:
                current_ver = self.db[item][1] if item in self.db else 0
                self.db[item] = (val, current_ver + 1)
            return 'commit'

    def handle_request(self, conn):
        data = conn.recv(4096)
        if not data:
            return
        try:
            msg = json.loads(data.decode())
            if msg.get('type') == 'read':
                item = msg['item']
                with self.lock:
                    value, version = self.db.get(item, (0, 0))
                response = {'item': item, 'value': value, 'version': version}
                conn.sendall(json.dumps(response).encode())
            elif msg.get('type') == 'commit':
                result = self.certify_and_apply(msg)
                print(f"Servidor {self.port} - tx {msg['tx_id']} -> {result}")
        except json.JSONDecodeError:
            print("Erro ao decodificar mensagem JSON")

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, self.port))
            s.listen()
            print(f"Servidor {self.port} ativo...")
            while True:
                conn, _ = s.accept()
                threading.Thread(target=self.handle_request, args=(conn,)).start()

# ============ CLIENTE ============
# Executa transações que realizam leituras (do servidor) e escritas (em memória local)
# Ao final envia requisição de commit para o sequenciador
class Client:
    def __init__(self, client_id):
        self.client_id = client_id
        self.rs = []
        self.ws = []

    def read(self, item):
        port = random.choice(SERVERS)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.connect((HOST, port))
            msg = {'type': 'read', 'item': item}
            s.sendall(json.dumps(msg).encode())
            data = s.recv(4096)
            res = json.loads(data.decode())
            self.rs.append((res['item'], res['value'], res['version']))
            print(f"Cliente {self.client_id} leu {res}")
            return res['value']

    def write(self, item, value):
        self.ws.append((item, value))
        print(f"Cliente {self.client_id} preparou escrita: ({item}, {value})")

    def commit(self):
        tx = {'type': 'commit', 'client_id': self.client_id, 'rs': self.rs, 'ws': self.ws}
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.connect((HOST, PORT_CLIENT))
            s.sendall(json.dumps(tx).encode())
        print(f"Cliente {self.client_id} enviou transação para commit.")


# ============ TESTES DE CONCORRÊNCIA ============
def teste1():
    # Duas transações concorrentes escrevendo no mesmo item
    c1 = Client('C1')
    c2 = Client('C2')

    def tx1():
        c1.read('x')
        time.sleep(0.5)
        c1.write('x', 10)
        c1.commit()

    def tx2():
        c2.read('x')
        time.sleep(0.1)
        c2.write('x', 20)
        c2.commit()

    threading.Thread(target=tx1).start()
    threading.Thread(target=tx2).start()

def teste2():
    # Transações isoladas em diferentes itens (sem conflitos)
    c3 = Client('C3')
    c4 = Client('C4')

    def tx3():
        c3.read('a')
        c3.write('a', 100)
        c3.commit()

    def tx4():
        c4.read('b')
        c4.write('b', 200)
        c4.commit()

    threading.Thread(target=tx3).start()
    threading.Thread(target=tx4).start()

def teste3():
    # Transação lendo valor obsoleto após outra transação escrever e commitar
    c5 = Client('C5')
    c6 = Client('C6')

    def tx5():
        c5.read('z')
        c5.write('z', 300)
        c5.commit()

    def tx6():
        time.sleep(1)
        c6.read('z')  # Lê valor novo
        time.sleep(1)
        c6.write('z', 400)
        c6.commit()  # Deve abortar, pois leu versão atualizada e foi ultrapassado por outra tx

    threading.Thread(target=tx5).start()
    threading.Thread(target=tx6).start()

def teste4():
    # 3 transações concorrentes sobre mesmo item
    c7 = Client('C7')
    c8 = Client('C8')
    c9 = Client('C9')

    def tx7():
        c7.read('m')
        time.sleep(0.1)
        c7.write('m', 1)
        c7.commit()

    def tx8():
        c8.read('m')
        time.sleep(0.3)
        c8.write('m', 2)
        c8.commit()

    def tx9():
        c9.read('m')
        time.sleep(0.5)
        c9.write('m', 3)
        c9.commit()

    threading.Thread(target=tx7).start()
    threading.Thread(target=tx8).start()
    threading.Thread(target=tx9).start()

# ============ EXECUÇÃO ============
if __name__ == '__main__':
    for p in SERVERS:
        threading.Thread(target=Server(p).run, daemon=True).start()
    time.sleep(1)

    threading.Thread(target=Sequencer(SERVERS).run, daemon=True).start()
    time.sleep(1)

    print("Iniciando Teste 1")
    teste1()
    time.sleep(5)

    print("Iniciando Teste 2")
    teste2()
    time.sleep(5)

    print("Iniciando Teste 3")
    teste3()
    time.sleep(5)

    print("Iniciando Teste 4")
    teste4()
    time.sleep(5)
