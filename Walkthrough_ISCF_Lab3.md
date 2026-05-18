# Guia Passo-a-Passo: Como construir o Lab 3 de Raiz

Este guia descreve o processo de desenvolvimento do projeto, com os passos principais, ferramentas e decisões técnicas necessárias.

---

## Passo 1: Planear a Estrutura de Pastas
O primeiro passo num projeto de microsserviços é garantir que os diferentes componentes estão isolados (preparando o terreno para os contentores Docker). Teria de criar as seguintes pastas:
- `protobuf/` -> Onde vivem os ficheiros de interface "neutros" (contratos gRPC).
- `inventory/` -> Onde vive o MS2 em Python.
- `demand/` -> Onde vive o MS1 em Java.
- `api_gateway/` -> Onde vive o servidor web e os ficheiros de interface gráfica.

---

## Passo 2: Escrever os Contratos de Comunicação (gRPC / Protobuf)
O gRPC requer que os serviços sejam definidos numa linguagem chamada "Protocol Buffers". Teria de criar:
1. **`inventory.proto`**: Define os parâmetros de entrada (Stock Atual, Procura, etc.) e saída (Quantidade a Encomendar, Ação). Para suportar *Streaming*, teria de declarar `returns (stream InventoryResponse)`.
2. **`demand.proto`**: Define que o Java vai receber um Array (lista) de valores históricos e devolver um número único (a previsão).

> **A Dificuldade aqui:** Lembrar-se da sintaxe do Protobuf (ex: usar `repeated` em vez de Listas/Arrays, e associar o número do índice de cada variável `int32 current_stock = 2;`).

---

## Passo 3: Implementar o Microsserviço Python (Inventory)
Teria de abrir o terminal e criar um ambiente virtual (venv) para instalar o gRPC:
`pip install grpcio grpcio-tools`

**3.1 Gerar o Código Base**
Em vez de programar a comunicação gRPC do zero, usaria o compilador do gRPC no terminal:
`python -m grpc_tools.protoc -I../protobuf --python_out=. --grpc_python_out=. ../protobuf/inventory.proto`
*Isto criaria dois ficheiros confusos (`_pb2.py` e `_pb2_grpc.py`) que contêm a infraestrutura de rede pesada.*

**3.2 Programar a Lógica (`server.py`)**
- Herdaria a classe `InventoryOptimizationServicer` gerada no passo anterior.
- Escreveria os blocos de validação e IF/ELSE para comparar as variáveis (se o stock estiver abaixo do alvo, então `REORDER`; se estiver suficiente, `NO_ACTION`; se estiver demasiado alto, `SCALE_DOWN`).
- Usaria o `yield` do Python em vez de `return` para implementar a funcionalidade de *Server Streaming*.

---

## Passo 4: Implementar o Microsserviço Java (Demand)
Programar gRPC em Java é mais complexo que em Python devido ao rigor da linguagem.

**4.1 Criar o `pom.xml` (Maven)**
Teria de criar um ficheiro Maven declarando dezenas de linhas de dependências (io.grpc, grpc-netty-shaded) e configurar o plugin incrivelmente detalhado `protobuf-maven-plugin` para que o Java percebesse como gerar as classes dos `.proto`.

**4.2 Programar o Servidor Java**
- Criar a classe que extende `DemandForecastingImplBase`.
- Substituir o método de previsão, somar os valores do array e dividir pelo seu comprimento para obter a média.
- Diferente do Python, em Java tem de interagir com o `StreamObserver`, chamando `.onNext(resposta)` e `.onCompleted()` para finalizar o processamento.

---

## Passo 5: Criar a API REST como Ponto de Entrada (FastAPI)
Para que uma página Web normal consiga falar com o gRPC (que não usa HTTP normal, mas sim HTTP/2 binário), precisamos de um "tradutor". O FastAPI serve para isso.

**Como faria:**
1. Criaria um ficheiro `main.py` com rotas normais como `@app.post("/api")`.
2. Dentro dessa rota, criaria *Canais Inseguros* de gRPC para conectar aos serviços:
   `grpc.insecure_channel('ms1-demand:50052')`
3. A lógica interna da API faria a orquestração:
   - "Primeiro, liga ao Java e pede as previsões."
   - "Depois, pega nessas previsões, junta o stock, liga ao Python e inicia um Stream."
   - "Por fim, devolve tudo num dicionário JSON para o navegador."

---

## Passo 6: O Frontend Web (HTML + JS + CSS)
Aqui é pura programação Web.
- Escrever um documento `index.html` com caixas de texto (*inputs*) para os vários parâmetros de um item.
- Escrever código JavaScript (*Fetch API*) que deteta o clique no botão, converte os números recolhidos e os envia no formato JSON via `POST` para o `/api`.
- Adicionar o CSS, desenhando as cores e *shadows* manualmente.

---

## Passo 7: Contentorização com Docker
Esta é a última peça do puzzle. Teria de criar um `Dockerfile` para cada um dos três serviços.

**O segredo do Docker no gRPC:**
Para garantir que tudo compila sem erros dependentes do seu computador pessoal, nos `Dockerfiles` do Python (Inventory e API), incluiria a instrução que executa o `grpc_tools.protoc` *durante* a construção da imagem do Docker. Assim o código gRPC é sempre construído "fresquinho" no Linux, evitando problemas do Windows.

Para o Java, usaria um Dockerfile "Multi-Stage":
1. Começa com uma imagem pesada do `Maven` para compilar o código.
2. Copia o ficheiro `.jar` final para uma imagem leve de `Eclipse-Temurin 11` (JRE), cortando o peso do contentor de 600MB para menos de 100MB.

---

## Passo 8: Ligar Tudo com o Docker Compose
Por fim, não iria querer ligar 3 contentores à mão. Escreveria o ficheiro `docker-compose.yml`.
Este ficheiro vai:
1. Colocar o Java, Python e a API Gateway dentro de uma **rede virtual privada**.
2. O MS1 Java e MS2 Python não iriam expor as suas portas para o seu computador, mas conseguiriam comunicar internamente entre si através do nome do serviço (`ms1-demand`).
3. O API Gateway seria o único exposto para o exterior (na porta `8000`), garantindo segurança.

Executar `docker-compose up --build` inicia a arquitetura completa.
