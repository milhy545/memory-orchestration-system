# 🎼 MCP Servers Orchestration - Kompletní Dokumentace

## 📋 **PŘEHLED NOVÝCH MCP SERVERŮ**

Tato orchestrace nyní obsahuje **7 specializovaných MCP serverů** + univerzální koordinátor:

### **🎯 MCP Orchestration Coordinator**
- **Soubor**: `mcp_orchestration_coordinator.py`
- **Port**: 8000 (koordinátor)
- **Účel**: Univerzální launcher a manager všech MCP serverů

### **🐙 GitHub MCP Server** 
- **Soubor**: `github_mcp_server.py`
- **Port**: 8021
- **Účel**: Kompletní integrace s GitHub API

### **🐳 Docker MCP Server**
- **Soubor**: `docker_mcp_server.py` 
- **Port**: 8022
- **Účel**: Správa Docker kontejnerů a images

### **💾 Database MCP Server**
- **Soubor**: `database_mcp_server.py`
- **Port**: 8023
- **Účel**: PostgreSQL, MySQL, SQLite operace

### **📁 Enhanced File MCP Server**
- **Soubor**: `enhanced_file_mcp_server.py`
- **Port**: 8024
- **Účel**: Pokročilé operace se soubory

### **📧 Gmail MCP Server** (David Strejc)
- **Soubor**: `gmail_mcp_server/src/email_client/server.py`
- **Port**: 8025
- **Účel**: Gmail integrace

### **🌐 Browser MCP Server**
- **Soubor**: `browser_mcp_server.py`
- **Port**: 8026
- **Účel**: Web browser automation, testing, scraping

### **🧠 Zen Coordinator** (David Strejc - Updated)
- **Soubor**: `zen_coordinator_updated.py`
- **Port**: 8020
- **Účel**: Hlavní AI tools koordinátor

---

## 🚀 **RYCHLÝ START**

### **1. Spuštění Koordinátora**
```bash
# Spustit hlavní koordinátor
python3 /home/milhy777/memory-orchestration-system/mcp_orchestration_coordinator.py
```

### **2. Spuštění Jednotlivých Serverů**
```bash
# GitHub MCP Server
python3 /home/milhy777/memory-orchestration-system/github_mcp_server.py

# Docker MCP Server  
python3 /home/milhy777/memory-orchestration-system/docker_mcp_server.py

# Database MCP Server
python3 /home/milhy777/memory-orchestration-system/database_mcp_server.py

# Enhanced File MCP Server
python3 /home/milhy777/memory-orchestration-system/enhanced_file_mcp_server.py

# Browser MCP Server
python3 /home/milhy777/memory-orchestration-system/browser_mcp_server.py
```

---

## 🛠️ **DETAILNÍ NÁSTROJE PODLE SERVERŮ**

### **🌐 Browser MCP Server Tools:**
- `browser_start` - Spuštění prohlížeče
- `browser_stop` - Zastavení prohlížeče
- `browser_navigate` - Navigace na URL
- `browser_click` - Klik na element
- `browser_type` - Psaní textu
- `browser_get_text` - Získání textu z elementu
- `browser_screenshot` - Screenshot stránky/elementu
- `browser_scroll` - Scrollování stránky
- `browser_execute_js` - Spuštění JavaScript
- `browser_wait_for_element` - Čekání na element
- `browser_hover` - Hover nad elementem
- `browser_drag_and_drop` - Drag & drop
- `browser_get_cookies` - Získání cookies
- `browser_set_cookie` - Nastavení cookie
- `browser_get_page_info` - Info o stránce
- `browser_get_page_source` - HTML source
- `browser_back` / `browser_forward` - Navigace v historii
- `browser_refresh` - Obnovení stránky
- `browser_wait_and_pause` - Pauza

**Příklad použití:**
```json
{
  "tool": "browser_start",
  "arguments": {
    "browser": "chrome",
    "headless": false,
    "window_size": "1920,1080",
    "user_data_dir": "/tmp/chrome_profile"
  }
}
```

**Automatizace workflow:**
```json
{
  "tool": "browser_navigate",
  "arguments": {
    "url": "https://github.com/login"
  }
}
```

### **🐙 GitHub MCP Server Tools:**
- `github_list_repos` - Seznam repositories
- `github_get_repo_info` - Detaily repository
- `github_list_issues` - Seznam issues
- `github_create_issue` - Vytvoření issue
- `github_list_commits` - Historie commitů
- `github_get_file_content` - Obsah souboru
- `github_list_pull_requests` - Seznam PR
- `github_search_code` - Vyhledávání kódu

**Příklad použití:**
```json
{
  "tool": "github_list_repos",
  "arguments": {
    "username": "david-strejc",
    "type": "public",
    "sort": "updated"
  }
}
```

### **🐳 Docker MCP Server Tools:**
- `docker_list_containers` - Seznam kontejnerů
- `docker_start_container` - Spuštění kontejneru
- `docker_stop_container` - Zastavení kontejneru
- `docker_create_container` - Vytvoření kontejneru
- `docker_execute_command` - Příkaz v kontejneru
- `docker_list_images` - Seznam images
- `docker_system_info` - Systémové info
- `docker_system_prune` - Vyčištění systému

**Příklad použití:**
```json
{
  "tool": "docker_list_containers",
  "arguments": {
    "all": true
  }
}
```

### **💾 Database MCP Server Tools:**
- `db_connect` - Připojení k databázi
- `db_execute_query` - Spuštění SQL dotazu
- `db_get_tables` - Seznam tabulek
- `db_get_table_schema` - Schema tabulky
- `db_backup_table` - Záloha tabulky
- `db_database_stats` - Statistiky databáze

