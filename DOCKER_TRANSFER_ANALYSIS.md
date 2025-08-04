# 🐳 DOCKER TRANSFER ANALYSIS - KOMPLETNÍ PŘEHLED

## 📊 **AKTUÁLNÍ DOCKER ECOSYSTEM NA SERVERU:**

### **🏃‍♂️ BĚŽÍCÍ KONTEJNERY (12):**

#### **🎼 MCP ORCHESTRACE:**
```
root-memory-mcp-1          | memory-mcp-updated         | /home/orchestrace, /tmp
root-webm-transcriber-mcp-1| root-webm-transcriber-mcp | /tmp
root-filesystem-mcp-1      | root-filesystem-mcp       | /home, /tmp, /opt/mcp-data  
root-git-mcp-1             | root-git-mcp               | /opt/mcp-data
root-perplexity-mcp-1      | root-perplexity-mcp        | (no volumes)
root-terminal-mcp-1        | root-terminal-mcp          | (no volumes)
root-database-mcp-1        | root-database-mcp          | /opt/mcp-data
```

#### **🗄️ DATABÁZE & CACHE:**
```
redis                      | redis:7-alpine             | anonymous volume
qdrant                     | qdrant/qdrant             | qdrant_storage (named)
```

#### **🏠 HOME ASSISTANT STACK:**
```
portainer                  | portainer-ce:2.27.9        | portainer_data, /var/run/docker
homeassistant              | home-assistant:stable      | /opt/homeassistant  
adguardhome                | adguard/adguardhome       | /opt/adguard/work, /opt/adguard/conf
```

---

## 📁 **VOLUME & MOUNT MAPPING:**

### **🎯 KRITICKÉ NÁLEZY:**

#### **1. Memory MCP - PROBLÉMOVÉ MOUNTY:**
```json
{
  "Source": "/home/orchestrace",
  "Destination": "/home/orchestrace", 
  "Problem": "Bind mount na server-specific path!"
}
{
  "Source": "/tmp",
  "Destination": "/tmp",
  "Problem": "Dočasná data - ztráta po restartu!"
}
```

#### **2. Filesystem MCP - ŠIROKÝ PŘÍSTUP:**
```json
{
  "Mounts": "/home, /tmp, /opt/mcp-data",
  "Problem": "Přístup k celému /home - security risk!"
}
```

#### **3. Named Volumes:**
```
qdrant_storage     | Qdrant vector database (KRITICKÉ!)
portainer_data     | Portainer konfigurace
```

#### **4. Data Directories:**
```
/home/orchestrace/data/databases/
├── cldmemory.db (2.1MB)
└── unified_memory_forai.db (196KB)

/opt/mcp-data/          | MCP shared data (prázdné)
/opt/homeassistant/     | Home Assistant config
/opt/adguard/           | AdGuard config
```

---

## 🎯 **TRANSFER KOMPLEXITA ANALÝZA:**

### **⚠️ VYSOKÁ KOMPLEXITA:**

#### **1. Path Dependencies:**
- **Memory MCP**: Hardcoded `/home/orchestrace` paths v kódu
- **Filesystem MCP**: Bind mounts na system paths  
- **Databáze**: Server-specific lokace

#### **2. Network Dependencies:**
```
perplexity-ha-control_default    | LiteLLM komunikace
perplexity-ha-control_perplexity-ha | Internal networking
root_default                     | MCP inter-service communication
```

#### **3. Service Interdependencies:**
```
Zen Coordinator (8020) → Memory MCP (8007) → Orchestrace DB
                      → Qdrant (8006) → qdrant_storage
                      → Other MCPs → /opt/mcp-data
```

#### **4. Startup Orchestration:**
- Žádné Docker Compose files pro MCP stack
- Containers spouštěné manuálně nebo scriptem
- Dependency chain pro port binding

---

## 🛠️ **TRANSFER STRATEGIE - 4 MOŽNOSTI:**

### **🎯 OPTION 1: FULL DOCKER MIGRATION**
**Komplexita: VELMI VYSOKÁ** 🔴
```
Kroky:
1. Export všech volumes (docker volume backup)
2. Export všech images (docker save)
3. Export containers configs (docker inspect)
4. Rekonstrukce na novém serveru
5. Update všech bind mount paths
6. Rekonfigurace networking
7. Update database paths v MCP source kódu

Čas: 4-8 hodin
Riziko: VYSOKÉ (downtime, data loss možný)
```

### **🎯 OPTION 2: SELECTIVE MIGRATION**
**Komplexita: STŘEDNÍ** 🟡
```
Kroky:
1. Migrovat jen kritické volumes (qdrant_storage, databases)
2. Rebuild MCP containers na novém místě
3. Zachovat Home Assistant stack na serveru
4. Update jen Memory/Qdrant connection strings

Čas: 2-4 hodiny  
Riziko: STŘEDNÍ (částečná funkcionalita během migrace)
```

### **🎯 OPTION 3: HYBRID APPROACH**
**Komplexita: NÍZKÁ** 🟢
```
Kroky:
1. Zachovat server Docker stack jak je
2. Spustit nový lokální Docker stack 
3. Sync databáze přes rsync/scp
4. Redirect jen potřebné services lokálně

Čas: 1-2 hodiny
Riziko: NÍZKÉ (server zůstává funkční)
```

### **🎯 OPTION 4: DATABASE-ONLY SYNC**
**Komplexita: MINIMÁLNÍ** 🟢  
```
Kroky:
1. Pravidelná synchronizace jen databází
2. Zachovat veškerou Docker infrastrukturu na serveru
3. Lokální development s kopií dat

Čas: 30 minut setup + cron job
Riziko: MINIMÁLNÍ (pouze data sync)
```

---

## ⚡ **DOPORUČENÁ STRATEGIE:**

### **🎯 HYBRID APPROACH (Option 3) - NEJLEPŠÍ VOLBA**

**Důvody:**
- ✅ **Minimální riziko** - server zůstává funkční
- ✅ **Rychlá implementace** - 1-2 hodiny max
- ✅ **Flexibilní** - lze postupně přenášet services
- ✅ **Rollback friendly** - snadný návrat k původnímu stavu

**Implementation Plan:**
```
1. Setup lokální Docker Compose
2. Volume sync script pro kritická data
3. Port mapping update pro lokální development
4. Graduální service migration dle potřeby
```

---

## 📋 **NEXT STEPS:**

1. **Rozhodnout strategii** (doporučuji Option 3)
2. **Vytvořit Docker Compose** pro lokální stack
3. **Implementovat data sync** mechanismus  
4. **Testovat lokální funkcionalität**
5. **Postupná migrace** dle potřeby

**TRANSFER JE MOŽNÝ, ALE VYŽADUJE PEČLIVÉ PLÁNOVÁNÍ!** 🎯