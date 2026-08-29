# gRPC Microservices — Inventory Management System

Distributed microservices system for inventory management and demand forecasting, developed as part of the Interconnected Systems and Computer Fundamentals (ISCF) course at FCT NOVA.

Grade: 20 / 20

---

## Overview

This project implements a production-grade microservices architecture where three independent services communicate exclusively via gRPC and Protocol Buffers. The entire system is containerised with Docker and orchestrated with Docker Compose.

---

## Architecture

**MS1 — Demand Forecasting Service (Java)**
- Exposes a unary gRPC endpoint `ForecastDemand`
- Receives historical demand data and returns a predicted demand value using a moving average algorithm
- Built with Java 11, Maven, and the `protobuf-maven-plugin` for automatic code generation

**MS2 — Inventory Optimization Service (Python)**
- Exposes a server-streaming gRPC endpoint `OptimizeInventoryBatch`
- Consumes MS1's forecast, evaluates current stock against reorder levels, and streams back recommended actions (`REORDER`, `NO_ACTION`, `SCALE_DOWN`) for each item
- Built with Python 3.9 and `grpcio`

**API Gateway and Frontend (Python / FastAPI)**
- Single entry point for all client requests
- Orchestrates calls to MS1 and MS2 via gRPC
- Exposes an interactive HTML/JS dashboard for real-time monitoring and manual queries

---

## Repository Structure

```
grpc-microservices/
├── demand/                  # MS1 — Java demand forecasting service
├── inventory/               # MS2 — Python inventory optimization service
├── api_gateway/             # FastAPI gateway and HTML frontend
├── protobuf/                # Shared .proto definitions
├── docker-compose.yml       # Service orchestration
├── Relatorio_ISCF_Lab3.md   # Technical report
└── Walkthrough_ISCF_Lab3.md # Step-by-step implementation guide
```

---

## Prerequisites

- Docker and Docker Compose

---

## How to Run

```bash
docker-compose up --build
```

The dashboard is available at `http://localhost:8000` once all services are healthy.

---

## Tech Stack

| Component | Technology |
|---|---|
| Inter-service communication | gRPC, Protocol Buffers |
| MS1 | Java 11, Maven |
| MS2 | Python 3.9, grpcio |
| Gateway | Python, FastAPI, uvicorn |
| Containerisation | Docker, Docker Compose |

---

## Author

Rafael Martins Batista da Silva
MSc Electrical Engineering — FCT NOVA
[github.com/Rafael03mbs](https://github.com/Rafael03mbs)
