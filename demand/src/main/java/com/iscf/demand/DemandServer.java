package com.iscf.demand;

import io.grpc.Server;
import io.grpc.ServerBuilder;
import java.io.IOException;

public class DemandServer {
    public static void main(String[] args) throws IOException, InterruptedException {
        Server server = ServerBuilder.forPort(50052)
            .addService(new DemandForecasterImpl())
            .build()
            .start();
        System.out.println("Demand Forecasting Service started on port 50052");
        server.awaitTermination();
    }
}
