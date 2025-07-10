import socket
import threading
import json

HOST = 'localhost'

class Server:
    def __init__(self, port):
        self.db = {}                    # Banco de dados local: item -> (valor, versão)
        self.lock = threading.Lock()    # Proteção de concorrência
        self.port = port                # Porta onde o servidor escuta conexões

    def certifica(self, tx):

        # Realiza o teste de certificação da transação
        rs = tx['rs']
        ws = tx['ws']
        with self.lock:
            # Verifica se todos os itens lidos ainda possuem as mesmas versões
            for (x, val, versao) in rs:
                if x in self.db and self.db[x][1] != versao:
                    return 'abort'
            # Atualiza os itens do banco e incrementa a versão
            for (x, val) in ws:
                versao_atual = self.db[x][1] if x in self.db else 0
                self.db[x] = (val, versao_atual + 1)
            return 'commit'

    def trata_mensagem(self, conn):

        # Trata uma mensagem recebida via socket TCP
        m = conn.recv(4096)                             # Equivalente a primitiva receive()  

        if not m:
            return
        try:
            msg = json.loads(m.decode())

            # Cliente solicitou leitura de item x
            if msg['type'] == 'read':
                x = msg['item']
                with self.lock:
                    val, versao = self.db.get(x, (0, 0))
                resposta = {'item': x, 'value': val, 'version': versao}
                conn.sendall(json.dumps(resposta).encode())

            # Sequenciador enviou solicitação de commit
            elif msg['type'] == 'commit':
                resultado = self.certifica(msg)
                print(f"Servidor {self.port} - tx {msg['tx_id']} -> {resultado}")
        except Exception as e:
            print("Erro ao tratar mensagem no servidor:", e)

    def run(self):

        # Inicia o servidor e escuta conexões de clientes e sequenciador
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, self.port))
            s.listen()
            print(f"Servidor {self.port} ativo...")
            while True:
                conn, _ = s.accept()
                threading.Thread(target=self.trata_mensagem, args=(conn,)).start()