**Příklad použití:**
```json
{
  "tool": "db_connect",
  "arguments": {
    "connection_name": "main_db",
    "db_type": "postgresql",
    "host": "localhost",
    "database": "myapp",
    "username": "user",
    "password": "pass"
  }
}
```

### **📁 Enhanced File MCP Server Tools:**
- `file_analyze` - Analýza souboru (hash, metadata)
- `directory_scan` - Rekurzivní scan adresáře
- `file_compress` - Komprese souborů (zip, tar.gz)
- `file_extract` - Extrakce archivů
- `file_encrypt` - Šifrování souborů
- `file_decrypt` - Dešifrování souborů
- `file_duplicate_finder` - Hledání duplicit
- `file_sync` - Synchronizace adresářů
- `file_permissions_batch` - Hromadné změny oprávnění

**Příklad použití:**
```json
{
  "tool": "file_analyze", 
  "arguments": {
    "file_path": "/home/user/document.pdf",
    "include_hash": true,
    "include_content_preview": false
  }
}
```

---

## 🎼 **KOORDINÁTOR - MANAGEMENT TOOLS**

### **Koordinační nástroje:**
- `mcp_list_servers` - Seznam všech serverů
- `mcp_start_server` - Spuštění serveru
- `mcp_stop_server` - Zastavení serveru
- `mcp_restart_server` - Restart serveru
- `mcp_start_all` - Spuštění všech
- `mcp_stop_all` - Zastavení všech
- `mcp_system_status` - Celkový stav systému
- `mcp_health_check` - Health check všech služeb

**Příklad usage:**
```json
{
  "tool": "mcp_start_server",
  "arguments": {
    "server_name": "github"
  }
}
```

---

## ⚙️ **KONFIGURACE A ZÁVISLOSTI**

### **Požadované knihovny:**
```bash
# GitHub MCP Server
pip install requests

# Docker MCP Server  
pip install docker

# Database MCP Server
pip install psycopg2-binary mysql-connector-python

# Enhanced File MCP Server
pip install cryptography watchdog

# Gmail MCP Server (již nainstalováno)
# Zen Coordinator (již nainstalován)
```

### **Environment Variables:**
```bash
# GitHub
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"

# Docker
# (používá Docker daemon - žádná konfigurace není potřeba)

# Database
export DB_HOST="localhost"
export DB_USER="username" 
export DB_PASS="password"
```

---

## 🔥 **POKROČILÉ POUŽITÍ**

### **1. Automatizace GitHub Workflow:**
```bash
# Vytvoření issue pro bug
python3 -c "
import json, requests
data = {
  'tool': 'github_create_issue',
  'arguments': {
    'owner': 'myuser',
    'repo': 'myrepo', 
    'title': 'Auto-generated bug report',
    'body': 'Found via automated testing'
  }
}
requests.post('http://localhost:8021', json=data)
"
```

### **2. Docker Container Orchestration:**
```bash
# Spuštění development prostředí
python3 -c "
import json, requests
containers = ['redis', 'postgres', 'app']
for container in containers:
    data = {'tool': 'docker_start_container', 'arguments': {'container_id': container}}
    requests.post('http://localhost:8022', json=data)
"
```

### **3. Database Monitoring:**
```bash
# Automatická záloha všech tabulek
python3 -c "
import json, requests
# Connect to DB
connect_data = {
  'tool': 'db_connect',
  'arguments': {
    'connection_name': 'backup_conn',
    'db_type': 'postgresql',
    'host': 'localhost',
    'database': 'production'
  }
}
requests.post('http://localhost:8023', json=connect_data)

# Get tables and backup each
tables_data = {'tool': 'db_get_tables', 'arguments': {'connection_name': 'backup_conn'}}
response = requests.post('http://localhost:8023', json=tables_data)
# Process tables and create backups...
"
```

---

## 🎯 **INTEGRACE S BROWSER MCP**

Pro kompletní automatizaci webového testování kombinuj s **Browser MCP**:

```bash
# Install Browser MCP
npm install -g @browser-mcp/server

# Kombinované použití:
# 1. Browser MCP - otevře GitHub stránku
# 2. GitHub MCP - analyzuje repository data  
# 3. Enhanced File MCP - uloží výsledky do souboru
# 4. Docker MCP - spustí test kontejnery
```

---

## 📊 **MONITORING A LOGGING**

### **Health Check Endpoint:**
```bash
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{"tool": "mcp_health_check", "arguments": {}}'
```

### **System Status Dashboard:**
```bash
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{"tool": "mcp_system_status", "arguments": {}}'
```

---

## 🚨 **TROUBLESHOOTING**

### **Časté problémy:**

1. **Port conflicts:**
   ```bash
   lsof -i :8020-8025  # Check port usage
   ```

2. **Permission errors:**
   ```bash
   chmod +x *.py
   ```

3. **Missing dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Docker daemon not running:**
   ```bash
   sudo systemctl start docker
   ```

---

## 🎉 **VÝSLEDEK**

Máš nyní kompletní **MCP Servers Orchestration** s:

✅ **7 specializovaných MCP serverů**  
✅ **Univerzální koordinátor**  
✅ **70+ nástrojů celkem**  
✅ **Kompletní dokumentaci**  
✅ **GitHub, Docker, Database, File, Browser integrace**  
✅ **Automatizované spouštění a monitoring**

**Systém je připraven pro produkční nasazení!** 🚀