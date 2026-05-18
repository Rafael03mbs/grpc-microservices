# Relatório Técnico - Integração de Sistemas Ciber-Físicos (ISCF)
## Lab Assignment 3: Microservices Architecture with gRPC

**Objetivo:** Desenvolvimento de uma arquitetura baseada em microsserviços para otimização e gestão de inventário de um centro de distribuição inteligente, utilizando gRPC para a comunicação interna e uma API REST como porta de entrada.

---

## 1. Arquitetura do Sistema

O sistema final é constituído por três componentes principais, totalmente contentorizados utilizando Docker e orquestrados através do `docker-compose`:

1. **MS1 - Demand Forecasting Service (Java)**: Um microsserviço que recebe dados históricos e fornece uma previsão de procura com base numa média simples.
2. **MS2 - Inventory Optimization Service (Python)**: Um microsserviço que consome a previsão do MS1, analisa o stock atual e os níveis de re-encomenda, e devolve ações recomendadas (`REORDER`, `NO_ACTION` ou `SCALE_DOWN`).
3. **API Gateway & Frontend (Python / FastAPI / HTML+JS)**: O ponto de entrada unificado que expõe uma interface gráfica avançada ao utilizador, orquestrando as chamadas aos microsserviços por gRPC.

---

## 2. Implementação e Tecnologias

### 2.1 MS1 (Java): Serviço de Previsão de Procura
- **Tecnologias:** Java 11, Maven, gRPC.
- **Protobuf (`demand.proto`):** Expõe um serviço unário `ForecastDemand` que recebe o histórico e devolve a previsão (`predicted_demand`).
- **Lógica:** Implementa o `DemandForecasterImpl`, percorrendo o histórico fornecido (vetor de valores flutuantes) para calcular a média da procura. O Maven foi configurado para gerar automaticamente as classes na compilação utilizando o `protobuf-maven-plugin`.

### 2.2 MS2 (Python): Serviço de Otimização de Inventário
- **Tecnologias:** Python 3.9, grpcio.
- **Protobuf (`inventory.proto`):** Expõe o serviço `OptimizeInventoryBatch`. Em resposta ao requisito de *Streaming* do projeto, este endpoint **utiliza Server Streaming**, o que permite que a API Gateway envie uma lista de itens e receba os resultados em fluxo contínuo (*stream*).
- **Lógica:** Calcula um stock alvo com base em `predicted_demand`, `reorder_level`, `safety_stock` e `supplier_lead_time`. Se o stock atual estiver abaixo desse alvo, devolve `REORDER` e calcula a quantidade a encomendar. Se o stock estiver muito acima do alvo, devolve `SCALE_DOWN`; caso contrário, devolve `NO_ACTION`.

### 2.3 API Gateway & Orquestração (FastAPI)
- **Tecnologias:** FastAPI, Uvicorn, pydantic.
- Exposta no porto `8000`, processa o pedido REST (`POST /api/orchestrate_batch`) proveniente da aplicação web.
- **Orquestração:**
  1. Estabelece ligação aos dois microsserviços (utilizando os DNS internos do Docker `ms1-demand` e `ms2-inventory`).
  2. Executa chamadas síncronas/unárias ao MS1 para obter a previsão de *todos* os itens do lote.
  3. Com as previsões recolhidas, inicia uma chamada **Server Streaming** com o MS2 (`OptimizeInventoryBatch`).
  4. Agrega os resultados e devolve via HTTP ao navegador.

### 2.4 Interface Web (Web App)
- **Design:** Criada usando um sistema de design moderno, dinâmico e focado no estilo "glassmorphism", com animações suaves de fundo e cartões estruturados. Totalmente desenvolvida em *Vanilla JS* e CSS.
- **Funcionalidade:** O utilizador preenche os dados dos itens a analisar. Estes são adicionados a uma fila de processamento (*batch queue*). Ao clicar em "Orchestrate Analysis", a interface consome a API e visualiza os resultados de otimização em cartões codificados por cor.

---

## 3. Contentorização (Docker)

Todo o ecossistema é iniciado de forma independente graças ao ficheiro `docker-compose.yml`.
- A API expõe apenas o porto `8000` para a máquina hospedeira (evitando a exposição direta dos microsserviços gRPC).
- Os microsserviços ligam-se numa rede privada `iscf_network`, com compilação dinâmica dos *stubs* de protobuf (tanto para Python como para Java) durante a fase de `build` das imagens. Isto significa que a compilação do `protoc` ocorre de forma isolada no Docker, tornando a solução 100% resistente a falhas relacionadas com o sistema operativo da máquina hospedeira.

---

## 4. Instruções de Execução

1. Certifique-se de que a aplicação **Docker Desktop** está em execução.
2. Abra o terminal na diretoria `c:\Users\rafae\Desktop\ISCF\lab3`.
3. Inicie o projeto com o comando:
   ```bash
   docker-compose up -d --build
   ```
4. Aceda à Interface Web através do navegador: **[http://localhost:8000](http://localhost:8000)**.
5. Insira os dados de teste na aplicação (ex: Histórico de 10,15,20 com Stock Atual de 50) e observe a recomendação inteligente que é devolvida.
