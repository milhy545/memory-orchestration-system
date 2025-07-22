#!/usr/bin/env python3
"""
Database MCP Server - Integrace s PostgreSQL, MySQL, SQLite
Poskytuje AI přístup k databázím pro dotazy, schema inspekce, data management
"""
import json
import sys
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# Optional imports for PostgreSQL and MySQL
try:
    import psycopg2
    import psycopg2.extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

class DatabaseMCPServer:
    def __init__(self):
        self.connections = {}
        self.connection_configs = {}
        
    def get_tools(self):
        """Return available database tools"""
        tools = [
            {
                "name": "db_connect",
                "description": "Connect to database (PostgreSQL, MySQL, SQLite)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "connection_name": {
                            "type": "string",
                            "description": "Unique name for this connection"
                        },
                        "db_type": {
                            "type": "string",
                            "enum": ["postgresql", "mysql", "sqlite"],
                            "description": "Database type"
                        },
                        "host": {
                            "type": "string",
                            "description": "Database host (not needed for SQLite)"
                        },
                        "port": {
                            "type": "number",
                            "description": "Database port (not needed for SQLite)"
                        },
                        "database": {
                            "type": "string",
                            "description": "Database name or SQLite file path"
                        },
                        "username": {
                            "type": "string",
                            "description": "Database username (not needed for SQLite)"
                        },
                        "password": {
                            "type": "string",
                            "description": "Database password (not needed for SQLite)"
                        }
                    },
                    "required": ["connection_name", "db_type", "database"]
                }
            },
            {
                "name": "db_disconnect",
                "description": "Disconnect from database",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "connection_name": {
                            "type": "string",
                            "description": "Connection name to disconnect"
                        }
                    },
                    "required": ["connection_name"]
                }
            },
            {
                "name": "db_list_connections",
                "description": "List active database connections",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "db_execute_query",
                "description": "Execute SQL query",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "connection_name": {
                            "type": "string",
                            "description": "Database connection to use"
                        },
                        "query": {
                            "type": "string",
                            "description": "SQL query to execute"
                        },
                        "params": {
                            "type": "array",
                            "description": "Query parameters for prepared statements"
                        },
                        "fetch_results": {
                            "type": "boolean",
                            "default": True,
                            "description": "Whether to fetch and return results"
                        },
                        "limit": {
                            "type": "number",
                            "default": 100,
                            "description": "Maximum number of rows to return"
                        }
                    },
                    "required": ["connection_name", "query"]
                }
            },
            {
                "name": "db_get_tables",
                "description": "List tables in database",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "connection_name": {
                            "type": "string",
                            "description": "Database connection to use"
                        },
                        "schema": {
                            "type": "string",
                            "description": "Schema name (PostgreSQL only)"
                        }
                    },
                    "required": ["connection_name"]
                }
            },
            {
                "name": "db_get_table_schema",
                "description": "Get table schema/structure",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "connection_name": {
                            "type": "string",
                            "description": "Database connection to use"
                        },
                        "table_name": {
                            "type": "string",
                            "description": "Table name to inspect"
                        },
                        "schema": {
                            "type": "string",
                            "description": "Schema name (PostgreSQL only)"
                        }
                    },
                    "required": ["connection_name", "table_name"]
                }
            },
            {
                "name": "db_get_indexes",
                "description": "Get indexes for table",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "connection_name": {
                            "type": "string",
                            "description": "Database connection to use"
                        },
                        "table_name": {
                            "type": "string",
                            "description": "Table name"
                        },
                        "schema": {
                            "type": "string",
                            "description": "Schema name (PostgreSQL only)"
                        }
                    },
                    "required": ["connection_name", "table_name"]
                }
            },
            {
                "name": "db_explain_query",
                "description": "Get query execution plan",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "connection_name": {
                            "type": "string",
                            "description": "Database connection to use"
                        },
                        "query": {
                            "type": "string",
                            "description": "SQL query to explain"
                        },
                        "analyze": {
                            "type": "boolean",
                            "default": False,
                            "description": "Run EXPLAIN ANALYZE (actually executes query)"
                        }
                    },
                    "required": ["connection_name", "query"]
                }
            },
            {
                "name": "db_backup_table",
                "description": "Create backup of table data",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "connection_name": {
                            "type": "string",
                            "description": "Database connection to use"
                        },
                        "table_name": {
                            "type": "string",
                            "description": "Table to backup"
                        },
                        "output_file": {
                            "type": "string",
                            "description": "Output file path for backup"
                        },
                        "format": {
                            "type": "string",
                            "enum": ["json", "csv", "sql"],
                            "default": "json",
                            "description": "Backup format"
                        }
                    },
                    "required": ["connection_name", "table_name", "output_file"]
                }
            },
            {
                "name": "db_database_stats",
                "description": "Get database statistics",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "connection_name": {
                            "type": "string",
                            "description": "Database connection to use"
                        }
                    },
                    "required": ["connection_name"]
                }
            }
        ]
        
        return tools
    
    def connect_database(self, connection_name: str, db_type: str, database: str, 
                        host: str = None, port: int = None, username: str = None, 
                        password: str = None) -> Dict:
        """Connect to database"""
        
        if connection_name in self.connections:
            return {"success": False, "error": f"Connection '{connection_name}' already exists"}
        
        try:
            if db_type == "sqlite":
                connection = sqlite3.connect(database)
                connection.row_factory = sqlite3.Row  # Enable column access by name
                
            elif db_type == "postgresql":
                if not POSTGRES_AVAILABLE:
                    return {"success": False, "error": "psycopg2 not available. Install with: pip install psycopg2-binary"}
                
                connection = psycopg2.connect(
                    host=host,
                    port=port or 5432,
                    database=database,
                    user=username,
                    password=password
                )
                connection.autocommit = True
                
            elif db_type == "mysql":
                if not MYSQL_AVAILABLE:
                    return {"success": False, "error": "mysql-connector not available. Install with: pip install mysql-connector-python"}
                
                connection = mysql.connector.connect(
                    host=host,
                    port=port or 3306,
                    database=database,
                    user=username,
                    password=password,
                    autocommit=True
                )
            else:
                return {"success": False, "error": f"Unsupported database type: {db_type}"}
            
            # Test connection
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            
            self.connections[connection_name] = connection
            self.connection_configs[connection_name] = {
                "db_type": db_type,
                "database": database,
                "host": host,
                "port": port,
                "username": username,
                "connected_at": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "message": f"Connected to {db_type} database '{database}' as '{connection_name}'"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to connect: {str(e)}"}
    
    def disconnect_database(self, connection_name: str) -> Dict:
        """Disconnect from database"""
        if connection_name not in self.connections:
            return {"success": False, "error": f"Connection '{connection_name}' not found"}
        
        try:
            self.connections[connection_name].close()
            del self.connections[connection_name]
            del self.connection_configs[connection_name]
            
            return {"success": True, "message": f"Disconnected from '{connection_name}'"}
            
        except Exception as e:
            return {"success": False, "error": f"Failed to disconnect: {str(e)}"}
    
    def list_connections(self) -> Dict:
        """List active connections"""
        connections = []
        for name, config in self.connection_configs.items():
            connections.append({
                "name": name,
                "type": config["db_type"],
                "database": config["database"],
                "host": config.get("host", "local"),
                "connected_at": config["connected_at"]
            })
        
        return {"success": True, "data": connections}
    
    def execute_query(self, connection_name: str, query: str, params: List = None, 
                     fetch_results: bool = True, limit: int = 100) -> Dict:
        """Execute SQL query"""
        if connection_name not in self.connections:
            return {"success": False, "error": f"Connection '{connection_name}' not found"}
        
        connection = self.connections[connection_name]
        db_type = self.connection_configs[connection_name]["db_type"]
        
        try:
            cursor = connection.cursor()
            
            # Execute query with parameters
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            result = {"success": True, "query": query}
            
            if fetch_results:
                if query.strip().upper().startswith(('SELECT', 'WITH', 'SHOW', 'DESCRIBE', 'EXPLAIN')):
                    rows = cursor.fetchmany(limit)
                    
                    # Convert rows to list of dictionaries
                    if db_type == "sqlite":
                        columns = [description[0] for description in cursor.description]
                        data = [dict(zip(columns, row)) for row in rows]
                    elif db_type == "postgresql":
                        columns = [desc[0] for desc in cursor.description]
                        data = [dict(zip(columns, row)) for row in rows]
                    elif db_type == "mysql":
                        columns = cursor.column_names
                        data = [dict(zip(columns, row)) for row in rows]
                    
                    result["data"] = data
                    result["row_count"] = len(data)
                    result["columns"] = columns
                else:
                    # For INSERT, UPDATE, DELETE, etc.
                    result["rows_affected"] = cursor.rowcount
            
            cursor.close()
            return result
            
        except Exception as e:
            return {"success": False, "error": f"Query execution failed: {str(e)}"}
    
    def get_tables(self, connection_name: str, schema: str = None) -> Dict:
        """List tables in database"""
        if connection_name not in self.connections:
            return {"success": False, "error": f"Connection '{connection_name}' not found"}
        
        db_type = self.connection_configs[connection_name]["db_type"]
        
        try:
            if db_type == "sqlite":
                query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            elif db_type == "postgresql":
                if schema:
                    query = f"SELECT tablename FROM pg_tables WHERE schemaname='{schema}' ORDER BY tablename"
                else:
                    query = "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
            elif db_type == "mysql":
                query = "SHOW TABLES"
            
            result = self.execute_query(connection_name, query)
            
            if result["success"]:
                # Flatten the result to just table names
                if db_type == "sqlite":
                    tables = [row["name"] for row in result["data"]]
                elif db_type == "postgresql":
                    tables = [row["tablename"] for row in result["data"]]
                elif db_type == "mysql":
                    column_name = result["columns"][0]
                    tables = [row[column_name] for row in result["data"]]
                
                return {"success": True, "data": {"tables": tables}}
            else:
                return result
                
        except Exception as e:
            return {"success": False, "error": f"Failed to get tables: {str(e)}"}
    
    def get_table_schema(self, connection_name: str, table_name: str, schema: str = None) -> Dict:
        """Get table schema/structure"""
        if connection_name not in self.connections:
            return {"success": False, "error": f"Connection '{connection_name}' not found"}
        
        db_type = self.connection_configs[connection_name]["db_type"]
        
        try:
            if db_type == "sqlite":
                query = f"PRAGMA table_info({table_name})"
            elif db_type == "postgresql":
                schema_name = schema or "public"
                query = f"""
                SELECT column_name, data_type, is_nullable, column_default 
                FROM information_schema.columns 
                WHERE table_name='{table_name}' AND table_schema='{schema_name}'
                ORDER BY ordinal_position
                """
            elif db_type == "mysql":
                query = f"DESCRIBE {table_name}"
            
            result = self.execute_query(connection_name, query)
            
            if result["success"]:
                return {"success": True, "data": {"schema": result["data"], "table": table_name}}
            else:
                return result
                
        except Exception as e:
            return {"success": False, "error": f"Failed to get table schema: {str(e)}"}
    
    def get_indexes(self, connection_name: str, table_name: str, schema: str = None) -> Dict:
        """Get indexes for table"""
        if connection_name not in self.connections:
            return {"success": False, "error": f"Connection '{connection_name}' not found"}
        
        db_type = self.connection_configs[connection_name]["db_type"]
        
        try:
            if db_type == "sqlite":
                query = f"PRAGMA index_list({table_name})"
            elif db_type == "postgresql":
                schema_name = schema or "public"
                query = f"""
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE tablename='{table_name}' AND schemaname='{schema_name}'
                """
            elif db_type == "mysql":
                query = f"SHOW INDEXES FROM {table_name}"
            
            result = self.execute_query(connection_name, query)
            
            if result["success"]:
                return {"success": True, "data": {"indexes": result["data"], "table": table_name}}
            else:
                return result
                
        except Exception as e:
            return {"success": False, "error": f"Failed to get indexes: {str(e)}"}
    
    def explain_query(self, connection_name: str, query: str, analyze: bool = False) -> Dict:
        """Get query execution plan"""
        if connection_name not in self.connections:
            return {"success": False, "error": f"Connection '{connection_name}' not found"}
        
        db_type = self.connection_configs[connection_name]["db_type"]
        
        try:
            if db_type == "sqlite":
                explain_query = f"EXPLAIN QUERY PLAN {query}"
            elif db_type == "postgresql":
                if analyze:
                    explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
                else:
                    explain_query = f"EXPLAIN (FORMAT JSON) {query}"
            elif db_type == "mysql":
                explain_query = f"EXPLAIN FORMAT=JSON {query}"
            
            result = self.execute_query(connection_name, explain_query)
            
            if result["success"]:
                return {"success": True, "data": {"plan": result["data"], "original_query": query}}
            else:
                return result
                
        except Exception as e:
            return {"success": False, "error": f"Failed to explain query: {str(e)}"}
    
    def backup_table(self, connection_name: str, table_name: str, output_file: str, format: str = "json") -> Dict:
        """Create backup of table data"""
        if connection_name not in self.connections:
            return {"success": False, "error": f"Connection '{connection_name}' not found"}
        
        try:
            # Get all data from table
            query = f"SELECT * FROM {table_name}"
            result = self.execute_query(connection_name, query, limit=10000)
            
            if not result["success"]:
                return result
            
            # Write backup file
            if format == "json":
                import json
                with open(output_file, 'w') as f:
                    json.dump({
                        "table": table_name,
                        "backup_date": datetime.now().isoformat(),
                        "row_count": result["row_count"],
                        "columns": result["columns"],
                        "data": result["data"]
                    }, f, indent=2, default=str)
                    
            elif format == "csv":
                import csv
                with open(output_file, 'w', newline='') as f:
                    if result["data"]:
                        writer = csv.DictWriter(f, fieldnames=result["columns"])
                        writer.writeheader()
                        writer.writerows(result["data"])
                        
            elif format == "sql":
                with open(output_file, 'w') as f:
                    f.write(f"-- Backup of table {table_name}\n")
                    f.write(f"-- Generated on {datetime.now().isoformat()}\n\n")
                    
                    for row in result["data"]:
                        columns = ", ".join(row.keys())
                        values = ", ".join([f"'{v}'" if v is not None else "NULL" for v in row.values()])
                        f.write(f"INSERT INTO {table_name} ({columns}) VALUES ({values});\n")
            
            return {
                "success": True,
                "message": f"Table {table_name} backed up to {output_file}",
                "rows_backed_up": result["row_count"],
                "format": format
            }
            
        except Exception as e:
            return {"success": False, "error": f"Backup failed: {str(e)}"}
    
    def database_stats(self, connection_name: str) -> Dict:
        """Get database statistics"""
        if connection_name not in self.connections:
            return {"success": False, "error": f"Connection '{connection_name}' not found"}
        
        db_type = self.connection_configs[connection_name]["db_type"]
        
        try:
            stats = {"database_type": db_type}
            
            if db_type == "sqlite":
                # SQLite specific stats
                queries = {
                    "database_size": "SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()",
                    "table_count": "SELECT COUNT(*) as count FROM sqlite_master WHERE type='table'"
                }
                
            elif db_type == "postgresql":
                # PostgreSQL specific stats
                queries = {
                    "database_size": "SELECT pg_size_pretty(pg_database_size(current_database())) as size",
                    "table_count": "SELECT COUNT(*) as count FROM pg_tables WHERE schemaname='public'"
                }
                
            elif db_type == "mysql":
                # MySQL specific stats
                database_name = self.connection_configs[connection_name]["database"]
                queries = {
                    "database_size": f"SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 1) AS size FROM information_schema.tables WHERE table_schema='{database_name}'",
                    "table_count": f"SELECT COUNT(*) as count FROM information_schema.tables WHERE table_schema='{database_name}'"
                }
            
            # Execute stat queries
            for stat_name, query in queries.items():
                result = self.execute_query(connection_name, query)
                if result["success"] and result["data"]:
                    stats[stat_name] = result["data"][0]
            
            return {"success": True, "data": stats}
            
        except Exception as e:
            return {"success": False, "error": f"Failed to get database stats: {str(e)}"}
    
    def handle_tool_call(self, tool_name: str, arguments: Dict) -> Dict:
        """Handle database tool calls"""
        try:
            if tool_name == "db_connect":
                return self.connect_database(**arguments)
            elif tool_name == "db_disconnect":
                return self.disconnect_database(**arguments)
            elif tool_name == "db_list_connections":
                return self.list_connections()
            elif tool_name == "db_execute_query":
                return self.execute_query(**arguments)
            elif tool_name == "db_get_tables":
                return self.get_tables(**arguments)
            elif tool_name == "db_get_table_schema":
                return self.get_table_schema(**arguments)
            elif tool_name == "db_get_indexes":
                return self.get_indexes(**arguments)
            elif tool_name == "db_explain_query":
                return self.explain_query(**arguments)
            elif tool_name == "db_backup_table":
                return self.backup_table(**arguments)
            elif tool_name == "db_database_stats":
                return self.database_stats(**arguments)
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}
                
        except Exception as e:
            return {"success": False, "error": f"Tool execution failed: {str(e)}"}

def main():
    """Main MCP server loop for Database integration"""
    server = DatabaseMCPServer()
    
    print("💾 Database MCP Server Started", file=sys.stderr)
    print(f"🐘 PostgreSQL: {'✅ Available' if POSTGRES_AVAILABLE else '❌ Missing (pip install psycopg2-binary)'}", file=sys.stderr)
    print(f"🐬 MySQL: {'✅ Available' if MYSQL_AVAILABLE else '❌ Missing (pip install mysql-connector-python)'}", file=sys.stderr)
    print(f"📁 SQLite: ✅ Available", file=sys.stderr)
    
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
                            "name": "Database MCP Server",
                            "version": "1.0.0"
                        }
                    }
                }
            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {"tools": server.get_tools()}
                }
            elif method == "tools/call":
                params = request.get("params", {})
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})
                
                result = server.handle_tool_call(tool_name, arguments)
                
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