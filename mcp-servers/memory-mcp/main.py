from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import psycopg2.extras
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

app = FastAPI(
    title="Memory MCP API",
    description="API for memory storage and retrieval operations using PostgreSQL.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# PostgreSQL configuration
DATABASE_URL = os.getenv('MCP_DATABASE_URL', 'postgresql://mcp_admin:mcp_secure_2024@postgresql:5432/mcp_unified')

def get_memory_connection():
    """Get connection to PostgreSQL database"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

def ensure_table_exists():
    """Ensure the memory table exists"""
    conn = get_memory_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS unified_memory (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    type VARCHAR(50) DEFAULT 'user',
                    importance REAL DEFAULT 0.5,
                    agent VARCHAR(100) DEFAULT 'claude-code',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB DEFAULT '{}'
                )
            """)
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Table creation failed: {str(e)}")
    finally:
        conn.close()

class MemoryEntry(BaseModel):
    content: str
    type: Optional[str] = "user"
    importance: Optional[float] = 0.5
    agent: Optional[str] = "claude-code"
    metadata: Optional[Dict[str, Any]] = {}

class MemoryResponse(BaseModel):
    id: int
    content: str
    type: str
    importance: float
    agent: str
    timestamp: str
    metadata: Dict[str, Any]

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    ensure_table_exists()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        conn = get_memory_connection()
        conn.close()
        return {"status": "healthy", "service": "memory-mcp", "version": "2.0.0"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.post("/memory/store", response_model=Dict[str, Any])
async def store_memory(entry: MemoryEntry):
    """Store a memory entry"""
    conn = get_memory_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("""
                INSERT INTO unified_memory (content, type, importance, agent, metadata)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, content, type, importance, agent, timestamp, metadata
            """, (entry.content, entry.type, entry.importance, entry.agent, entry.metadata))
            result = cursor.fetchone()
            conn.commit()
            return {
                "success": True,
                "memory_id": result['id'],
                "stored_at": result['timestamp'].isoformat()
            }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to store memory: {str(e)}")
    finally:
        conn.close()

@app.get("/memory/list", response_model=List[MemoryResponse])
async def list_memories(limit: int = 100, offset: int = 0):
    """List stored memories"""
    conn = get_memory_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, content, type, importance, agent, timestamp, metadata
                FROM unified_memory
                ORDER BY timestamp DESC
                LIMIT %s OFFSET %s
            """, (limit, offset))
            results = cursor.fetchall()
            
            memories = []
            for row in results:
                memories.append(MemoryResponse(
                    id=row['id'],
                    content=row['content'],
                    type=row['type'],
                    importance=row['importance'],
                    agent=row['agent'],
                    timestamp=row['timestamp'].isoformat(),
                    metadata=row['metadata'] or {}
                ))
            return memories
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list memories: {str(e)}")
    finally:
        conn.close()

@app.get("/memory/search")
async def search_memories(query: str, limit: int = 50):
    """Search memories by content"""
    conn = get_memory_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, content, type, importance, agent, timestamp, metadata
                FROM unified_memory
                WHERE content ILIKE %s
                ORDER BY importance DESC, timestamp DESC
                LIMIT %s
            """, (f"%{query}%", limit))
            results = cursor.fetchall()
            
            memories = []
            for row in results:
                memories.append(MemoryResponse(
                    id=row['id'],
                    content=row['content'],
                    type=row['type'],
                    importance=row['importance'],
                    agent=row['agent'],
                    timestamp=row['timestamp'].isoformat(),
                    metadata=row['metadata'] or {}
                ))
            return memories
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search memories: {str(e)}")
    finally:
        conn.close()

@app.delete("/memory/{memory_id}")
async def delete_memory(memory_id: int):
    """Delete a memory entry"""
    conn = get_memory_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM unified_memory WHERE id = %s", (memory_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Memory not found")
            conn.commit()
            return {"success": True, "message": f"Memory {memory_id} deleted"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete memory: {str(e)}")
    finally:
        conn.close()

@app.get("/memory/stats")
async def memory_stats():
    """Get memory statistics"""
    conn = get_memory_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_memories,
                    AVG(importance) as avg_importance,
                    COUNT(DISTINCT agent) as unique_agents,
                    COUNT(DISTINCT type) as unique_types
                FROM unified_memory
            """)
            stats = cursor.fetchone()
            return {
                "total_memories": stats['total_memories'],
                "average_importance": float(stats['avg_importance']) if stats['avg_importance'] else 0.0,
                "unique_agents": stats['unique_agents'],
                "unique_types": stats['unique_types']
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
