# 🔄 CONTAINER MIGRATION TASKLIST - /ROOT → /HOME NA SERVERU

## 🎯 **STRATEGIE: POSTUPNÁ MIGRACE S TESTING**

**Princip:** Kopírovat → Test nový → Vypnout starý → Přepnout → Ověřit → Pokračovat na další

---

## 📋 **PHASE 1: PŘÍPRAVA & BACKUP**

### **TASK 1.1: Příprava cílové struktury**
```bash
# Na serveru vytvořit:
mkdir -p /home/docker-mcp-stack/{memory,database,filesystem,git,terminal,perplexity,webm-transcriber}
mkdir -p /home/docker-mcp-stack/volumes/{memory,database,git}
mkdir -p /home/docker-mcp-stack/configs
mkdir -p /home/docker-mcp-stack/logs
```

### **TASK 1.2: Kompletní backup /root**
```bash
# Backup celého /root/new-mcp-servers
tar -czf /home/docker-mcp-backup-$(date +%Y%m%d).tar.gz /root/new-mcp-servers /root/docker-compose-complete.yml
```

### **TASK 1.3: Kopie source files do /home**
```bash
# Zkopírovat všechny MCP sources:
cp -r /root/new-mcp-servers/* /home/docker-mcp-stack/
cp /root/docker-compose-complete.yml /home/docker-mcp-stack/docker-compose.yml
```

---

## 🔄 **PHASE 2: POSTUPNÁ MIGRACE (7 KONTEJNERŮ)**

### **TASK 2.1: MEMORY MCP MIGRATION**
**Priority: NEJVYŠŠÍ** (kritická komponenta)

#### **2.1.1: Příprava nového containeru**
```bash
cd /home/docker-mcp-stack/memory-mcp/
# Update main.py paths:
MEMORY_DATABASE = "/home/docker-mcp-stack/volumes/memory/unified_memory_forai.db"
```

#### **2.1.2: Copy databáze**
```bash
cp /home/orchestrace/data/databases/unified_memory_forai.db /home/docker-mcp-stack/volumes/memory/
```

#### **2.1.3: Build nový container**
```bash
docker build -t memory-mcp-home /home/docker-mcp-stack/memory-mcp/
```

#### **2.1.4: Test na jiném portu**
```bash
docker run -d --name memory-mcp-test -p 8107:8000 \
  -v /home/docker-mcp-stack/volumes/memory:/app/data \
  memory-mcp-home
```

#### **2.1.5: Ověření funkcionality**
```bash
curl http://localhost:8107/docs  # FastAPI docs
# Test API endpoints
# Verify database connection
```

#### **2.1.6: Switch production**
```bash
docker stop root-memory-mcp-1
docker rm root-memory-mcp-1
docker run -d --name memory-mcp-prod -p 8007:8000 \
  -v /home/docker-mcp-stack/volumes/memory:/app/data \
  memory-mcp-home
```

#### **2.1.7: Final validation**
```bash
# Run orchestration tests
# Verify Memory MCP in production
```

---

### **TASK 2.2: DATABASE MCP MIGRATION**
**Priority: VYSOKÁ**

#### **2.2.1: Příprava & build**
```bash
cd /home/docker-mcp-stack/database-mcp/
docker build -t database-mcp-home .
```

#### **2.2.2: Test**
```bash
docker run -d --name database-mcp-test -p 8104:8000 \
  -v /home/docker-mcp-stack/volumes/database:/data \
  database-mcp-home
curl http://localhost:8104/docs
```

#### **2.2.3: Production switch**
```bash
docker stop root-database-mcp-1 && docker rm root-database-mcp-1
docker run -d --name database-mcp-prod -p 8004:8000 \
  -v /home/docker-mcp-stack/volumes/database:/data \
  database-mcp-home
```

---

### **TASK 2.3: FILESYSTEM MCP MIGRATION**
**Priority: STŘEDNÍ** (má široké permissions)

#### **2.3.1: Příprava & build**
```bash
cd /home/docker-mcp-stack/filesystem-mcp/
# Review volume mounts před build
docker build -t filesystem-mcp-home .
```

#### **2.3.2: Test s opatrným volume mapping**
```bash
docker run -d --name filesystem-mcp-test -p 8101:8000 \
  -v /home:/home:ro \
  -v /home/docker-mcp-stack/volumes/filesystem:/tmp \
  filesystem-mcp-home
```

