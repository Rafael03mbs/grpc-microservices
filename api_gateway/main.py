from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, validator
import grpc
import math
import os
from typing import List, Optional

import demand_pb2
import demand_pb2_grpc
import inventory_pb2
import inventory_pb2_grpc

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

MS1_HOST = os.getenv("MS1_HOST", "localhost:50052")
MS2_HOST = os.getenv("MS2_HOST", "localhost:50051")

class ItemPayload(BaseModel):
    item_id: str = Field(..., min_length=1)
    historical_demand: List[float] = Field(..., min_items=1)
    forecast_horizon: int = Field(..., gt=0)
    warehouse_id: str = Field("WH-Main", min_length=1)
    current_stock: int = Field(..., ge=0)
    reorder_level: int = Field(..., ge=0)
    safety_stock: Optional[int] = Field(None, ge=0)
    supplier_lead_time: Optional[int] = Field(None, ge=0)

    @validator("item_id", "warehouse_id")
    def strip_required_text(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @validator("historical_demand")
    def demand_values_must_be_non_negative(cls, values):
        if any(value < 0 for value in values):
            raise ValueError("historical_demand values cannot be negative")
        return values

class BatchPayload(BaseModel):
    items: List[ItemPayload] = Field(..., min_items=1)


def raise_grpc_http_error(service_name, error):
    if error.code() == grpc.StatusCode.INVALID_ARGUMENT:
        status_code = 400
    elif error.code() == grpc.StatusCode.UNAVAILABLE:
        status_code = 503
    else:
        status_code = 500

    detail = error.details() or error.code().name
    raise HTTPException(status_code=status_code, detail=f"{service_name}: {detail}")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/orchestrate_batch")
def orchestrate_batch(payload: BatchPayload):
    results = []
    
    with grpc.insecure_channel(MS1_HOST) as channel1, grpc.insecure_channel(MS2_HOST) as channel2:
        demand_stub = demand_pb2_grpc.DemandForecastingStub(channel1)
        inventory_stub = inventory_pb2_grpc.InventoryOptimizationStub(channel2)
        
        inventory_requests = []
        forecasts = []
        
        # Unary calls to MS1
        for item in payload.items:
            try:
                demand_req = demand_pb2.DemandRequest(
                    item_id=item.item_id,
                    historical_demand=item.historical_demand,
                    forecast_horizon=item.forecast_horizon,
                    warehouse_id=item.warehouse_id
                )
                demand_resp = demand_stub.ForecastDemand(demand_req, timeout=5)
                forecasts.append({
                    "item_id": item.item_id,
                    "predicted_demand": demand_resp.predicted_demand,
                    "forecast_confidence": demand_resp.forecast_confidence,
                    "forecast_horizon": demand_resp.forecast_horizon
                })
                
                inv_request_fields = {
                    "item_id": item.item_id,
                    "current_stock": item.current_stock,
                    "predicted_demand": math.ceil(demand_resp.predicted_demand),
                    "reorder_level": item.reorder_level
                }
                if item.safety_stock is not None:
                    inv_request_fields["safety_stock"] = item.safety_stock
                if item.supplier_lead_time is not None:
                    inv_request_fields["supplier_lead_time"] = item.supplier_lead_time

                inv_req = inventory_pb2.InventoryRequest(
                    **inv_request_fields
                )
                inventory_requests.append(inv_req)
            except grpc.RpcError as e:
                raise_grpc_http_error(f"MS1 Error for {item.item_id}", e)

        # Server Streaming call to MS2
        try:
            batch_req = inventory_pb2.BatchInventoryRequest(requests=inventory_requests)
            responses = inventory_stub.OptimizeInventoryBatch(batch_req, timeout=10)
            for inv_resp, forecast in zip(responses, forecasts):
                results.append({
                    "item_id": inv_resp.item_id,
                    "predicted_demand": forecast["predicted_demand"],
                    "forecast_confidence": forecast["forecast_confidence"],
                    "forecast_horizon": forecast["forecast_horizon"],
                    "action": inventory_pb2.Action.Name(inv_resp.action),
                    "reorder_quantity": inv_resp.reorder_quantity,
                    "explanation": inv_resp.explanation_message
                })
        except grpc.RpcError as e:
            raise_grpc_http_error("MS2 Error", e)

    return {"results": results}
