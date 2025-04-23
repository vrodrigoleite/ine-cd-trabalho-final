# Controle de Concorrência em Transações com Replicação de Atualização Adiada (Deferred Update Replication)

## Contexto

Sistemas transacionais visam aumentar a concorrência em sistemas de gerenciamento de
dados, enquanto oferecem garantias de consistência e alta disponibilidade. Usando
protocolos para controle de concorrência, pode-se estabelecer o nível de consistência
desejável, garantindo que transações efetivadas não violem o critério de consistência
estipulado (ex. serializabilidade, snapshot isolation, etc.). A replicação surge como uma
estratégia para aumentar a disponibilidade e vazão do serviço.