#### **2.3.3: Production switch**
```bash
docker stop root-filesystem-mcp-1 && docker rm root-filesystem-mcp-1
docker run -d --name filesystem-mcp-prod -p 8001:8000 \
  -v /home:/home:ro \
  -v /home/docker-mcp-stack/volumes/filesystem:/tmp \
  filesystem-mcp-home
```

---

### **TASK 2.4: GIT MCP MIGRATION**
**Priority: STŘEDNÍ**

#### **2.4.1-3: Build, Test, Switch**
```bash
cd /home/docker-mcp-stack/git-mcp/
docker build -t git-mcp-home .
# Test na 8102, pak switch na 8002
```

---

### **TASK 2.5: TERMINAL MCP MIGRATION**
**Priority: STŘEDNÍ** (privileged container)

#### **Speciální considerations:**
```bash
# Terminal MCP vyžaduje privileged mode
docker run -d --name terminal-mcp-test -p 8103:8000 \
  --privileged \
  terminal-mcp-home
```

---

### **TASK 2.6: PERPLEXITY MCP MIGRATION**
**Priority: NÍZKÁ**

#### **Environment variables:**
```bash
# Potřebuje PERPLEXITY_API_KEY
docker run -d --name perplexity-mcp-test -p 8105:8000 \
  -e PERPLEXITY_API_KEY=YOUR_PERPLEXITY_API_KEY_HERE \
  perplexity-mcp-home
```

---

### **TASK 2.7: WEBM TRANSCRIBER MIGRATION**
**Priority: NEJNIŽŠÍ**

#### **Standard migration:**
```bash
cd /home/docker-mcp-stack/webm-transcriber/
docker build -t webm-transcriber-home .
# Test na 8108, switch na 8008
```

---

## 🧪 **PHASE 3: FINAL VALIDATION**

### **TASK 3.1: Comprehensive Testing**
```bash
# Run complete orchestration tests
python3 /home/milhy777/memory-orchestration-system/test_complete_orchestration.py

# Expected: 6/6 tests PASS
```

### **TASK 3.2: Port Mapping Verification**
```bash
# Verify all services on correct ports:
8001: Filesystem MCP
8002: Git MCP  
8003: Terminal MCP
8004: Database MCP
8005: Perplexity MCP
8007: Memory MCP
8008: WebM Transcriber
8020: Zen Coordinator (native - nezměněn)
```

### **TASK 3.3: Volume & Data Integrity**
```bash
# Check database files:
ls -la /home/docker-mcp-stack/volumes/memory/
ls -la /home/docker-mcp-stack/volumes/database/

# Verify no data loss
```

---

## 🧹 **PHASE 4: CLEANUP**

### **TASK 4.1: Remove old containers**
```bash
# Cleanup old containers (pokud vše funguje)
docker image rm memory-mcp-updated root-memory-mcp root-database-mcp ...
```

### **TASK 4.2: Archive /root sources**
```bash
# Přesunout /root/new-mcp-servers do archivu
mv /root/new-mcp-servers /root/archived-mcp-servers-$(date +%Y%m%d)
```

### **TASK 4.3: Update Docker Compose**
```bash
# Create master docker-compose.yml v /home/docker-mcp-stack/
# Pro jednoduché management všech služeb
```

---

## ⚠️ **RISK MITIGATION**

### **ROLLBACK PLAN pro každý kontejner:**
```bash
# Pokud migrace selže:
1. docker stop {new-container}
2. docker rm {new-container}  
3. docker start {old-container}
4. Verify služba funguje
5. Investigate issues
```

### **MONITORING během migrace:**
```bash
# Průběžně sledovat:
docker ps                    # Container status
docker logs {container}      # Error logs
curl http://localhost:PORT   # Service availability
```

---

## 📊 **EXECUTION TIMELINE**

**FÁZE 1 (Příprava):** 30 minut
**FÁZE 2 (Migrace):** 2-3 hodiny (20-30 min per container)
**FÁZE 3 (Validation):** 30 minut  
**FÁZE 4 (Cleanup):** 15 minut

**CELKOVÁ DOBA: 3-4 hodiny s důkladným testováním** ⏱️

**ÚSPĚCH = Všech 7 MCP kontejnerů běží z /home s 100% funkčností!** 🎯