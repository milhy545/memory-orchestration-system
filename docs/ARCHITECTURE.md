# 🏗️ Architecture Deep Dive

## System Overview

The MCP Orchestration System implements a **service mesh architecture** with a central coordinator that provides HTTP-to-MCP protocol translation.

```mermaid
graph TD
    A[HTTP Client] -->|REST API| B[Zen Coordinator :8020]
    
    B --> C[Filesystem MCP :8001]
    B --> D[Git MCP :8002]  
    B --> E[Terminal MCP :8003]
    B --> F[Database MCP :8004]
    B --> G[Memory MCP :8005]
    B --> H[Advanced Memory :8006]
    B --> I[Qdrant Vector :8007]
    B --> J[WebM Transcriber :8008]
    B --> K[Research MCP :8011]
    
    C --> L[(PostgreSQL :5432)]
    D --> L
    E --> L
    F --> L
    G --> L
    H --> L
    J --> L
    K --> L
    
    C --> M[(Redis :6379)]
    D --> M
    E --> M
    F --> M
    G --> M
    H --> M
    J --> M
    K --> M
    
    H --> I
    I --> N[(Qdrant Storage)]
    
    style B fill:#f9d71c,stroke:#333,stroke-width:3px
    style L fill:#336791,color:#fff
    style M fill:#dc382d,color:#fff
    style I fill:#ff6b6b,color:#fff
```

## Data Flow Architecture

### Request Processing Flow

```mermaid
sequenceDiagram
    participant Client
    participant Zen as Zen Coordinator
    participant MCP as MCP Service
    participant DB as PostgreSQL
    participant Cache as Redis
    
    Client->>Zen: HTTP POST /mcp
    Zen->>Cache: Check request cache
    Cache-->>Zen: Cache miss
    Zen->>MCP: Forward MCP request
    MCP->>DB: Query/Store data
    DB-->>MCP: Response
    MCP-->>Zen: MCP response
    Zen->>Cache: Store response
    Zen-->>Client: HTTP JSON response
```

### Memory & Vector Search Flow

```mermaid
sequenceDiagram
    participant Client
    participant Zen as Zen Coordinator
    participant Memory as Memory MCP
    participant Advanced as Advanced Memory
    participant Qdrant as Qdrant Vector DB
    participant PG as PostgreSQL
    
    Client->>Zen: Store memory
    Zen->>Memory: Simple storage
    Memory->>PG: Store key-value
    Memory->>Advanced: Trigger vector indexing
    Advanced->>Qdrant: Generate embeddings
    Qdrant-->>Advanced: Store vectors
    
    Client->>Zen: Search memories
    Zen->>Advanced: Semantic search
    Advanced->>Qdrant: Vector similarity
    Qdrant-->>Advanced: Similar vectors
    Advanced->>PG: Fetch full content
    PG-->>Advanced: Content data
    Advanced-->>Zen: Search results
    Zen-->>Client: Ranked results
```

## Service Architecture Details

### Zen Coordinator (Port 8020)
- **Role**: HTTP ↔ MCP Protocol Bridge
- **Features**:
  - Request routing based on tool name
  - Protocol translation (HTTP JSON ↔ MCP)
  - Health monitoring of all services
  - Centralized logging and metrics
  - Redis-based response caching

### MCP Services Layer
Each MCP service is containerized with:
- **Shared Database**: PostgreSQL connection
- **Shared Cache**: Redis connection  
- **Individual Ports**: 8001-8011 range
- **Fault Isolation**: Container-level isolation
- **Auto-restart**: Docker Compose restart policies

### Data Persistence Layer
- **PostgreSQL**: Primary data store, ACID compliance
- **Redis**: High-speed caching, session storage
- **Qdrant**: Vector embeddings, similarity search
- **File System**: Document storage, workspace data

## Security Architecture

### Network Security
```mermaid
graph TB
    subgraph "Host Network"
        A[Client :80/443]
    end
    
    subgraph "Docker Network: mcp-network"
        B[Zen Coordinator :8020]
        C[MCP Services :8001-8011]
        D[PostgreSQL :5432]
        E[Redis :6379]
        F[Qdrant :6333]
    end
    
    A -->|Exposed| B
    B -.->|Internal| C
    C -.->|Internal| D
    C -.->|Internal| E
    C -.->|Internal| F
    
    style A fill:#ff9999
    style B fill:#ffcc99
    style C fill:#99ccff
    style D fill:#99ff99
    style E fill:#ffff99
    style F fill:#cc99ff
```

### Authentication & Authorization
- **Environment Variables**: All secrets via .env
- **Container Isolation**: Service-level boundaries
- **Database Authentication**: PostgreSQL user/password
- **API Key Management**: External service tokens
- **Network Segmentation**: Docker internal network

## Scalability Patterns

### Horizontal Scaling
```mermaid
graph TB
    A[Load Balancer] --> B[Zen Coordinator 1]
    A --> C[Zen Coordinator 2]
    A --> D[Zen Coordinator N]
    
    B --> E[Shared PostgreSQL Cluster]
    C --> E
    D --> E
    
    B --> F[Redis Cluster]
    C --> F
    D --> F
```

### Vertical Scaling
- **Resource Limits**: Docker container constraints
- **Database Scaling**: PostgreSQL connection pooling
- **Cache Optimization**: Redis memory management
- **Vector Search**: Qdrant index optimization

## Monitoring & Observability

### Health Check Architecture
```mermaid
graph LR
    A[Health Check Script] --> B{Service Status}
    B -->|Healthy| C[Log Success]
    B -->|Unhealthy| D[Alert & Restart]
    D --> E[Docker Compose Restart]
    E --> F[Service Recovery]
```

### Metrics Collection
- **Service Health**: HTTP endpoint monitoring
- **Database Performance**: PostgreSQL query metrics
- **Cache Hit Rates**: Redis performance stats
- **Vector Search**: Qdrant index statistics
- **Resource Usage**: Docker container metrics

## Development Architecture

### Testing Pyramid
```mermaid
graph TD
    A[End-to-End Tests<br/>Workflow Integration] 
    B[Integration Tests<br/>Service Communication]
    C[Unit Tests<br/>Individual Services]
    D[Performance Tests<br/>Load & Stress]
    E[Security Tests<br/>Vulnerability Assessment]
    F[Failure Tests<br/>Recovery Scenarios]
    
    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    
    style A fill:#ff6b6b
    style B fill:#4ecdc4
    style C fill:#45b7d1
    style D fill:#96ceb4
    style E fill:#feca57
    style F fill:#ff9ff3
```

### CI/CD Pipeline (Recommended)
1. **Code Commit** → Trigger pipeline
2. **Unit Tests** → Individual service testing
3. **Integration Tests** → Service communication
4. **Security Scan** → Vulnerability assessment
5. **Performance Tests** → Load benchmarking
6. **Build Images** → Docker container creation
7. **Deploy Staging** → Environment testing
8. **Production Deploy** → Blue-green deployment

This architecture ensures **scalability**, **maintainability**, and **production readiness** for enterprise deployments.