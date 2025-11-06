# Multi-stage build for ABSA Service
FROM gradle:8.8-jdk21-alpine AS builder

# Set build directory
WORKDIR /home/gradle/build

# Copy Gradle configuration files for dependency resolution
COPY settings.gradle .
COPY build.gradle .
COPY gateway/build.gradle gateway/build.gradle
COPY collector/build.gradle collector/build.gradle
COPY analysis/build.gradle analysis/build.gradle
COPY absa/build.gradle absa/build.gradle
COPY alert/build.gradle alert/build.gradle
COPY osint-orchestrator/build.gradle osint-orchestrator/build.gradle
COPY osint-planning/build.gradle osint-planning/build.gradle
COPY osint-source/build.gradle osint-source/build.gradle

# Download dependencies (this layer will be cached)
RUN gradle :absa:dependencies --no-daemon

# Copy absa source code
COPY absa/src ./absa/src

# Build only the absa service
RUN gradle :absa:bootJar -x test --no-daemon

# Runtime stage
FROM eclipse-temurin:21-jre-alpine

WORKDIR /app

# Create non-root user for security
RUN addgroup -S spring && adduser -S spring -G spring
USER spring:spring

# Copy built JAR from builder stage
COPY --from=builder /home/gradle/build/absa/build/libs/*.jar app.jar

# Expose application port
EXPOSE 8003

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8003/actuator/health || exit 1

# Run the application
ENTRYPOINT ["java", "-XX:+UseContainerSupport", "-XX:MaxRAMPercentage=75.0", "-Djava.security.egd=file:/dev/./urandom", "-jar", "app.jar"]
