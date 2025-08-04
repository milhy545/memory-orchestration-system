# 🚨 SERVER STARTUP ANALÝZA - DATABASE PATHS

## 📍 **ZJIŠTĚNÉ DATABÁZOVÉ CESTY:**

### **🖥️ Server Memory MCP Container:**
```dockerfile
# /root/new-mcp-servers/memory-mcp/main.py
MEMORY_DATABASE = "/home/orchestrace/data/databases/unified_memory_forai.db"
```
**⚠️ PROBLÉM:** Server používá `/home/orchestrace/` místo našich cest!

### **🏠 Lokální System:**
```python
# /home/milhy777/memory-orchestration-system/data/
conversation_memory.db
cldmemory.db  
bash_tracker.db
unified_memory_forai.db
```

---

## 🔧 **STARTUP KONFLIKTY:**

### **1. Memory MCP Container Restart:**
```bash
# Server container path:
/home/orchestrace/data/databases/unified_memory_forai.db

# Naše migrace:
/home/milhy777/memory-orchestration-system/data/unified_memory_forai.db
```

### **2. Potenciální /tmp Reset:**
- Server container může defaultovat zpět na `/tmp/` paths
- Docker volume mount může být na jinou cestu
- Startup skripty moučo překrýt naše konfigurace

---

## ✅ **MEMORY STATUS - AKTUÁLNÍ KONVERZACE:**

### **🧠 Uloženo v Memory Systému:**
```json
{
  "id": 253,
  "content": "Memory Orchestration System 100% pass rate...",
  "similarity": 0.647,
  "created_at": "2025-07-22 23:44:22"
}
```

**✅ ANO - Tato konverzace JE v memory systému s vysokou podobností (64.7%)!**

---

## 🛠️ **STARTUP FIX DOPORUČENÍ:**

### **1. Server Memory MCP Update:**
```bash
# Aktualizovat server container paths
MEMORY_DATABASE = "/home/milhy777/memory-orchestration-system/data/cldmemory.db"
```

### **2. Docker Volume Mount:**
```yaml
volumes:
  - "/home/milhy777/memory-orchestration-system/data:/app/data"
```

### **3. Environment Variables:**
```bash
MEMORY_DB_PATH=/app/data/cldmemory.db
QDRANT_URL=http://localhost:8006
```

### **4. Startup Script Update:**
```bash
# Ensure persistent paths on server restart
ln -sf /home/milhy777/memory-orchestration-system/data /home/orchestrace/data
```

---

## 🎯 **AKČNÍ PLÁN:**

1. **Zkontrolovat server Docker volumes**
2. **Aktualizovat Memory MCP container paths** 
3. **Ověřit startup skripty na serveru**
4. **Testovat restart stability**
5. **Zajistit databáze persisted mimo /tmp**

**BEZ TĚCHTO OPRAV se po server restartu databáze resetují do /tmp!** ⚠️