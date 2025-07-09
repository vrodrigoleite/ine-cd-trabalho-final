import threading
import time
from cliente import Client
from servidor import Server
from sequenciador import Sequencer

HOST = 'localhost'
SERVERS = [6000, 6001]

# Inicializa servidores
for p in SERVERS:
    threading.Thread(target=Server(p).run, daemon=True).start()
time.sleep(1)

# Inicializa sequenciador
threading.Thread(target=Sequencer(SERVERS).run, daemon=True).start()
time.sleep(1)

# ============ TESTES DE CONCORRÊNCIA ============

def teste1():
    print("\n[Teste 1] Duas transações sobre mesmo item (x)")
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
    print("\n[Teste 2] Transações independentes (a, b)")
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
    print("\n[Teste 3] Leitura obsoleta seguida de escrita (z)")
    c5 = Client('C5')
    c6 = Client('C6')

    def tx5():
        time.sleep(1)  # atraso proposital: permite C6 ler antes
        c5.read('z')
        c5.write('z', 300)
        c5.commit()

    def tx6():
        c6.read('z')  # lê versão antiga
        time.sleep(2)  # espera C5 comitar
        c6.write('z', 400)
        c6.commit()

    threading.Thread(target=tx5).start()
    threading.Thread(target=tx6).start()


def teste4():
    print("\n[Teste 4] Três transações sobre o mesmo item (m)")
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

def teste5():
    print("\n[Teste 5] Leitura local após escrita no item (k)")
    c10 = Client('C10')
    def tx10():
        c10.read('k') 
        c10.write('k', 123)             # Escreve localmente no ws
        c10.read('k')                   # Deve ler do ws sem consultar servidor
        c10.commit()                    # Commit deve conter rs com versão fictícia
        
    threading.Thread(target=tx10).start()


# Executa os testes sequencialmente
if __name__ == '__main__':
    # teste1()
    # time.sleep(5)
    # teste2()
    # time.sleep(5)
    # teste3() 
    # time.sleep(5)
    # teste4()
    # time.sleep(5)
    teste5()
    time.sleep(5)