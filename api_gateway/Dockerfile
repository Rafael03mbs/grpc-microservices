FROM python:3.9-slim

WORKDIR /app
COPY api_gateway/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY protobuf ./protobuf
COPY api_gateway ./api_gateway

WORKDIR /app/api_gateway
RUN python -m grpc_tools.protoc -I../protobuf --python_out=. --grpc_python_out=. ../protobuf/inventory.proto
RUN python -m grpc_tools.protoc -I../protobuf --python_out=. --grpc_python_out=. ../protobuf/demand.proto

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
