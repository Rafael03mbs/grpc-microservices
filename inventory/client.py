import grpc
import inventory_pb2
import inventory_pb2_grpc


def print_response(response):
    print(f"Response for {response.item_id}:")
    print(f"  Action: {inventory_pb2.Action.Name(response.action)}")
    print(f"  Reorder Quantity: {response.reorder_quantity}")
    print(f"  Explanation: {response.explanation_message}")


def run():
    print("Trying to communicate with Inventory Optimization Service...")
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = inventory_pb2_grpc.InventoryOptimizationStub(channel)

        print("--- Test Case 1: Low Stock ---")
        request = inventory_pb2.InventoryRequest(
            item_id="ITEM001",
            current_stock=10,
            predicted_demand=20,
            reorder_level=5,
            safety_stock=3,
            supplier_lead_time=1
        )
        try:
            response = stub.OptimizeInventory(request, timeout=5)
            print_response(response)
        except grpc.RpcError as e:
            print(f"RPC failed: {e.code()} - {e.details()}")

        print("\n--- Test Case 2: Sufficient Stock ---")
        request2 = inventory_pb2.InventoryRequest(
            item_id="ITEM002",
            current_stock=50,
            predicted_demand=15,
            reorder_level=10
        )
        try:
            response2 = stub.OptimizeInventory(request2, timeout=5)
            print_response(response2)
        except grpc.RpcError as e:
            print(f"RPC failed: {e.code()} - {e.details()}")

        print("\n--- Test Case 3: Batch Streaming ---")
        batch_request = inventory_pb2.BatchInventoryRequest(requests=[
            request,
            request2,
            inventory_pb2.InventoryRequest(
                item_id="ITEM003",
                current_stock=300,
                predicted_demand=20,
                reorder_level=10
            )
        ])
        try:
            for batch_response in stub.OptimizeInventoryBatch(batch_request, timeout=5):
                print_response(batch_response)
        except grpc.RpcError as e:
            print(f"RPC failed: {e.code()} - {e.details()}")

if __name__ == '__main__':
    run()
