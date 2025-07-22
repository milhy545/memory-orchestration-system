#!/usr/bin/env python3
"""
Conversation Memory System for Zen MCP Server
Handles stateless-to-stateful conversation continuity with thread context management
"""
import json
import sqlite3
import uuid
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class ConversationTurn:
    """Represents a single conversation turn"""
    id: str
    tool_name: str
    request: Dict[str, Any]
    response: Dict[str, Any]
    timestamp: str
    token_count: int = 0
    files_referenced: List[str] = None
    
    def __post_init__(self):
        if self.files_referenced is None:
            self.files_referenced = []

@dataclass
class ThreadContext:
    """Represents a conversation thread context"""
    thread_id: str
    session_id: str
    created_at: str
    last_activity: str
    turns: List[ConversationTurn] = None
    total_tokens: int = 0
    expiry_time: str = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.turns is None:
            self.turns = []
        if self.metadata is None:
            self.metadata = {}

class ConversationMemoryManager:
    """Manages conversation threads and context continuity"""
    
    def __init__(self, db_path: str = "/home/milhy777/memory-orchestration-system/data/conversation_memory.db"):
        self.db_path = db_path
        self.memory_lock = threading.Lock()
        self.thread_cache = {}  # In-memory cache for active threads
        self.max_cache_size = 100
        self.thread_expiry_hours = 24
        
        # Initialize database
        self.init_database()
        
        # Cleanup expired threads periodically
        self.last_cleanup = time.time()
        self.cleanup_interval = 3600  # 1 hour
    
    def init_database(self):
        """Initialize conversation memory database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Threads table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_threads (
                    thread_id TEXT PRIMARY KEY,
                    session_id TEXT,
                    created_at TEXT NOT NULL,
                    last_activity TEXT NOT NULL,
                    expiry_time TEXT NOT NULL,
                    total_tokens INTEGER DEFAULT 0,
                    metadata TEXT DEFAULT '{}'
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_id ON conversation_threads(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_last_activity ON conversation_threads(last_activity)')
            
            # Turns table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_turns (
                    turn_id TEXT PRIMARY KEY,
                    thread_id TEXT,
                    tool_name TEXT NOT NULL,
                    request TEXT NOT NULL,
                    response TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    token_count INTEGER DEFAULT 0,
                    files_referenced TEXT DEFAULT '[]',
                    FOREIGN KEY (thread_id) REFERENCES conversation_threads (thread_id)
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_thread_id ON conversation_turns(thread_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON conversation_turns(timestamp)')
            
            conn.commit()
    
    def create_thread(self, session_id: str = None) -> str:
        """Create a new conversation thread"""
        thread_id = str(uuid.uuid4())
        session_id = session_id or f"session_{int(time.time())}"
        
        now = datetime.now().isoformat()
        expiry = (datetime.now() + timedelta(hours=self.thread_expiry_hours)).isoformat()
        
        thread = ThreadContext(
            thread_id=thread_id,
            session_id=session_id,
            created_at=now,
            last_activity=now,
            expiry_time=expiry
        )
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO conversation_threads 
                (thread_id, session_id, created_at, last_activity, expiry_time, total_tokens, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (thread_id, session_id, now, now, expiry, 0, json.dumps({})))
            conn.commit()
        
        # Cache the thread
        with self.memory_lock:
            self.thread_cache[thread_id] = thread
            self._manage_cache_size()
        
        logger.info(f"Created new conversation thread: {thread_id}")
        return thread_id
    
    def add_turn(self, thread_id: str, tool_name: str, request: Dict[str, Any], 
                 response: Dict[str, Any], token_count: int = 0, 
                 files_referenced: List[str] = None) -> str:
        """Add a conversation turn to a thread"""
        if files_referenced is None:
            files_referenced = []
        
        turn_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        turn = ConversationTurn(
            id=turn_id,
            tool_name=tool_name,
            request=request,
            response=response,
            timestamp=timestamp,
            token_count=token_count,
            files_referenced=files_referenced
        )
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Insert turn
            cursor.execute('''
                INSERT INTO conversation_turns 
                (turn_id, thread_id, tool_name, request, response, timestamp, token_count, files_referenced)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                turn_id, thread_id, tool_name, 
                json.dumps(request), json.dumps(response), 
                timestamp, token_count, json.dumps(files_referenced)
            ))
            
            # Update thread activity and token count
            cursor.execute('''
                UPDATE conversation_threads 
                SET last_activity = ?, total_tokens = total_tokens + ?
                WHERE thread_id = ?
            ''', (timestamp, token_count, thread_id))
            
            conn.commit()
        
        # Update cache
        with self.memory_lock:
            if thread_id in self.thread_cache:
                thread = self.thread_cache[thread_id]
                thread.turns.append(turn)
                thread.last_activity = timestamp
                thread.total_tokens += token_count
        
        logger.debug(f"Added turn {turn_id} to thread {thread_id}")
        return turn_id
    
    def get_thread(self, thread_id: str) -> Optional[ThreadContext]:
        """Retrieve a conversation thread with all turns"""
        # Check cache first
        with self.memory_lock:
            if thread_id in self.thread_cache:
                thread = self.thread_cache[thread_id]
                # Check if expired
                if datetime.fromisoformat(thread.expiry_time) > datetime.now():
                    return thread
                else:
                    # Remove expired thread from cache
                    del self.thread_cache[thread_id]
        
        # Load from database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get thread info
            cursor.execute('''
                SELECT thread_id, session_id, created_at, last_activity, 
                       expiry_time, total_tokens, metadata
                FROM conversation_threads 
                WHERE thread_id = ? AND datetime(expiry_time) > datetime('now')
            ''', (thread_id,))
            
            thread_row = cursor.fetchone()
            if not thread_row:
                logger.warning(f"Thread {thread_id} not found or expired")
                return None
            
            # Get turns
            cursor.execute('''
                SELECT turn_id, tool_name, request, response, timestamp, 
                       token_count, files_referenced
                FROM conversation_turns 
                WHERE thread_id = ?
                ORDER BY timestamp ASC
            ''', (thread_id,))
            
            turn_rows = cursor.fetchall()
            
        # Build thread object
        turns = []
        for row in turn_rows:
            turn = ConversationTurn(
                id=row[0],
                tool_name=row[1],
                request=json.loads(row[2]),
                response=json.loads(row[3]),
                timestamp=row[4],
                token_count=row[5],
                files_referenced=json.loads(row[6])
            )
            turns.append(turn)
        
        thread = ThreadContext(
            thread_id=thread_row[0],
            session_id=thread_row[1],
            created_at=thread_row[2],
            last_activity=thread_row[3],
            expiry_time=thread_row[4],
            total_tokens=thread_row[5],
            metadata=json.loads(thread_row[6]),
            turns=turns
        )
        
        # Cache the thread
        with self.memory_lock:
            self.thread_cache[thread_id] = thread
            self._manage_cache_size()
        
        return thread
    
    def build_conversation_history(self, context: ThreadContext, 
                                  model_context: Dict[str, Any]) -> Tuple[str, int]:
        """Build conversation history with intelligent prioritization"""
        if not context or not context.turns:
            return "", 0
        
        # Token budget management
        max_tokens = model_context.get("max_context_tokens", 8000)
        reserved_tokens = model_context.get("reserved_response_tokens", 1000)
        available_tokens = max_tokens - reserved_tokens
        
        # Build history with prioritization
        history_parts = []
        total_tokens = 0
        
        # Process turns chronologically for presentation
        turns_to_include = []
        
        # First pass: collect turns within token budget (newest first for priority)
        for turn in reversed(context.turns):
            estimated_tokens = len(json.dumps({
                "tool": turn.tool_name,
                "request": turn.request,
                "response": turn.response
            })) // 4  # Rough token estimation
            
            if total_tokens + estimated_tokens <= available_tokens:
                turns_to_include.insert(0, turn)  # Insert at beginning for chronological order
                total_tokens += estimated_tokens
            else:
                break
        
        # Second pass: build formatted history
        for i, turn in enumerate(turns_to_include):
            # Format turn for context
            turn_context = f"## Turn {i+1} - {turn.tool_name} ({turn.timestamp})\n"
            
            # Add request context
            if turn.request:
                # Extract key information from request
                request_summary = self._summarize_request(turn.request)
                turn_context += f"**Request:** {request_summary}\n"
            
            # Add response context
            if turn.response:
                response_summary = self._summarize_response(turn.response)
                turn_context += f"**Response:** {response_summary}\n"
            
            # Add file references
            if turn.files_referenced:
                turn_context += f"**Files:** {', '.join(turn.files_referenced)}\n"
            
            turn_context += "\n"
            history_parts.append(turn_context)
        
        # Combine into final history
        if history_parts:
            conversation_history = "# Conversation History\n\n" + "".join(history_parts)
        else:
            conversation_history = ""
        
        return conversation_history, total_tokens
    
    def _summarize_request(self, request: Dict[str, Any]) -> str:
        """Summarize request for context"""
        if isinstance(request, dict):
            # Extract key fields
            summary_parts = []
            
            if "query" in request:
                summary_parts.append(f"Query: {request['query'][:100]}...")
            elif "message" in request:
                summary_parts.append(f"Message: {request['message'][:100]}...")
            elif "prompt" in request:
                summary_parts.append(f"Prompt: {request['prompt'][:100]}...")
            elif "file_path" in request:
                summary_parts.append(f"File: {request['file_path']}")
            
            # Add other relevant fields
            for key in ["task", "action", "type", "mode"]:
                if key in request:
                    summary_parts.append(f"{key.title()}: {request[key]}")
            
            return "; ".join(summary_parts) if summary_parts else "Request details"
        
        return str(request)[:100] + "..." if len(str(request)) > 100 else str(request)
    
    def _summarize_response(self, response: Dict[str, Any]) -> str:
        """Summarize response for context"""
        if isinstance(response, dict):
            if "content" in response:
                content = response["content"]
                if isinstance(content, list) and content:
                    # MCP response format
                    text_content = content[0].get("text", "") if content[0].get("type") == "text" else ""
                    return text_content[:200] + "..." if len(text_content) > 200 else text_content
                elif isinstance(content, str):
                    return content[:200] + "..." if len(content) > 200 else content
            
            if "result" in response:
                result = str(response["result"])
                return result[:200] + "..." if len(result) > 200 else result
            
            if "message" in response:
                return response["message"][:200] + "..." if len(response["message"]) > 200 else response["message"]
        
        return str(response)[:200] + "..." if len(str(response)) > 200 else str(response)
    
    def _manage_cache_size(self):
        """Manage in-memory cache size"""
        if len(self.thread_cache) > self.max_cache_size:
            # Remove oldest threads from cache
            sorted_threads = sorted(
                self.thread_cache.items(),
                key=lambda x: x[1].last_activity
            )
            
            # Remove oldest 10%
            to_remove = len(sorted_threads) // 10
            for i in range(to_remove):
                thread_id, _ = sorted_threads[i]
                del self.thread_cache[thread_id]
    
    def cleanup_expired_threads(self):
        """Clean up expired threads from database"""
        current_time = time.time()
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Delete expired threads and their turns
            cursor.execute('''
                DELETE FROM conversation_turns 
                WHERE thread_id IN (
                    SELECT thread_id FROM conversation_threads 
                    WHERE datetime(expiry_time) <= datetime('now')
                )
            ''')
            
            cursor.execute('''
                DELETE FROM conversation_threads 
                WHERE datetime(expiry_time) <= datetime('now')
            ''')
            
            deleted_count = cursor.rowcount
            conn.commit()
        
        # Clean up cache
        with self.memory_lock:
            expired_threads = []
            now = datetime.now()
            for thread_id, thread in self.thread_cache.items():
                if datetime.fromisoformat(thread.expiry_time) <= now:
                    expired_threads.append(thread_id)
            
            for thread_id in expired_threads:
                del self.thread_cache[thread_id]
        
        self.last_cleanup = current_time
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} expired conversation threads")
    
    def get_thread_stats(self) -> Dict[str, Any]:
        """Get conversation memory statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Thread stats
            cursor.execute('SELECT COUNT(*) FROM conversation_threads')
            total_threads = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM conversation_threads 
                WHERE datetime(expiry_time) > datetime('now')
            ''')
            active_threads = cursor.fetchone()[0]
            
            # Turn stats
            cursor.execute('SELECT COUNT(*) FROM conversation_turns')
            total_turns = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(token_count) FROM conversation_turns WHERE token_count > 0')
            avg_tokens = cursor.fetchone()[0] or 0
        
        return {
            "total_threads": total_threads,
            "active_threads": active_threads,
            "cached_threads": len(self.thread_cache),
            "total_turns": total_turns,
            "average_tokens_per_turn": round(avg_tokens, 2),
            "cache_size": len(self.thread_cache),
            "database_path": self.db_path
        }

# Global instance
_manager = None

def get_manager() -> ConversationMemoryManager:
    """Get global conversation memory manager instance"""
    global _manager
    if _manager is None:
        _manager = ConversationMemoryManager()
    return _manager

# Convenience functions that match the expected API
def create_thread(session_id: str = None) -> str:
    """Create a new conversation thread"""
    return get_manager().create_thread(session_id)

def add_turn(thread_id: str, tool_name: str, request: Dict[str, Any], 
             response: Dict[str, Any], token_count: int = 0, 
             files_referenced: List[str] = None) -> str:
    """Add a conversation turn to a thread"""
    return get_manager().add_turn(thread_id, tool_name, request, response, 
                                 token_count, files_referenced)

def get_thread(thread_id: str) -> Optional[ThreadContext]:
    """Retrieve a conversation thread with all turns"""
    return get_manager().get_thread(thread_id)

def build_conversation_history(context: ThreadContext, 
                              model_context: Dict[str, Any]) -> Tuple[str, int]:
    """Build conversation history with intelligent prioritization"""
    return get_manager().build_conversation_history(context, model_context)

def cleanup_expired_threads():
    """Clean up expired threads"""
    get_manager().cleanup_expired_threads()

def get_thread_stats() -> Dict[str, Any]:
    """Get conversation memory statistics"""
    return get_manager().get_thread_stats()

if __name__ == "__main__":
    # Test the conversation memory system
    print("🧠 Testing Conversation Memory System")
    
    # Create a test thread
    thread_id = create_thread("test_session")
    print(f"Created thread: {thread_id}")
    
    # Add some test turns
    add_turn(thread_id, "chat", 
            {"message": "Hello, how are you?"}, 
            {"content": [{"type": "text", "text": "I'm doing well, thank you!"}]},
            token_count=25)
    
    add_turn(thread_id, "analyze", 
            {"file_path": "/test/file.py", "task": "review code"}, 
            {"content": [{"type": "text", "text": "Code analysis complete. Found 3 issues."}]},
            token_count=150,
            files_referenced=["/test/file.py"])
    
    # Retrieve and test
    thread = get_thread(thread_id)
    if thread:
        print(f"Thread has {len(thread.turns)} turns")
        
        # Build conversation history
        model_context = {"max_context_tokens": 8000, "reserved_response_tokens": 1000}
        history, tokens = build_conversation_history(thread, model_context)
        print(f"History built: {tokens} tokens")
        print("History preview:", history[:200] + "...")
    
    # Show stats
    stats = get_thread_stats()
    print("Stats:", stats)
    
    print("✅ Conversation Memory System test completed")