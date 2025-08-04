# 🏠 DOCKER /ROOT → /HOME TRANSFER PLAN

## 📍 **IDENTIFIKOVANÉ ZDROJOVÉ SOUBORY V /ROOT:**

### **🐳 DOCKER INFRASTRUKTURA:**
```
/root/.docker/                     | Docker client config + buildx cache
/root/docker-compose-complete.yml  | Master Docker Compose (všech MCP)
/root/new-mcp-servers/              | 7x MCP source directories s Dockerfiles
```

### **🎼 MCP SOURCE DIRECTORIES:**
```
/root/new-mcp-servers/
├── memory-mcp/        | main.py + Dockerfile + requirements.txt
├── database-mcp/      | Database operations MCP
├── filesystem-mcp/    | File operations MCP  
├── git-mcp/          | Git operations MCP
├── research-mcp/     | Perplexity research MCP
├── terminal-mcp/     | Terminal commands MCP
└── webm-transcriber/ | Audio transcription MCP
```

### **🖥️ DOCKER MANAGEMENT:**
```
Portainer: Container na portu 10001 (ne binary)
Docker Images: 16 aktivních MCP images (5GB total)
Docker Daemon: Systemd service (zůstává)
```

### **📜 MANAGEMENT SCRIPTS:**
```
/root/claude-code-telegram/docker-start.sh
/root/claude-code-telegram/setup-claude-auth-docker.sh  
/root/perplexity-ha-integration/install.sh
```

---

## 🎯 **TRANSFER STRATEGIE:**

### **📦 CO TRANSFEROVAT:**

#### **✅ PRIORITY 1 - KRITICKÉ:**
```
/root/new-mcp-servers/              → /home/docker-mcp-stack/
/root/docker-compose-complete.yml   → /home/docker-mcp-stack/docker-compose.yml
/root/.docker/                     → /home/milhy777/.docker/
```

#### **✅ PRIORITY 2 - UŽITEČNÉ:**
```
Docker build scripts               → /home/docker-mcp-stack/scripts/
Management scripts                → /home/docker-mcp-stack/management/
```

#### **❌ NETRRANSFEROVAT:**
```
Docker daemon config (systemwide)
Running containers (rebuild z source)
Docker images (rebuild z Dockerfiles)
Portainer data (ponechat na serveru)
```

---

## 🔧 **IMPLEMENTAČNÍ PLÁN:**

### **KROK 1: PŘÍPRAVA CÍLOVÉ STRUKTURY**
```bash
# Na lokálním systému:
mkdir -p /home/milhy777/docker-mcp-stack/{sources,scripts,management,data}
mkdir -p /home/milhy777/docker-mcp-stack/volumes/{memory,database,git}
```

### **KROK 2: TRANSFER ZDROJOVÝCH SOUBORŮ**
```bash
# Zkopírovat MCP source:
scp -r Home-Automation-Server:/root/new-mcp-servers/* \
    /home/milhy777/docker-mcp-stack/sources/

# Zkopírovat Docker Compose:
scp Home-Automation-Server:/root/docker-compose-complete.yml \
    /home/milhy777/docker-mcp-stack/docker-compose.yml

# Zkopírovat Docker config:
scp -r Home-Automation-Server:/root/.docker/* \
    /home/milhy777/.docker/
```

### **KROK 3: ADAPTACE PRO LOKÁLNÍ PROSTŘEDÍ**
```yaml
# Upravit docker-compose.yml:
services:
  memory-mcp:
    build: ./sources/memory-mcp
    ports:
      - "8107:8000"  # Offset ports to avoid conflicts
    volumes:
      - ./volumes/memory:/app/data
    environment:
      - MEMORY_DB_PATH=/app/data/cldmemory.db
```

### **KROK 4: PATH & CONFIG UPDATES**
```python
# V memory-mcp/main.py změnit:
MEMORY_DATABASE = "/app/data/cldmemory.db"  # místo /home/orchestrace

# V ostatních MCP:
- Update volume paths na ./volumes/
- Update port mappings (8100-8110 range)
- Update environment variables
```

### **KROK 5: BUILD & TEST LOKÁLNĚ**
```bash
cd /home/milhy777/docker-mcp-stack/
docker-compose build
docker-compose up -d
docker-compose ps  # Verify all services running
```

---

## 📊 **PŘED/PO SROVNÁNÍ:**

### **🖥️ SERVER (PŘED):**
```
Lokace: /root/new-mcp-servers/
Porty: 8001-8008
Volumes: /home/orchestrace, /opt/mcp-data
Management: Ruční docker commands
```

### **🏠 LOCAL (PO):**
```
Lokace: /home/milhy777/docker-mcp-stack/
Porty: 8101-8108 (offset)
Volumes: ./volumes/ (relative)
Management: Docker Compose
```

---

## ⚡ **TRANSFER BENEFITS:**

### **✅ VÝHODY:**
- **Lokální development** - rychlejší iterace
- **Version control** - všechny změny v Gitu
- **Isolated environment** - bez konfliktů se serverem
- **Easy backup** - celý stack v jednom adresáři
- **Portainer management** - GUI pro Docker stack

### **⚠️ CONSIDERATIONS:**
- **Port conflicts** - nutno offsetovat porty
- **Data sync** - databáze musí být synchronizovány
- **Resource usage** - duplicitní kontejnery = více RAM/CPU
- **Network access** - lokální stack = lokální access only

---

## 🎯 **RECOMMENDED EXECUTION:**

### **FÁZE 1: COPY & ADAPT (1-2 hodiny)**
```
1. Copy source files z /root
2. Adapt paths a porty
3. Create local docker-compose.yml
4. Test build všech MCP services
```

### **FÁZE 2: DATA SYNC (30 minut)**
```
1. Copy databases z server volumes
2. Setup volume mappings
3. Test data persistence
```

### **FÁZE 3: INTEGRATION TEST (1 hodina)**
```
1. Start lokální MCP stack
2. Update orchestration tests
3. Verify 100% pass rate lokálně
```

**CELKOVÁ DOBA: 3-4 hodiny pro kompletní transfer** ⏱️

**Transfer je straightforward - hlavně source files + config adaptace!** 🚀