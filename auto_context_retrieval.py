#!/usr/bin/env python3
"""
Auto-Context Retrieval System
Automatically loads relevant context based on user queries
"""
import re
import json
from typing import Dict, List, Optional, Tuple
from utils.conversation_memory import get_manager, get_thread_stats
import requests
import sqlite3

class AutoContextRetrieval:
    def __init__(self):
        self.cldmemory_url = "http://192.168.0.58:8007"
        self.context_threshold = 0.7
        self.max_context_items = 5
        
    def analyze_user_query(self, query: str) -> Dict[str, any]:
        """Analyze user query for context keywords"""
        keywords = {
            'docker': ['docker', 'container', 'image', 'compose'],
            'git': ['git', 'github', 'repo', 'commit', 'push', 'pull'],
            'python': ['python', 'pip', 'script', 'code', 'function'],
            'system': ['system', 'service', 'daemon', 'process'],
            'memory': ['memory', 'paměť', 'uložit', 'najdi', 'hledej']
        }
        
        detected_contexts = []
        for context, terms in keywords.items():
            if any(term in query.lower() for term in terms):
                detected_contexts.append(context)
        
        return {
            'contexts': detected_contexts,
            'needs_memory_search': any(term in query.lower() for term in 
                ['najdi', 'hledej', 'pamatuj', 'předchozí', 'dříve']),
            'complexity': len(query.split())
        }
    
    def search_memory(self, query: str, limit: int = 3) -> List[Dict]:
        """Search semantic memory for relevant context"""
        try:
            response = requests.post(f"{self.cldmemory_url}/search", 
                json={"query": query, "limit": limit}, timeout=5)
            if response.status_code == 200:
                return response.json().get('results', [])
        except:
            pass
        return []
    
    def get_conversation_context(self, query: str) -> List[Dict]:
        """Get relevant conversation history"""
        memory_manager = get_manager()
        
        # Simple keyword matching in conversation DB
        with sqlite3.connect('/tmp/conversation_memory.db') as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT tool_name, request, response, timestamp 
                FROM conversation_turns 
                WHERE request LIKE ? OR response LIKE ?
                ORDER BY timestamp DESC LIMIT 3
            """, (f"%{query[:20]}%", f"%{query[:20]}%"))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'tool': row[0],
                    'request': json.loads(row[1]) if row[1] else {},
                    'response': json.loads(row[2]) if row[2] else {},
                    'timestamp': row[3]
                })
            return results
    
    def build_auto_context(self, user_query: str) -> str:
        """Build automatic context for Claude"""
        analysis = self.analyze_user_query(user_query)
        
        if not analysis['needs_memory_search'] and analysis['complexity'] < 5:
            return ""  # Simple query, no context needed
        
        context_parts = ["# 🧠 AUTO-LOADED CONTEXT:\n"]
        
        # Memory search
        if analysis['needs_memory_search']:
            memory_results = self.search_memory(user_query)
            if memory_results:
                context_parts.append("## 📚 Relevant Memory:")
                for result in memory_results[:2]:
                    context_parts.append(f"- {result.get('content', '')[:100]}...")
        
        # Conversation history
        conv_results = self.get_conversation_context(user_query)
        if conv_results:
            context_parts.append("\n## 💬 Recent Related Work:")
            for result in conv_results[:2]:
                tool = result['tool']
                context_parts.append(f"- {tool}: {str(result['request'])[:80]}...")
        
        return "\n".join(context_parts) if len(context_parts) > 1 else ""

# Test function
def test_auto_context():
    retriever = AutoContextRetrieval()
    
    test_queries = [
        "Spusť Docker container",
        "Najdi ten Python kód co jsme dělali včera", 
        "ls",  # Simple query
        "Pokračuj v práci na MCP serverech"
    ]
    
    for query in test_queries:
        print(f"Query: {query}")
        context = retriever.build_auto_context(query)
        print(f"Context: {len(context)} chars")
        print("---")

if __name__ == "__main__":
    test_auto_context()