import grpc
from concurrent import futures
import logging

import inventory_pb2
import inventory_pb2_grpc


def _get_optional_int(request, field_name, default=0):
    try:
        return getattr(request, field_name) if request.HasField(field_name) else default
    except ValueError:
        return default


def _validate_request(request, context):
    if not request.item_id.strip():
        context.abort(grpc.StatusCode.INVALID_ARGUMENT, "item_id is required")

    if request.current_stock < 0:
        context.abort(grpc.StatusCode.INVALID_ARGUMENT, "current_stock cannot be negative")
    if request.predicted_demand < 0:
        context.abort(grpc.StatusCode.INVALID_ARGUMENT, "predicted_demand cannot be negative")
    if request.reorder_level < 0:
        context.abort(grpc.StatusCode.INVALID_ARGUMENT, "reorder_level cannot be negative")

    safety_stock = _get_optional_int(request, "safety_stock")
    supplier_lead_time = _get_optional_int(request, "supplier_lead_time")

    if safety_stock < 0:
        context.abort(grpc.StatusCode.INVALID_ARGUMENT, "safety_stock cannot be negative")
    if supplier_lead_time < 0:
        context.abort(grpc.StatusCode.INVALID_ARGUMENT, "supplier_lead_time cannot be negative")

    return safety_stock, supplier_lead_time


def _calculate_recommendation(request, safety_stock, supplier_lead_time):
    lead_time_buffer = request.predicted_demand * supplier_lead_time
    target_stock = request.predicted_demand + request.reorder_level + safety_stock + lead_time_buffer

    if request.current_stock < target_stock:
        reorder_quantity = target_stock - request.current_stock
        return (
            reorder_quantity,
            inventory_pb2.REORDER,
            (
                f"Stock below target ({target_stock}). Recommendation includes demand, "
                "reorder level, safety stock and supplier lead-time buffer."
            ),
    )

    scale_down_threshold = max(target_stock * 2, request.reorder_level + safety_stock)
    if request.current_stock > 0 and request.current_stock > scale_down_threshold:
        return (
            0,
            inventory_pb2.SCALE_DOWN,
            f"Stock is well above target ({target_stock}). Consider reducing replenishment.",
        )

    return (
        0,
        inventory_pb2.NO_ACTION,
        f"Stock covers the target level ({target_stock}). No replenishment is needed.",
    )


class InventoryOptimizationServicer(inventory_pb2_grpc.InventoryOptimizationServicer):
    def OptimizeInventory(self, request, context):
        print(f"Received request for item: {request.item_id}")

        safety_stock, supplier_lead_time = _validate_request(request, context)
        reorder_quantity, action, explanation = _calculate_recommendation(
            request, safety_stock, supplier_lead_time
        )

        return inventory_pb2.InventoryResponse(
            item_id=request.item_id,
            reorder_quantity=reorder_quantity,
            action=action,
            explanation_message=explanation
        )

    def OptimizeInventoryBatch(self, request, context):
        print(f"Received batch request with {len(request.requests)} items")
        for req in request.requests:
            safety_stock, supplier_lead_time = _validate_request(req, context)
            reorder_quantity, action, explanation = _calculate_recommendation(
                req, safety_stock, supplier_lead_time
            )

            yield inventory_pb2.InventoryResponse(
                item_id=req.item_id,
                reorder_quantity=reorder_quantity,
                action=action,
                explanation_message=explanation
            )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    inventory_pb2_grpc.add_InventoryOptimizationServicer_to_server(
        InventoryOptimizationServicer(), server
    )
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Inventory Optimization Service started on port 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig()
    serve()
