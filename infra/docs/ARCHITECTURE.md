# AWS IoT Project Architecture

## System Diagram

```
┌───────────────────────────────────────────────────────────────────────┐
│                                  AWS CLOUD                            │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │                            VPC (10.0.0.0/16)                   │   │
│  │                                                                │   │
│  │  ┌──────────────────────────┐  ┌──────────────────────────┐    │   │
│  │  │  Public Subnet AZ-a      │  │  Public Subnet AZ-b      │    │   │
│  │  │  (10.0.10.0/24)          │  │  (10.0.11.0/24)          │    │   │
│  │  │                          │  │                          │    │   │
│  │  │  ┌──────────────────┐    │  │                          │    │   │
│  │  │  │  NAT Gateway     │    │  │                          │    │   │
│  │  │  │  (Elastic IP)    │    │  │                          │    │   │
│  │  │  └────────┬─────────┘    │  │                          │    │   │
│  │  └───────────┼──────────────┘  └──────────────────────────┘    │   │
│  │              │                                                 │   │
│  │              │ ┌──────────────────────────────────────────┐    │   │
│  │              │ │    Internet Gateway                      │    │   │
│  │              │ └──────────────┬───────────────────────────┘    │   │
│  │              │                │                                │   │
│  │  ┌───────────┼────────────────┼──────────────────────────┐     │   │
│  │  │  Private Subnet AZ-a       │                          │     │   │
│  │  │  (10.0.1.0/24)             │ (routes via NAT GW)      │     │   │
│  │  │                            │                          │     │   │
│  │  │  ┌──────────────────┐      │                          │     │   │
│  │  │  │  ECS Fargate     │──────┘                          │     │   │
│  │  │  │  Task (Backend)  │  ◄── Only 1 task (desired=1)    │     │   │
│  │  │  │  Port: 8001      │────┐ Could deploy to AZ-b       │     │   │
│  │  │  │  (service_sg)    │    │                            │     │   │
│  │  │  └──────────────────┘    │                            │     │   │
│  │  │                          │                            │     │   │
│  │  │  ┌──────────────────┐    │                            │     │   │
│  │  │  │  Lambda Function │    │                            │     │   │
│  │  │  │  (iot_handler)   │────┤                            │     │   │
│  │  │  │  (lambda_sg)     │    │                            │     │   │
│  │  │  └──────────────────┘    │                            │     │   │
│  │  │                          │                            │     │   │
│  │  │                          │  ┌──────────────────┐      │     │   │
│  │  │                          └─►│  RDS Proxy       │      │     │   │
│  │  │                             │  (PostgreSQL)    │      │     │   │
│  │  │                             └────────┬─────────┘      │     │   │
│  │  │                                      │                │     │   │
│  │  │                                      ▼                │     │   │
│  │  │                             ┌──────────────────┐      │     │   │
│  │  │                             │  RDS PostgreSQL  │      │     │   │
│  │  │                             │  (db.t3.micro)   │      │     │   │
│  │  │                             │  Port: 5432      │      │     │   │
│  │  │                             │  (rds_sg)        │      │     │   │
│  │  │                             └──────────────────┘      │     │   │
│  │  └───────────────────────────────────────────────────────┘     │   │
│  │                                                                │   │
│  │  ┌──────────────────────────────────────────────────────┐      │   │
│  │  │  Private Subnet AZ-b (10.0.2.0/24)                   │      │   │
│  │  │                                                      │      │   │
│  │  │  [No ECS tasks currently deployed here]              │      │   │
│  │  │                                                      │      │   │
│  │  │  * Required for RDS multi-AZ subnet group            │      │   │
│  │  │  * Available for Lambda failover                     │      │   │
│  │  │  * Available if ECS scales up (desired_count > 1)    │      │   │
│  │  └──────────────────────────────────────────────────────┘      │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  AWS IoT Core                                                  │   │
│  │                                                                │   │
│  │  ┌──────────────────┐         ┌──────────────────┐             │   │
│  │  │  IoT Topic Rule  │────────►│  Lambda Function │             │   │
│  │  │  'sensors/#'     │         │  (iot_handler)   │             │   │
│  │  └──────────────────┘         └──────────────────┘             │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  ECR (Elastic Container Registry)                              │   │
│  │                                                                │   │
│  │  ┌──────────────────┐                                          │   │
│  │  │  Docker Image    │◄────── ECS pulls images via NAT GW       │   │
│  │  │  (Backend App)   │                                          │   │
│  │  └──────────────────┘                                          │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  Secrets Manager                                               │   │
│  │                                                                │   │
│  │  ┌──────────────────┐                                          │   │
│  │  │  RDS Credentials │◄────── Lambda & RDS Proxy access         │   │
│  │  └──────────────────┘                                          │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
         ▲
         │
         │ MQTT (Port 8883)
         │
    ┌────┴─────┐
    │ IoT      │
    │ Devices  │
    └──────────┘
```

## Data Flow

### 1. IoT Device → Database (via Lambda)
```
IoT Device 
  → (MQTT) AWS IoT Core 
  → IoT Topic Rule (sensors/#)
  → Lambda Function (in Private Subnet)
  → RDS Proxy
  → PostgreSQL Database
```

### 2. Backend API → Database
```
ECS Fargate Task (Backend)
  → RDS Proxy
  → PostgreSQL Database
```

### 3. Internet Access (for pulling Docker images, external APIs)
```
ECS Task / Lambda
  → NAT Gateway (in Public Subnet)
  → Internet Gateway
  → Internet (ECR, etc.)
```

## Security Groups

| Security Group | Ingress | Egress | Purpose |
|---------------|---------|--------|---------|
| `service_sg` | Port 8001 from [] | All traffic | ECS Fargate tasks |
| `lambda_sg` | None | All traffic | Lambda functions |
| `rds_sg` | Port 5432 from `lambda_sg` & `service_sg` | All traffic | RDS & RDS Proxy |

## Key Components

### Compute
- **ECS Fargate**: Runs containerized backend API (port 8001)
  - Task: 256 CPU, 512 MB memory
  - **Current deployment**: 1 task (desired_count = 1)
  - Configured for 2 AZs but only 1 task runs at a time
  
- **Lambda**: Handles IoT Core messages
  - Runtime: Node.js 20.x
  - Deployed in VPC (private subnets)

### Networking
- **VPC**: 10.0.0.0/16
- **Public Subnets**: 10.0.10.0/24, 10.0.11.0/24
- **Private Subnets**: 10.0.1.0/24, 10.0.2.0/24
  - Both subnets required for RDS multi-AZ subnet group
  - ECS service configured for both but only deploys 1 task
- **NAT Gateway**: Provides internet access for private resources
- **Internet Gateway**: Provides internet access for public subnets

### Database
- **RDS PostgreSQL**: db.t3.micro, PostgreSQL 15
- **RDS Proxy**: Connection pooling for Lambda & ECS

### Storage & Secrets
- **ECR**: Stores Docker images for backend
- **Secrets Manager**: Stores RDS credentials

### IoT
- **AWS IoT Core**: MQTT broker for IoT devices
- **IoT Topic Rule**: Routes `sensors/#` messages to Lambda

## Cost Considerations (per day)

- **NAT Gateway**: ~$1.08/day (hourly charge) + data transfer
- **RDS db.t3.micro**: ~$0.37/day
- **ECS Fargate**: ~$0.29/day (256 CPU, 512 MB)
- **Lambda**: Pay per invocation (likely < $0.01/day for low volume)
- **Elastic IP**: Free while NAT Gateway is running

**Estimated Total**: ~$2-3/day for a week = **~$14-21 total**
