# 🖥️ SERVER 192.168.0.58 - KOMPLETNÍ MAPA PORTŮ

## 📊 **VŠECHNY AKTIVNÍ PORTY:**

### **🔧 SYSTÉMOVÉ SLUŽBY:**
| Port | Service | Process | Popis |
|------|---------|---------|-------|
| **53** | DNS | docker-proxy | AdGuard Home DNS |
| **2222** | SSH | sshd | SSH Server (custom port) |

### **🐳 DOCKER SLUŽBY:**
| Port | Service | Container | Status | Popis |
|------|---------|-----------|--------|-------|
| **6333** | ✅ **Qdrant Vector DB** | qdrant | Up 21h | **Vector Database** |
| **6334** | ✅ **Qdrant Admin** | qdrant | Up 21h | **Qdrant Management** |
| **6379** | ✅ **Redis** | redis | Up 25h | **Cache Database** |

### **🎼 MCP ORCHESTRACE:**
| Port | Service | Container | Status | Popis |
|------|---------|-----------|--------|-------|
| **8001** | ✅ **Filesystem MCP** | root-filesystem-mcp-1 | Up 25h | File operations |
| **8002** | ✅ **Git MCP** | root-git-mcp-1 | Up 25h | Git operations |
| **8003** | ✅ **Terminal MCP** | root-terminal-mcp-1 | Up 25h | Shell commands |
| **8004** | ✅ **Database MCP** | root-database-mcp-1 | Up 25h | Database operations |
| **8005** | ✅ **Perplexity MCP** | root-perplexity-mcp-1 | Up 25h | AI Research |
| **8006** | ✅ **Web-Bridge MCP** | root-web-bridge-mcp-1 | Up 25h | **Web Bridge** |
| **8007** | ✅ **Memory MCP** | root-memory-mcp-1 | Up 25h | **MEMORY SERVICE!** |
| **8008** | ✅ **WebM Transcriber** | root-webm-transcriber-mcp-1 | Up 25h | Audio processing |
| **8020** | ✅ **Zen Coordinator** | python3 (native) | Running | **Main Coordinator** |

### **🏠 HOME ASSISTANT EKOSYSTÉM:**
| Port | Service | Container | Status | Popis |
|------|---------|-----------|--------|-------|
| **10001** | ✅ **Portainer** | portainer | Up 25h | Docker management |
| **10002** | ✅ **Home Assistant** | home-assistant | Up 25h | Smart home hub |
| **10003** | ✅ **AdGuard Home** | adguard-home | Up 25h | DNS filtering |
| **19443** | ✅ **Home Assistant SSL** | home-assistant | Up 25h | HTTPS interface |

---

## 🎯 **KLÍČOVÉ POZNATKY:**

### **✅ SPRÁVNÁ KONFIGURACE:**
- **Memory service**: Port **8007** (NE 8006!) ✅
- **Qdrant Vector DB**: Port **6333** (správně) ✅
- **Web-Bridge**: Port **8006** (ne memory) ✅
- **Zen Coordinator**: Port **8020** (native Python) ✅

### **🔄 AUTO-STARTUP SYSTÉM:**
- **Docker containers**: Všechny s auto-restart policy ✅
- **Koordinátor**: Native Python proces ✅
- **Uptime**: 25+ hodin = startup funguje ✅

### **🚨 PROBLÉMY IDENTIFIKOVÁNY:**
1. **Memory MCP container**: Vrací 404 na všech endpoints ❌
2. **Lokální CLDMEMORY**: Port 8006 konflikt s Web-Bridge ❌
3. **Koordinátor tooling**: Tools definovány ale servery neodpovídají ❌

---

## 🛠️ **OPRAVANÁ KONFIGURACE:**

### **LOKÁLNÍ SYSTEM UPDATE:**
```python
# V cldmemory_simple.py nebo auto_context_retrieval.py:
CLDMEMORY_URL = "http://192.168.0.58:8007"  # NE localhost:8006!
QDRANT_URL = "http://192.168.0.58:6333"     # Server Qdrant
```

### **PORT MAPPING OPRAVA:**
```
STARÁ MAPA (špatná):
- Memory: localhost:8006 ❌
- Qdrant: localhost:6333 ❌

NOVÁ MAPA (správná):  
- Memory: 192.168.0.58:8007 ✅
- Qdrant: 192.168.0.58:6333 ✅
```

---

## 📋 **ACTION ITEMS:**

1. **Opravit lokální memory URLs** → 192.168.0.58:8007
2. **Diagnostikovat Memory MCP container** (proč 404?)
3. **Zastavit duplicitní lokální CLDMEMORY** (port 8006)
4. **Ověřit Qdrant connection** z lokálního systému

**KONEČNĚ MÁMME KOMPLETNÍ MAPU! 🎯**