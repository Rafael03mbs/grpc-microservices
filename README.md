# ISCF Lab 3 - Microservices Architecture with gRPC

Projeto para o Lab Assignment 3 de Integracao de Sistemas Ciber-Fisicos.

O sistema implementa uma arquitetura de microsservicos para recomendacoes de inventario num centro de distribuicao inteligente. A comunicacao interna entre componentes usa gRPC e o acesso do utilizador e feito atraves de uma API REST com uma pagina web simples.

## Arquitetura

Componentes principais:

- `demand`: MS1, servico Java de previsao de procura.
- `inventory`: MS2, servico Python de otimizacao de inventario.
- `api_gateway`: API REST em FastAPI e frontend web.
- `protobuf`: contratos gRPC usados pelos microsservicos.

Fluxo principal:

1. O utilizador adiciona um ou mais itens na pagina web.
2. A API REST recebe o lote de itens em `POST /api/orchestrate_batch`.
3. A API chama o MS1 por gRPC para calcular a procura prevista.
4. A API envia os pedidos ao MS2 por gRPC.
5. O MS2 devolve as recomendacoes usando server streaming.
6. A API agrega os resultados e devolve JSON ao frontend.

## MS1 - Demand Forecasting Service

Localizacao: `demand/`

Tecnologias:

- Java 11
- Maven
- gRPC
- Protocol Buffers

Contrato: `protobuf/demand.proto`

RPC principal:

- `ForecastDemand(DemandRequest) returns (DemandResponse)`

Entrada:

- `item_id`
- `historical_demand`
- `forecast_horizon`
- `warehouse_id`

Saida:

- `item_id`
- `predicted_demand`
- `forecast_confidence`
- `forecast_horizon`

Logica implementada:

- Valida `item_id`, `warehouse_id`, `forecast_horizon` e valores historicos.
- Usa uma media movel simples dos ultimos valores historicos.
- Ajusta a confianca com base no tamanho do historico e no horizonte de previsao.
- Devolve erros gRPC `INVALID_ARGUMENT` quando recebe valores invalidos.

## MS2 - Inventory Optimization Service

Localizacao: `inventory/`

Tecnologias:

- Python 3.9
- grpcio
- grpcio-tools

Contrato: `protobuf/inventory.proto`

RPCs principais:

- `OptimizeInventory(InventoryRequest) returns (InventoryResponse)`
- `OptimizeInventoryBatch(BatchInventoryRequest) returns (stream InventoryResponse)`

Entrada:

- `item_id`
- `current_stock`
- `predicted_demand`
- `reorder_level`
- `safety_stock` opcional
- `supplier_lead_time` opcional

Saida:

- `item_id`
- `reorder_quantity`
- `action`
- `explanation_message`

Acoes possiveis:

- `REORDER`
- `NO_ACTION`
- `SCALE_DOWN`

Logica implementada:

- Valida campos obrigatorios e impede valores negativos.
- Calcula um stock alvo com base em procura prevista, nivel de reposicao, stock de seguranca e tempo de entrega do fornecedor.
- Recomenda `REORDER` quando o stock atual esta abaixo do alvo.
- Recomenda `SCALE_DOWN` quando o stock esta muito acima do alvo.
- Recomenda `NO_ACTION` quando o stock cobre o alvo definido.

## API REST e Frontend

Localizacao: `api_gateway/`

Tecnologias:

- FastAPI
- Uvicorn
- Pydantic
- HTML, CSS e JavaScript

Endpoints:

- `GET /`: pagina web
- `GET /health`: estado basico da API
- `POST /api/orchestrate_batch`: orquestra previsao e recomendacao

O endpoint `POST /api/orchestrate_batch` recebe um lote de itens, chama o MS1 para obter a previsao de procura e chama o MS2 para obter recomendacoes de inventario por server streaming.

A API tambem converte erros gRPC para respostas HTTP adequadas:

- `INVALID_ARGUMENT` -> HTTP 400
- `UNAVAILABLE` -> HTTP 503
- Outros erros -> HTTP 500

## Streaming gRPC

A funcionalidade de streaming escolhida foi server streaming no MS2:

```proto
rpc OptimizeInventoryBatch (BatchInventoryRequest) returns (stream InventoryResponse) {}
```

Esta escolha e adequada porque a API envia um lote de itens e o servico de inventario pode devolver uma recomendacao de cada vez. Isto permite processar varios itens sem esperar que todo o lote esteja pronto antes de comecar a receber respostas.

## Estrutura do Projeto

```text
lab3/
  api_gateway/
    static/
      index.html
      script.js
      style.css
    Dockerfile
    main.py
    requirements.txt
  demand/
    src/main/java/com/iscf/demand/
      DemandForecasterImpl.java
      DemandServer.java
    Dockerfile
    pom.xml
  inventory/
    client.py
    dockerfile
    inventory_pb2.py
    inventory_pb2_grpc.py
    requirements.txt
    server.py
  protobuf/
    demand.proto
    inventory.proto
  docker-compose.yml
  Relatorio_ISCF_Lab3.md
  Walkthrough_ISCF_Lab3.md
```

## Execucao com Docker

Pre-requisito:

- Docker Desktop em execucao.

Na pasta do projeto:

```bash
docker compose up -d --build
```

Depois abrir:

```text
http://localhost:8000
```

Para ver o estado dos contentores:

```bash
docker compose ps
```

Para parar e remover os contentores:

```bash
docker compose down
```

## Teste REST

Exemplo de pedido para a API:

```bash
curl -X POST http://localhost:8000/api/orchestrate_batch \
  -H "Content-Type: application/json" \
  -d "{\"items\":[{\"item_id\":\"ITEM-001\",\"historical_demand\":[10,15,20,18,25],\"forecast_horizon\":7,\"warehouse_id\":\"WH-A\",\"current_stock\":20,\"reorder_level\":10,\"safety_stock\":5,\"supplier_lead_time\":1}]}"
```

Resposta esperada:

```json
{
  "results": [
    {
      "item_id": "ITEM-001",
      "predicted_demand": 21.0,
      "forecast_confidence": 0.85,
      "forecast_horizon": 7,
      "action": "REORDER",
      "reorder_quantity": 37,
      "explanation": "Stock below target (57). Recommendation includes demand, reorder level, safety stock and supplier lead-time buffer."
    }
  ]
}
```

## Notas de Desenvolvimento

- Os stubs Python da API e do MS2 sao gerados durante o build das imagens Docker.
- O servico Java gera as classes gRPC durante o build Maven.
- `target/`, `venv/` e `__pycache__/` nao sao necessarios no repositorio e podem ser regenerados.
- O frontend comunica apenas com a API REST; a comunicacao gRPC fica interna aos servicos.
