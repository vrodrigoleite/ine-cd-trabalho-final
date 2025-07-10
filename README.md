# Protocolo DUR - Replicação de Atualização Adiada

Este projeto implementa o protocolo **Deferred Update Replication (DUR)** com base nos algoritmos apresentados em aula, utilizando Python e comunicação via sockets TCP.

## 📁 Estrutura do Projeto

```
.
├── cliente.py            # Implementação do Algoritmo 3 (Cliente DUR)
├── servidor.py           # Implementação do Algoritmo 4 (Servidor DUR)
├── sequenciador.py       # Difusão ordenada das transações para os servidores
├── teste_concorrencia.py # Execução de 5 testes concorrentes simultâneos
├── README.md             # Este documento
```

## 🚀 Como Executar

1. **Pré-requisitos**:

   * Python 3.8 ou superior
   * Sistema operacional com suporte a sockets (Linux/macOS/Windows)

2. **Executar o script de testes**:

```bash
python3 teste_concorrencia.py
```

Esse script:

* Inicia 2 servidores replicados
* Inicia o sequenciador
* Executa 5 testes de concorrência com múltiplos clientes

## 🔬 Testes Implementados

### ✅ Teste 1 - Concorrência sobre o mesmo item (`x`)

* Duas transações tentam escrever sobre `x` com interleaving
* Espera-se que uma seja abortada devido à certificação

### ✅ Teste 2 - Transações independentes (`a`, `b`)

* Transações sobre chaves diferentes
* Ambas devem ser comitadas

### ✅ Teste 3 - Leitura obsoleta seguida de escrita (`z`)

* Uma transação lê `z`, enquanto outra já escreveu
* A segunda deve ser abortada

### ✅ Teste 4 - Três transações sobre o mesmo item (`m`)

* Escritas escalonadas e não sincronizadas
* Certificação controla quais commits são aceitos

### ✅ Teste 5 - Leitura local após escrita (`k`)

* Cliente escreve em `k` e depois lê `k` na mesma transação
* A leitura deve ser feita diretamente do `write set` local (sem acesso ao servidor)
* Confirma que a coerência da transação é mantida internamente

## 🧠 Organização do Código

* **cliente.py**:

  * Armazena localmente `rs` (read set) e `ws` (write set)
  * Executa operações e envia commit para o sequenciador

* **servidor.py**:

  * Responde leituras com valor e versão
  * Recebe commits e executa teste de certificação

* **sequenciador.py**:

  * Atribui identificador global (`tx_id`) à transação
  * Difunde ordenadamente para todos os servidores

## 📝 Observações

* A comunicação usa apenas TCP com serialização JSON
* Nenhum mecanismo de tolerância a falhas está incluído (assumimos nodos confiáveis)
* O projeto segue os algoritmos apresentados por Pedone e Schiper (2012) e Mendizabal et al. (2013)

---

Para dúvidas ou sugestões, entre em contato com o autor ou equipe responsável pelo trabalho.
