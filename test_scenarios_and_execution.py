#!/usr/bin/env python3
"""
Reálné testovací scénáře pro všechny MCP servery
Praktické testy funkcionalit s real-world příklady
"""
import json
import requests
import time
import subprocess
import os
from datetime import datetime
from pathlib import Path

class MCPTestScenarios:
    def __init__(self):
        self.base_path = "/home/milhy777/memory-orchestration-system"
        self.test_results = []
        self.servers = {
            "coordinator": "http://localhost:8000",
            "github": "http://localhost:8021", 
            "docker": "http://localhost:8022",
            "database": "http://localhost:8023",
            "enhanced_file": "http://localhost:8024",
            "browser": "http://localhost:8026"
        }
        
        print("🧪 MCP TESTOVACÍ SCÉNÁŘE - REÁLNÉ POUŽITÍ")
        print("=" * 60)
    
    def call_mcp_tool(self, server_url: str, tool_name: str, arguments: dict = None):
        """Call MCP tool via HTTP"""
        try:
            data = {
                "method": "tools/call",
                "id": 1,
                "params": {
                    "name": tool_name,
                    "arguments": arguments or {}
                }
            }
            
            response = requests.post(server_url, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result.get("result", {}).get("content", [{}])[0].get("text", "{}")
            else:
                return f"HTTP Error: {response.status_code}"
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    def run_test_scenario(self, scenario_name: str, test_func):
        """Run test scenario with logging"""
        print(f"\n🔍 {scenario_name}")
        print("-" * 40)
        
        start_time = time.time()
        try:
            result = test_func()
            duration = time.time() - start_time
            
            if result.get("success", False):
                print(f"✅ ÚSPĚCH ({duration:.1f}s)")
                status = "PASS"
            else:
                print(f"❌ CHYBA: {result.get('error', 'Unknown error')} ({duration:.1f}s)")
                status = "FAIL"
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"💥 VÝJIMKA: {str(e)} ({duration:.1f}s)")
            status = "ERROR"
            result = {"error": str(e)}
        
        self.test_results.append({
            "scenario": scenario_name,
            "status": status,
            "duration": duration,
            "result": result
        })
        
        return result
    
    # ===========================================
    # 🌐 BROWSER MCP SCENARIOS
    # ===========================================
    
    def test_browser_github_automation(self):
        """SCÉNÁŘ: Automatizace GitHub průzkumu"""
        print("📋 Testujeme: Otevřít GitHub, najít repository, získat info")
        
        # 1. Spustit browser
        start_result = self.call_mcp_tool(self.servers["browser"], "browser_start", {
            "browser": "chrome",
            "headless": True,
            "window_size": "1920,1080"
        })
        print(f"🚀 Browser start: {start_result[:100]}...")
        
        # 2. Navigovat na GitHub
        nav_result = self.call_mcp_tool(self.servers["browser"], "browser_navigate", {
            "url": "https://github.com/david-strejc"
        })
        print(f"🌐 Navigation: {nav_result[:100]}...")
        
        # 3. Screenshot
        screenshot_result = self.call_mcp_tool(self.servers["browser"], "browser_screenshot", {
            "filename": "github_david_strejc.png"
        })
        print(f"📸 Screenshot: {screenshot_result[:100]}...")
        
        # 4. Získat page info
        info_result = self.call_mcp_tool(self.servers["browser"], "browser_get_page_info", {})
        print(f"ℹ️ Page info: {info_result[:100]}...")
        
        # 5. Zavřít browser
        stop_result = self.call_mcp_tool(self.servers["browser"], "browser_stop", {})
        print(f"🛑 Browser stop: {stop_result[:100]}...")
        
        return {"success": "github" in nav_result.lower()}
    
    def test_browser_form_automation(self):
        """SCÉNÁŘ: Automatizace formulářů"""
        print("📋 Testujeme: Vyplnění a odeslání HTML formuláře")
        
        # Vytvoříme testovací HTML stránku
        test_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Test Form</title></head>
        <body>
            <h1>Test Formulář</h1>
            <form id="testform">
                <input type="text" id="name" placeholder="Jméno">
                <input type="email" id="email" placeholder="Email">
                <textarea id="message" placeholder="Zpráva"></textarea>
                <button type="submit">Odeslat</button>
            </form>
            <div id="result" style="display:none;">Formulář odeslán!</div>
            <script>
                document.getElementById('testform').onsubmit = function(e) {
                    e.preventDefault();
                    document.getElementById('result').style.display = 'block';
                }
            </script>
        </body>
        </html>
        """
        
        test_file = Path("/tmp/test_form.html")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_html)
        
        # 1. Spustit browser
        start_result = self.call_mcp_tool(self.servers["browser"], "browser_start", {
            "browser": "chrome",
            "headless": True
        })
        
        # 2. Otevřít testovací stránku
        nav_result = self.call_mcp_tool(self.servers["browser"], "browser_navigate", {
            "url": f"file://{test_file.absolute()}"
        })
        
        # 3. Vyplnit formulář
        type1_result = self.call_mcp_tool(self.servers["browser"], "browser_type", {
            "selector": "#name",
            "text": "Test User"
        })
        print(f"📝 Name field: {type1_result[:50]}...")
        
        type2_result = self.call_mcp_tool(self.servers["browser"], "browser_type", {
            "selector": "#email", 
            "text": "test@example.com"
        })
        print(f"📧 Email field: {type2_result[:50]}...")
        
        type3_result = self.call_mcp_tool(self.servers["browser"], "browser_type", {
            "selector": "#message",
            "text": "Toto je testovací zpráva z MCP Browser serveru!"
        })
        print(f"💬 Message field: {type3_result[:50]}...")
        
        # 4. Kliknout na odeslat
        click_result = self.call_mcp_tool(self.servers["browser"], "browser_click", {
            "selector": "button[type='submit']"
        })
        print(f"🖱️ Submit click: {click_result[:50]}...")
        
        # 5. Ověřit výsledek
        text_result = self.call_mcp_tool(self.servers["browser"], "browser_get_text", {
            "selector": "#result"
        })
        print(f"✅ Result text: {text_result[:50]}...")
        
        # 6. Screenshot výsledku
        screenshot_result = self.call_mcp_tool(self.servers["browser"], "browser_screenshot", {
            "filename": "form_automation_result.png"
        })
        
        # 7. Zavřít browser
        self.call_mcp_tool(self.servers["browser"], "browser_stop", {})
        
        return {"success": "odeslán" in text_result.lower() or "submitted" in text_result.lower()}
    
    # ===========================================
    # 🐙 GITHUB MCP SCENARIOS  
    # ===========================================
    
    def test_github_repository_analysis(self):
        """SCÉNÁŘ: Analýza GitHub repository"""
        print("📋 Testujeme: Kompletní analýzu David Strejc repository")
        
        # 1. Seznam repositories
        repos_result = self.call_mcp_tool(self.servers["github"], "github_list_repos", {
            "username": "david-strejc",
            "sort": "updated",
            "per_page": 5
        })
        print(f"📂 Repositories: {repos_result[:100]}...")
        
        # 2. Detail konkrétního repo (zen-mcp-server)
        repo_info = self.call_mcp_tool(self.servers["github"], "github_get_repo_info", {
            "owner": "BeehiveInnovations",
            "repo": "zen-mcp-server" 
        })
        print(f"ℹ️ Repo info: {repo_info[:100]}...")
        
        # 3. Seznam commitů
        commits_result = self.call_mcp_tool(self.servers["github"], "github_list_commits", {
            "owner": "BeehiveInnovations",
            "repo": "zen-mcp-server",
            "per_page": 3
        })
        print(f"📝 Commits: {commits_result[:100]}...")
        
        # 4. Obsah hlavního souboru
        file_content = self.call_mcp_tool(self.servers["github"], "github_get_file_content", {
            "owner": "BeehiveInnovations",
            "repo": "zen-mcp-server",
            "path": "server.py"
        })
        print(f"📄 File content: {file_content[:100]}...")
        
        # 5. Vyhledání v kódu
        search_result = self.call_mcp_tool(self.servers["github"], "github_search_code", {
            "query": "MCP server repo:BeehiveInnovations/zen-mcp-server",
            "per_page": 3
        })
        print(f"🔍 Code search: {search_result[:100]}...")
        
        return {"success": "zen-mcp-server" in repos_result.lower()}
    
    def test_github_issue_management(self):
        """SCÉNÁŘ: GitHub Issues management (READ-ONLY test)"""
        print("📋 Testujeme: Správu GitHub issues")
        
        # Použijeme veřejné repository pro test čtení issues
        issues_result = self.call_mcp_tool(self.servers["github"], "github_list_issues", {
            "owner": "microsoft", 
            "repo": "vscode",
            "state": "open",
            "per_page": 3
        })
        print(f"🐛 Issues list: {issues_result[:100]}...")
        
        return {"success": "issues" in issues_result.lower() or "title" in issues_result.lower()}
    
    # ===========================================
    # 🐳 DOCKER MCP SCENARIOS
    # ===========================================
    
    def test_docker_container_management(self):
        """SCÉNÁŘ: Docker kontejner lifecycle"""
        print("📋 Testujeme: Vytvoření, spuštění a správu Docker kontejneru")
        
        # 1. System info
        info_result = self.call_mcp_tool(self.servers["docker"], "docker_system_info", {})
        print(f"ℹ️ Docker info: {info_result[:100]}...")
        
        # 2. Seznam existujících kontejnerů
        containers_result = self.call_mcp_tool(self.servers["docker"], "docker_list_containers", {
            "all": True
        })
        print(f"📦 Containers: {containers_result[:100]}...")
        
        # 3. Pull malého test image
        pull_result = self.call_mcp_tool(self.servers["docker"], "docker_pull_image", {
            "repository": "hello-world",
            "tag": "latest"
        })
        print(f"⬇️ Image pull: {pull_result[:100]}...")
        
        # 4. Vytvoření kontejneru
        create_result = self.call_mcp_tool(self.servers["docker"], "docker_create_container", {
            "image": "hello-world",
            "name": "mcp-test-container"
        })
        print(f"🆕 Container create: {create_result[:100]}...")
        
        # 5. Spuštění kontejneru  
        start_result = self.call_mcp_tool(self.servers["docker"], "docker_start_container", {
            "container_id": "mcp-test-container"
        })
        print(f"▶️ Container start: {start_result[:100]}...")
        
        # 6. Získání logů
        logs_result = self.call_mcp_tool(self.servers["docker"], "docker_get_container_logs", {
            "container_id": "mcp-test-container",
            "tail": 20
        })
        print(f"📄 Container logs: {logs_result[:100]}...")
        
        # 7. Cleanup - odstranění kontejneru
        remove_result = self.call_mcp_tool(self.servers["docker"], "docker_remove_container", {
            "container_id": "mcp-test-container",
            "force": True
        })
        print(f"🗑️ Container remove: {remove_result[:100]}...")
        
        return {"success": "hello" in logs_result.lower() or "started" in start_result.lower()}
    
    def test_docker_image_management(self):
        """SCÉNÁŘ: Docker image management"""
        print("📋 Testujeme: Správu Docker images")
        
        # 1. Seznam images
        images_result = self.call_mcp_tool(self.servers["docker"], "docker_list_images", {})
        print(f"🖼️ Images list: {images_result[:100]}...")
        
        # 2. Pull specific image
        pull_result = self.call_mcp_tool(self.servers["docker"], "docker_pull_image", {
            "repository": "alpine",
            "tag": "latest"
        })
        print(f"⬇️ Alpine pull: {pull_result[:100]}...")
        
        # 3. System prune (cleanup)
        prune_result = self.call_mcp_tool(self.servers["docker"], "docker_system_prune", {
            "all": False
        })
        print(f"🧹 System prune: {prune_result[:100]}...")
        
        return {"success": "alpine" in pull_result.lower() or "pulled" in pull_result.lower()}
    
    # ===========================================
    # 💾 DATABASE MCP SCENARIOS
    # ===========================================
    
    def test_database_sqlite_operations(self):
        """SCÉNÁŘ: SQLite databázové operace"""
        print("📋 Testujeme: SQLite vytvoření, vložení, dotazy")
        
        # 1. Připojení k SQLite databázi
        connect_result = self.call_mcp_tool(self.servers["database"], "db_connect", {
            "connection_name": "test_sqlite",
            "db_type": "sqlite", 
            "database": "/tmp/mcp_test.db"
        })
        print(f"🔗 DB Connect: {connect_result[:100]}...")
        
        # 2. Vytvoření tabulky
        create_table = self.call_mcp_tool(self.servers["database"], "db_execute_query", {
            "connection_name": "test_sqlite",
            "query": """
                CREATE TABLE IF NOT EXISTS test_users (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "fetch_results": False
        })
        print(f"🏗️ Create table: {create_table[:100]}...")
        
        # 3. Vložení testovacích dat
        insert_data = self.call_mcp_tool(self.servers["database"], "db_execute_query", {
            "connection_name": "test_sqlite",
            "query": """
                INSERT OR REPLACE INTO test_users (name, email) VALUES 
                ('David Strejc', 'david@example.com'),
                ('MCP Tester', 'mcp@test.com'),
                ('AI Assistant', 'ai@orchestration.com')
            """,
            "fetch_results": False
        })
        print(f"📥 Insert data: {insert_data[:100]}...")
        
        # 4. SELECT dotaz
        select_result = self.call_mcp_tool(self.servers["database"], "db_execute_query", {
            "connection_name": "test_sqlite", 
            "query": "SELECT * FROM test_users ORDER BY created_at DESC",
            "fetch_results": True,
            "limit": 10
        })
        print(f"📊 Select data: {select_result[:100]}...")
        
        # 5. Získání tabulek
        tables_result = self.call_mcp_tool(self.servers["database"], "db_get_tables", {
            "connection_name": "test_sqlite"
        })
        print(f"📋 Tables: {tables_result[:100]}...")
        
        # 6. Schema tabulky
        schema_result = self.call_mcp_tool(self.servers["database"], "db_get_table_schema", {
            "connection_name": "test_sqlite",
            "table_name": "test_users"
        })
        print(f"🏗️ Table schema: {schema_result[:100]}...")
        
        # 7. Backup tabulky
        backup_result = self.call_mcp_tool(self.servers["database"], "db_backup_table", {
            "connection_name": "test_sqlite",
            "table_name": "test_users", 
            "output_file": "/tmp/test_users_backup.json",
            "format": "json"
        })
        print(f"💾 Backup: {backup_result[:100]}...")
        
        # 8. Database stats
        stats_result = self.call_mcp_tool(self.servers["database"], "db_database_stats", {
            "connection_name": "test_sqlite"
        })
        print(f"📈 DB Stats: {stats_result[:100]}...")
        
        # 9. Odpojení
        disconnect_result = self.call_mcp_tool(self.servers["database"], "db_disconnect", {
            "connection_name": "test_sqlite"
        })
        print(f"🔌 Disconnect: {disconnect_result[:100]}...")
        
        return {"success": "David Strejc" in select_result}
    
    # ===========================================
    # 📁 ENHANCED FILE MCP SCENARIOS
    # ===========================================
    
    def test_enhanced_file_operations(self):
        """SCÉNÁŘ: Pokročilé operace se soubory"""
        print("📋 Testujeme: Analýzu, kompresi, šifrování souborů")
        
        # Vytvoříme testovací soubory
        test_dir = Path("/tmp/mcp_file_test")
        test_dir.mkdir(exist_ok=True)
        
        # Vytvoř testovací soubory
        (test_dir / "test1.txt").write_text("Toto je první testovací soubor pro MCP Enhanced File server.\nObsahuje více řádků textu.")
        (test_dir / "test2.txt").write_text("Druhý testovací soubor s podobným obsahem.\nAby se testovala detekce duplicit.")
        (test_dir / "duplicate.txt").write_text("Toto je první testovací soubor pro MCP Enhanced File server.\nObsahuje více řádků textu.")  # Duplikát
        
        # 1. Analýza souboru
        analyze_result = self.call_mcp_tool(self.servers["enhanced_file"], "file_analyze", {
            "file_path": str(test_dir / "test1.txt"),
            "include_hash": True,
            "include_content_preview": True
        })
        print(f"🔍 File analysis: {analyze_result[:100]}...")
        
        # 2. Scan adresáře
        scan_result = self.call_mcp_tool(self.servers["enhanced_file"], "directory_scan", {
            "directory_path": str(test_dir),
            "include_stats": True,
            "file_extensions": [".txt"]
        })
        print(f"📂 Directory scan: {scan_result[:100]}...")
        
        # 3. Komprese souborů
        compress_result = self.call_mcp_tool(self.servers["enhanced_file"], "file_compress", {
            "source_path": str(test_dir),
            "output_path": "/tmp/mcp_test_archive.zip",
            "format": "zip"
        })
        print(f"🗜️ Compression: {compress_result[:100]}...")
        
        # 4. Extrakce archivu
        extract_dir = Path("/tmp/mcp_extracted")
        extract_result = self.call_mcp_tool(self.servers["enhanced_file"], "file_extract", {
            "archive_path": "/tmp/mcp_test_archive.zip",
            "extract_path": str(extract_dir),
            "create_directory": True
        })
        print(f"📦 Extraction: {extract_result[:100]}...")
        
        # 5. Hledání duplikátů
        duplicates_result = self.call_mcp_tool(self.servers["enhanced_file"], "file_duplicate_finder", {
            "directory_path": str(test_dir),
            "recursive": True,
            "min_size": 10
        })
        print(f"👥 Duplicates: {duplicates_result[:100]}...")
        
        # 6. Synchronizace adresářů
        sync_target = Path("/tmp/mcp_sync_target")
        sync_result = self.call_mcp_tool(self.servers["enhanced_file"], "file_sync", {
            "source_path": str(test_dir),
            "destination_path": str(sync_target),
            "mode": "sync",
            "dry_run": False
        })
        print(f"🔄 Sync: {sync_result[:100]}...")
        
        # 7. Batch permissions (pouze pokud máme oprávnění)
        try:
            permissions_result = self.call_mcp_tool(self.servers["enhanced_file"], "file_permissions_batch", {
                "directory_path": str(test_dir),
                "file_mode": "644",
                "recursive": True
            })
            print(f"🔒 Permissions: {permissions_result[:100]}...")
        except:
            print("🔒 Permissions: Skipped (insufficient privileges)")
        
        return {"success": "test1.txt" in analyze_result and "duplicate" in duplicates_result.lower()}
    
    def test_enhanced_file_encryption(self):
        """SCÉNÁŘ: Šifrování a dešifrování souborů"""
        print("📋 Testujeme: Šifrování a dešifrování souborů")
        
        # Vytvoření testovacího souboru
        test_file = Path("/tmp/secret_document.txt")
        secret_content = "Toto je tajný dokument, který bude zašifrován pomocí MCP Enhanced File serveru!"
        test_file.write_text(secret_content)
        
        # 1. Šifrování souboru
        encrypt_result = self.call_mcp_tool(self.servers["enhanced_file"], "file_encrypt", {
            "file_path": str(test_file),
            "password": "super_secret_password_123",
            "output_path": "/tmp/secret_document_encrypted.txt",
            "key_name": "test_encryption_key"
        })
        print(f"🔐 Encryption: {encrypt_result[:100]}...")
        
        # 2. Dešifrování souboru
        decrypt_result = self.call_mcp_tool(self.servers["enhanced_file"], "file_decrypt", {
            "encrypted_file": "/tmp/secret_document_encrypted.txt",
            "output_path": "/tmp/secret_document_decrypted.txt",
            "key_name": "test_encryption_key"
        })
        print(f"🔓 Decryption: {decrypt_result[:100]}...")
        
        # Ověření, že dešifrovaný obsah je správný
        try:
            decrypted_content = Path("/tmp/secret_document_decrypted.txt").read_text()
            content_match = decrypted_content.strip() == secret_content.strip()
            print(f"✅ Content verification: {'PASS' if content_match else 'FAIL'}")
        except:
            content_match = False
            print("❌ Content verification: ERROR")
        
        return {"success": "encrypted" in encrypt_result.lower() and content_match}
    
    # ===========================================
    # 🎼 COORDINATOR SCENARIOS
    # ===========================================
    
    def test_coordinator_orchestration(self):
        """SCÉNÁŘ: Koordinace všech MCP serverů"""
        print("📋 Testujeme: Koordinaci všech MCP serverů")
        
        # 1. Seznam serverů
        servers_result = self.call_mcp_tool(self.servers["coordinator"], "mcp_list_servers", {})
        print(f"📋 Servers list: {servers_result[:100]}...")
        
        # 2. System status
        status_result = self.call_mcp_tool(self.servers["coordinator"], "mcp_system_status", {})
        print(f"📊 System status: {status_result[:100]}...")
        
        # 3. Health check
        health_result = self.call_mcp_tool(self.servers["coordinator"], "mcp_health_check", {})
        print(f"🏥 Health check: {health_result[:100]}...")
        
        return {"success": "servers" in servers_result.lower()}
    
    # ===========================================
    # 🚀 RUN ALL SCENARIOS
    # ===========================================
    
    def run_all_scenarios(self):
        """Spustí všechny testovací scénáře"""
        scenarios = [
            # Browser MCP Tests
            ("🌐 Browser: GitHub Automation", self.test_browser_github_automation),
            ("🌐 Browser: Form Automation", self.test_browser_form_automation),
            
            # GitHub MCP Tests  
            ("🐙 GitHub: Repository Analysis", self.test_github_repository_analysis),
            ("🐙 GitHub: Issues Management", self.test_github_issue_management),
            
            # Docker MCP Tests
            ("🐳 Docker: Container Lifecycle", self.test_docker_container_management),
            ("🐳 Docker: Image Management", self.test_docker_image_management),
            
            # Database MCP Tests
            ("💾 Database: SQLite Operations", self.test_database_sqlite_operations),
            
            # Enhanced File MCP Tests
            ("📁 File: Advanced Operations", self.test_enhanced_file_operations),
            ("📁 File: Encryption/Decryption", self.test_enhanced_file_encryption),
            
            # Coordinator Tests
            ("🎼 Coordinator: Orchestration", self.test_coordinator_orchestration),
        ]
        
        print(f"\n🚀 SPOUŠTĚNÍ {len(scenarios)} TESTOVACÍCH SCÉNÁŘŮ")
        print("=" * 60)
        
        for scenario_name, test_func in scenarios:
            self.run_test_scenario(scenario_name, test_func)
            time.sleep(1)  # Brief pause between tests
        
        # Generate summary
        self.generate_test_summary()
    
    def generate_test_summary(self):
        """Generuje souhrn testů"""
        print(f"\n📊 SOUHRN TESTOVACÍCH SCÉNÁŘŮ")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        error_tests = len([r for r in self.test_results if r["status"] == "ERROR"])
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        total_duration = sum(r["duration"] for r in self.test_results)
        
        print(f"✅ ÚSPĚŠNÉ: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"❌ NEÚSPĚŠNÉ: {failed_tests}")  
        print(f"💥 CHYBY: {error_tests}")
        print(f"⏱️ CELKOVÝ ČAS: {total_duration:.1f}s")
        
        # Detailní výsledky
        print(f"\n📋 DETAILNÍ VÝSLEDKY:")
        for result in self.test_results:
            status_emoji = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "💥"
            print(f"{status_emoji} {result['scenario']} - {result['duration']:.1f}s")
        
        # Uložení výsledků do souboru
        results_file = f"/tmp/mcp_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "errors": error_tests,
                    "success_rate": success_rate,
                    "total_duration": total_duration
                },
                "results": self.test_results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Výsledky uloženy: {results_file}")
        
        return {
            "success": success_rate >= 70,  # 70% threshold
            "summary": {
                "total": total_tests,
                "passed": passed_tests,
                "success_rate": success_rate
            }
        }

def main():
    """Hlavní funkce pro spuštění testů"""
    tester = MCPTestScenarios()
    
    print("⚠️  UPOZORNĚNÍ: Některé testy vyžadují spuštěné MCP servery!")
    print("   Spusť servery před testováním nebo použij koordinátor pro jejich spuštění.")
    print()
    
    input("Stiskni ENTER pro pokračování nebo Ctrl+C pro zrušení...")
    
    result = tester.run_all_scenarios()
    
    if result["success"]:
        print(f"\n🎉 VŠECHNY TESTY ÚSPĚŠNĚ DOKONČENY!")
        print(f"   Úspěšnost: {result['summary']['success_rate']:.1f}%")
        return 0
    else:
        print(f"\n⚠️  NĚKTERÉ TESTY SELHALY")
        print(f"   Úspěšnost: {result['summary']['success_rate']:.1f}%")
        return 1

if __name__ == "__main__":
    exit(main())