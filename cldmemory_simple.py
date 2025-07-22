#!/usr/bin/env python3
"""
Simple CLDMEMORY with Gemini Embeddings - No external deps
"""
import json
import sys
import urllib.request
import urllib.parse
from datetime import datetime
import sqlite3

class SimpleCLDMemory:
    def __init__(self):
        self.gemini_api_key = "AIzaSyAygZwIf8jDLyzHASNg7cNKz9383U93iV4"
        self.db_path = "/home/milhy777/memory-orchestration-system/data/cldmemory.db"
        self.max_memories = 5000  # Increased to 5K
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                summary TEXT,
                type TEXT DEFAULT 'semantic',
                importance REAL DEFAULT 0.5,
                embedding TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_embedding(self, text):
        """Create embedding using Gemini API"""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={self.gemini_api_key}"
            
            data = {
                "model": "models/text-embedding-004",
                "content": {"parts": [{"text": text}]}
            }
            
            json_data = json.dumps(data).encode('utf-8')
            request = urllib.request.Request(url, data=json_data)
            request.add_header('Content-Type', 'application/json')
            
            with urllib.request.urlopen(request, timeout=10) as response:
                result = json.loads(response.read().decode())
                return result['embedding']['values']
                
        except Exception as e:
            print(f"Embedding error: {e}", file=sys.stderr)
            return None
    
    def store_memory(self, content, memory_type="semantic", summary="", importance=0.5):
        """Store memory with Gemini embedding"""
        try:
            # Create embedding
            embedding = self.create_embedding(content)
            if not embedding:
                return {"success": False, "error": "Failed to create embedding"}
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO memories (content, summary, type, importance, embedding)
                VALUES (?, ?, ?, ?, ?)
            ''', (content, summary, memory_type, importance, json.dumps(embedding)))
            
            memory_id = cursor.lastrowid
            
            # Check if we need to cleanup old memories
            cursor.execute('SELECT COUNT(*) FROM memories')
            count = cursor.fetchone()[0]
            
            if count > self.max_memories:
                # Delete oldest low-importance memories
                cursor.execute('''
                    DELETE FROM memories 
                    WHERE id IN (
                        SELECT id FROM memories 
                        WHERE importance < 0.5 
                        ORDER BY created_at ASC 
                        LIMIT ?
                    )
                ''', (count - self.max_memories,))
                
                # If still too many, delete oldest regardless of importance
                cursor.execute('SELECT COUNT(*) FROM memories')
                count = cursor.fetchone()[0]
                if count > self.max_memories:
                    cursor.execute('''
                        DELETE FROM memories 
                        WHERE id IN (
                            SELECT id FROM memories 
                            ORDER BY created_at ASC 
                            LIMIT ?
                        )
                    ''', (count - self.max_memories,))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "memory_id": memory_id,
                "message": "Memory stored with REAL Gemini embeddings!",
                "type": memory_type,
                "importance": importance,
                "embedding_size": len(embedding)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def cosine_similarity(self, a, b):
        """Calculate cosine similarity"""
        import math
        
        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = math.sqrt(sum(x * x for x in a))
        magnitude_b = math.sqrt(sum(x * x for x in b))
        
        if magnitude_a == 0 or magnitude_b == 0:
            return 0
        
        return dot_product / (magnitude_a * magnitude_b)
    
    def search_memories(self, query, limit=10):
        """Search memories using semantic similarity"""
        try:
            # Create query embedding
            query_embedding = self.create_embedding(query)
            if not query_embedding:
                return {"success": False, "error": "Failed to create query embedding"}
            
            # Get all memories
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, content, summary, type, importance, embedding, created_at FROM memories')
            memories = cursor.fetchall()
            conn.close()
            
            if not memories:
                return {
                    "success": True,
                    "results": [],
                    "message": "No memories found"
                }
            
            # Calculate similarities
            results = []
            for memory in memories:
                memory_id, content, summary, mem_type, importance, embedding_json, created_at = memory
                
                try:
                    memory_embedding = json.loads(embedding_json)
                    similarity = self.cosine_similarity(query_embedding, memory_embedding)
                    
                    results.append({
                        "id": memory_id,
                        "content": content,
                        "summary": summary,
                        "type": mem_type,
                        "importance": importance,
                        "similarity": round(similarity, 4),
                        "created_at": created_at
                    })
                except:
                    continue
            
            # Sort by similarity and limit
            results.sort(key=lambda x: x['similarity'], reverse=True)
            results = results[:limit]
            
            return {
                "success": True,
                "results": results,
                "query": query,
                "total_found": len(results),
                "message": "Search completed with Gemini semantic similarity"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

def handle_mcp_request(request):
    """Handle MCP request"""
    try:
        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id")
        
        memory = SimpleCLDMemory()
        
        if method == "tools/call":
            tool_name = params.get("name", "")
            args = params.get("arguments", {})
            
            if tool_name == "store_memory":
                result = memory.store_memory(
                    content=args.get("content", ""),
                    memory_type=args.get("type", "semantic"),
                    summary=args.get("summary", ""),
                    importance=args.get("importance", 0.5)
                )
            elif tool_name == "search_memories":
                result = memory.search_memories(
                    query=args.get("query", ""),
                    limit=args.get("limit", 10)
                )
            else:
                result = {"success": False, "error": f"Unknown tool: {tool_name}"}
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            }
        
        else:
            return {"success": False, "error": f"Method not supported: {method}"}
    
    except Exception as e:
        return {"success": False, "error": f"Internal error: {str(e)}"}

def main():
    """Simple test mode"""
    print("🧠 Simple CLDMEMORY with Gemini Embeddings", file=sys.stderr)
    
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            request = json.loads(line)
            response = handle_mcp_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()