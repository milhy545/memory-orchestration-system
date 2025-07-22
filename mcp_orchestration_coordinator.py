#!/usr/bin/env python3
"""
MCP Orchestration Coordinator - Univerzální launcher a koordinátor
Spravuje všechny MCP servery v orchestraci a poskytuje jednotné API
"""
import json
import sys
import subprocess
import requests
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import threading
import time

class MCPOrchestrationCoordinator:
    def __init__(self):
        self.base_path = Path("/home/milhy777/memory-orchestration-system")
        self.coordinator_url = "http://192.168.0.58:8020/mcp"
        
        # MCP Servers configuration
        self.mcp_servers = {
            "zen_coordinator": {
                "script": "zen_coordinator_updated.py",
                "description": "Main Zen MCP Server with AI tools",
                "port": 8020,
                "status": "unknown",
                "process": None,
                "tools": ["chat", "codereview", "debug", "refactor", "thinkdeep", "planner", "consensus"]
            },
            "github": {
                "script": "github_mcp_server.py", 
                "description": "GitHub API integration",
                "port": 8021,
                "status": "unknown",
                "process": None,
                "tools": ["list_repos", "get_repo_info", "list_issues", "create_issue", "list_commits", "get_file_content", "list_pull_requests", "search_code"]
            },
            "docker": {
                "script": "docker_mcp_server.py",
                "description": "Docker container management",
                "port": 8022,
                "status": "unknown", 
                "process": None,
                "tools": ["list_containers", "start_container", "stop_container", "create_container", "execute_command", "system_info"]
            },
            "database": {
                "script": "database_mcp_server.py",
                "description": "Database operations (PostgreSQL, MySQL, SQLite)",
                "port": 8023,
                "status": "unknown",
                "process": None,
                "tools": ["db_connect", "db_execute_query", "db_get_tables", "db_get_table_schema", "db_backup_table"]
            },
            "enhanced_file": {
                "script": "enhanced_file_mcp_server.py",
                "description": "Advanced file operations",
                "port": 8024,
                "status": "unknown",
                "process": None,
                "tools": ["file_analyze", "directory_scan", "file_compress", "file_extract", "file_encrypt", "find_duplicates", "file_sync"]
            },
            "gmail": {
                "script": "gmail_mcp_server/src/email_client/server.py",
                "description": "Gmail MCP integration",
                "port": 8025,
                "status": "unknown",
                "process": None,
                "tools": ["search_emails", "send_email", "get_email_content"]
            },
            "browser": {
                "script": "browser_mcp_server.py",
                "description": "Browser automation and web testing",
                "port": 8026,
                "status": "unknown",
                "process": None,
                "tools": ["browser_start", "browser_navigate", "browser_click", "browser_type", "browser_screenshot", "browser_execute_js", "browser_get_text", "browser_scroll"]
            }
        }
        
        # Memory system endpoints
        self.memory_services = {
            "cldmemory": {
                "url": "http://localhost:8006",
                "description": "CLDMEMORY with Gemini embeddings",
                "status": "unknown"
            },
            "qdrant": {
                "url": "http://192.168.0.58:8008", 
                "description": "Qdrant vector database",
                "status": "unknown"
            }
        }
        
    def get_tools(self):
        """Return orchestration coordination tools"""
        return [
            {
                "name": "mcp_list_servers",
                "description": "List all MCP servers and their status",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "mcp_start_server",
                "description": "Start specific MCP server",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "server_name": {
                            "type": "string",
                            "description": "Name of MCP server to start"
                        }
                    },
                    "required": ["server_name"]
                }
            },
            {
                "name": "mcp_stop_server",
                "description": "Stop specific MCP server",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "server_name": {
                            "type": "string",
                            "description": "Name of MCP server to stop"
                        }
                    },
                    "required": ["server_name"]
                }
            },
            {
                "name": "mcp_restart_server",
                "description": "Restart specific MCP server",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "server_name": {
                            "type": "string",
                            "description": "Name of MCP server to restart"
                        }
                    },
                    "required": ["server_name"]
                }
            },
            {
                "name": "mcp_start_all",
                "description": "Start all MCP servers",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "mcp_stop_all",
                "description": "Stop all MCP servers",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "mcp_get_server_tools",
                "description": "Get available tools for specific server",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "server_name": {
                            "type": "string",
                            "description": "Name of MCP server"
                        }
                    },
                    "required": ["server_name"]
                }
            },
            {
                "name": "mcp_call_tool",
                "description": "Call tool on specific MCP server",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "server_name": {
                            "type": "string",
                            "description": "MCP server name"
                        },
                        "tool_name": {
                            "type": "string",
                            "description": "Tool name to call"
                        },
                        "arguments": {
                            "type": "object",
                            "description": "Tool arguments"
                        }
                    },
                    "required": ["server_name", "tool_name"]
                }
            },
            {
                "name": "mcp_system_status",
                "description": "Get complete orchestration system status",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "mcp_health_check",
                "description": "Perform health check on all services",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    
    def check_server_status(self, server_name: str) -> str:
        """Check if MCP server is running"""
        if server_name not in self.mcp_servers:
            return "unknown"
        
        server_config = self.mcp_servers[server_name]
        
        # Check if process is still running
        if server_config["process"]:
            if server_config["process"].poll() is None:
                return "running"
            else:
                server_config["process"] = None
                return "stopped"
        
        return "stopped"
    
    def start_server(self, server_name: str) -> Dict:
        """Start specific MCP server"""
        if server_name not in self.mcp_servers:
            return {"success": False, "error": f"Unknown server: {server_name}"}
        
        server_config = self.mcp_servers[server_name]
        
        # Check if already running
        if self.check_server_status(server_name) == "running":
            return {"success": False, "error": f"Server {server_name} is already running"}
        
        try:
            script_path = self.base_path / server_config["script"]
            
            if not script_path.exists():
                return {"success": False, "error": f"Script not found: {script_path}"}
            
            # Start server process
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                cwd=str(self.base_path)
            )
            
            server_config["process"] = process
            server_config["status"] = "starting"
            
            # Give it a moment to start
            time.sleep(2)
            
            # Check if it started successfully
            if process.poll() is None:
                server_config["status"] = "running"
                return {
                    "success": True,
                    "message": f"Server {server_name} started successfully",
                    "pid": process.pid
                }
            else:
                stderr_output = process.stderr.read().decode() if process.stderr else ""
                return {
                    "success": False,
                    "error": f"Server {server_name} failed to start: {stderr_output}"
                }
                
        except Exception as e:
            return {"success": False, "error": f"Failed to start {server_name}: {str(e)}"}
    
    def stop_server(self, server_name: str) -> Dict:
        """Stop specific MCP server"""
        if server_name not in self.mcp_servers:
            return {"success": False, "error": f"Unknown server: {server_name}"}
        
        server_config = self.mcp_servers[server_name]
        
        if not server_config["process"]:
            return {"success": False, "error": f"Server {server_name} is not running"}
        
        try:
            # Terminate process
            server_config["process"].terminate()
            
            # Wait for graceful shutdown
            try:
                server_config["process"].wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't stop gracefully
                server_config["process"].kill()
                server_config["process"].wait()
            
            server_config["process"] = None
            server_config["status"] = "stopped"
            
            return {
                "success": True,
                "message": f"Server {server_name} stopped successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to stop {server_name}: {str(e)}"}
    
    def restart_server(self, server_name: str) -> Dict:
        """Restart specific MCP server"""
        stop_result = self.stop_server(server_name)
        if not stop_result["success"]:
            return stop_result
        
        time.sleep(1)  # Brief pause
        
        start_result = self.start_server(server_name)
        return start_result
    
    def start_all_servers(self) -> Dict:
        """Start all MCP servers"""
        results = {}
        
        for server_name in self.mcp_servers:
            result = self.start_server(server_name)
            results[server_name] = result
            
            # Brief pause between starts to avoid overwhelming
            time.sleep(1)
        
        successful = sum(1 for r in results.values() if r["success"])
        total = len(results)
        
        return {
            "success": successful == total,
            "message": f"Started {successful}/{total} servers",
            "details": results
        }
    
    def stop_all_servers(self) -> Dict:
        """Stop all MCP servers"""
        results = {}
        
        for server_name in self.mcp_servers:
            if self.check_server_status(server_name) == "running":
                result = self.stop_server(server_name)
                results[server_name] = result
        
        successful = sum(1 for r in results.values() if r["success"])
        total = len(results)
        
        return {
            "success": successful == total,
            "message": f"Stopped {successful}/{total} running servers",
            "details": results
        }
    
    def list_servers(self) -> Dict:
        """List all MCP servers and their status"""
        servers = []
        
        for server_name, config in self.mcp_servers.items():
            status = self.check_server_status(server_name)
            
            server_info = {
                "name": server_name,
                "description": config["description"],
                "script": config["script"],
                "port": config["port"],
                "status": status,
                "tools": config["tools"],
                "pid": config["process"].pid if config["process"] else None
            }
            servers.append(server_info)
        
        return {
            "success": True,
            "data": {
                "servers": servers,
                "total_servers": len(servers),
                "running_servers": len([s for s in servers if s["status"] == "running"]),
                "stopped_servers": len([s for s in servers if s["status"] == "stopped"])
            }
        }
    
    def get_server_tools(self, server_name: str) -> Dict:
        """Get available tools for specific server"""
        if server_name not in self.mcp_servers:
            return {"success": False, "error": f"Unknown server: {server_name}"}
        
        return {
            "success": True,
            "data": {
                "server": server_name,
                "tools": self.mcp_servers[server_name]["tools"],
                "status": self.check_server_status(server_name)
            }
        }
    
    def call_tool(self, server_name: str, tool_name: str, arguments: Dict = None) -> Dict:
        """Call tool on specific MCP server"""
        if server_name not in self.mcp_servers:
            return {"success": False, "error": f"Unknown server: {server_name}"}
        
        if self.check_server_status(server_name) != "running":
            return {"success": False, "error": f"Server {server_name} is not running"}
        
        try:
            # For now, route through the main coordinator
            # In practice, each server would have its own endpoint
            if server_name == "zen_coordinator":
                url = self.coordinator_url
            else:
                # Direct tool calls to other servers would need their own endpoints
                return {"success": False, "error": f"Direct tool calls to {server_name} not implemented yet"}
            
            data = {
                "tool": tool_name,
                "arguments": arguments or {}
            }
            
            response = requests.post(url, json=data, timeout=30)
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {
                    "success": False,
                    "error": f"Tool call failed: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            return {"success": False, "error": f"Tool call failed: {str(e)}"}
    
    def check_memory_services(self) -> Dict:
        """Check status of memory services"""
        services_status = {}
        
        for service_name, config in self.memory_services.items():
            try:
                response = requests.get(f"{config['url']}/health", timeout=5)
                if response.status_code == 200:
                    services_status[service_name] = {
                        "status": "running",
                        "url": config["url"],
                        "description": config["description"]
                    }
                else:
                    services_status[service_name] = {
                        "status": "error",
                        "url": config["url"],
                        "error": f"HTTP {response.status_code}"
                    }
            except Exception as e:
                services_status[service_name] = {
                    "status": "offline",
                    "url": config["url"],
                    "error": str(e)
                }
        
        return services_status
    
    def system_status(self) -> Dict:
        """Get complete orchestration system status"""
        # MCP Servers status
        servers_info = self.list_servers()
        
        # Memory services status
        memory_status = self.check_memory_services()
        
        # Overall health
        total_mcp_servers = servers_info["data"]["total_servers"]
        running_mcp_servers = servers_info["data"]["running_servers"]
        running_memory_services = sum(1 for s in memory_status.values() if s["status"] == "running")
        total_memory_services = len(memory_status)
        
        overall_health = "healthy" if (running_mcp_servers == total_mcp_servers and 
                                     running_memory_services == total_memory_services) else "degraded"
        
        return {
            "success": True,
            "data": {
                "timestamp": datetime.now().isoformat(),
                "overall_health": overall_health,
                "mcp_servers": servers_info["data"],
                "memory_services": memory_status,
                "summary": {
                    "total_services": total_mcp_servers + total_memory_services,
                    "running_services": running_mcp_servers + running_memory_services,
                    "offline_services": (total_mcp_servers - running_mcp_servers) + (total_memory_services - running_memory_services)
                }
            }
        }
    
    def health_check(self) -> Dict:
        """Perform comprehensive health check"""
        health_results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }
        
        # Check MCP servers
        for server_name in self.mcp_servers:
            status = self.check_server_status(server_name)
            health_results["checks"][f"mcp_{server_name}"] = {
                "status": status,
                "healthy": status == "running"
            }
        
        # Check memory services
        memory_status = self.check_memory_services()
        for service_name, status_info in memory_status.items():
            health_results["checks"][f"memory_{service_name}"] = {
                "status": status_info["status"],
                "healthy": status_info["status"] == "running"
            }
        
        # Overall health score
        total_checks = len(health_results["checks"])
        healthy_checks = sum(1 for check in health_results["checks"].values() if check["healthy"])
        health_score = (healthy_checks / total_checks) * 100 if total_checks > 0 else 0
        
        health_results["health_score"] = health_score
        health_results["overall_status"] = "healthy" if health_score >= 80 else "unhealthy"
        
        return {"success": True, "data": health_results}
    
    def handle_tool_call(self, tool_name: str, arguments: Dict) -> Dict:
        """Handle orchestration tool calls"""
        try:
            if tool_name == "mcp_list_servers":
                return self.list_servers()
            elif tool_name == "mcp_start_server":
                return self.start_server(**arguments)
            elif tool_name == "mcp_stop_server":
                return self.stop_server(**arguments)
            elif tool_name == "mcp_restart_server":
                return self.restart_server(**arguments)
            elif tool_name == "mcp_start_all":
                return self.start_all_servers()
            elif tool_name == "mcp_stop_all":
                return self.stop_all_servers()
            elif tool_name == "mcp_get_server_tools":
                return self.get_server_tools(**arguments)
            elif tool_name == "mcp_call_tool":
                return self.call_tool(**arguments)
            elif tool_name == "mcp_system_status":
                return self.system_status()
            elif tool_name == "mcp_health_check":
                return self.health_check()
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}
                
        except Exception as e:
            return {"success": False, "error": f"Tool execution failed: {str(e)}"}

def main():
    """Main MCP server loop for Orchestration Coordinator"""
    coordinator = MCPOrchestrationCoordinator()
    
    print("🎼 MCP Orchestration Coordinator Started", file=sys.stderr)
    print(f"📁 Base Path: {coordinator.base_path}", file=sys.stderr)
    print(f"🎯 Zen Coordinator: {coordinator.coordinator_url}", file=sys.stderr)
    
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            request = json.loads(line)
            method = request.get("method", "")
            
            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {
                            "name": "MCP Orchestration Coordinator",
                            "version": "1.0.0"
                        }
                    }
                }
            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {"tools": coordinator.get_tools()}
                }
            elif method == "tools/call":
                params = request.get("params", {})
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})
                
                result = coordinator.handle_tool_call(tool_name, arguments)
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                }
            elif method == "notifications/initialized":
                continue  # No response needed
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            print(json.dumps(response))
            sys.stdout.flush()
            
        except json.JSONDecodeError:
            error_response = {
                "jsonrpc": "2.0",
                "id": 1,
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()

if __name__ == "__main__":
    main()