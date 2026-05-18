FROM maven:3.8-eclipse-temurin-11 AS build
WORKDIR /app
COPY demand/pom.xml .
RUN mvn dependency:go-offline

COPY protobuf ./src/main/proto
COPY demand/src ./src

RUN mvn clean package -DskipTests

FROM eclipse-temurin:11-jre
WORKDIR /app
COPY --from=build /app/target/demand-service-1.0-SNAPSHOT.jar app.jar
EXPOSE 50052
CMD ["java", "-jar", "app.jar"]
