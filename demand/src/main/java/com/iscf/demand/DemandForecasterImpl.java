package com.iscf.demand;

import io.grpc.Status;
import io.grpc.stub.StreamObserver;

public class DemandForecasterImpl extends DemandForecastingGrpc.DemandForecastingImplBase {
    @Override
    public void forecastDemand(DemandRequest request, StreamObserver<DemandResponse> responseObserver) {
        System.out.println("Received forecast request for item: " + request.getItemId());

        if (request.getItemId().trim().isEmpty()) {
            responseObserver.onError(
                Status.INVALID_ARGUMENT.withDescription("item_id is required").asRuntimeException()
            );
            return;
        }
        if (request.getWarehouseId().trim().isEmpty()) {
            responseObserver.onError(
                Status.INVALID_ARGUMENT.withDescription("warehouse_id is required").asRuntimeException()
            );
            return;
        }
        if (request.getForecastHorizon() <= 0) {
            responseObserver.onError(
                Status.INVALID_ARGUMENT.withDescription("forecast_horizon must be greater than zero").asRuntimeException()
            );
            return;
        }

        int count = request.getHistoricalDemandCount();
        if (count == 0) {
            responseObserver.onError(
                Status.INVALID_ARGUMENT.withDescription("historical_demand must contain at least one value").asRuntimeException()
            );
            return;
        }

        for (float value : request.getHistoricalDemandList()) {
            if (value < 0) {
                responseObserver.onError(
                    Status.INVALID_ARGUMENT.withDescription("historical_demand values cannot be negative").asRuntimeException()
                );
                return;
            }
        }

        float sum = 0;
        int windowStart = Math.max(0, count - 3);
        for (int i = windowStart; i < count; i++) {
            sum += request.getHistoricalDemand(i);
        }

        int windowSize = count - windowStart;
        float predicted = sum / windowSize;
        float confidence = count >= 5 ? 0.85f : 0.65f;
        if (request.getForecastHorizon() > 14) {
            confidence -= 0.10f;
        }
        if (request.getForecastHorizon() > 30) {
            confidence -= 0.10f;
        }
        confidence = Math.max(confidence, 0.40f);
        
        DemandResponse response = DemandResponse.newBuilder()
            .setItemId(request.getItemId())
            .setPredictedDemand(predicted)
            .setForecastConfidence(confidence)
            .setForecastHorizon(request.getForecastHorizon())
            .build();
            
        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }
}
