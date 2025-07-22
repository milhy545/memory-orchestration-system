#!/bin/bash
# Complete Memory Stack Startup
echo "🚀 Starting Complete Memory Stack..."

# 1. Start CLDMEMORY HTTP service on 8006
echo "Starting CLDMEMORY on port 8006..."
cd /home/milhy777
python3 -c "
import sys
import http.server
import socketserver
import json
from cldmemory_simple import SimpleCLDMemory

class MemoryHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.memory = SimpleCLDMemory()
        super().__init__(*args, **kwargs)
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            
            if data.get('action') == 'store':
                result = self.memory.store_memory(
                    data.get('content', ''),
                    data.get('type', 'api'),
                    data.get('importance', 0.5)
                )
                response = {'success': True, 'memory_id': result}
            
            elif data.get('action') == 'search':
                results = self.memory.search_memories(
                    data.get('query', ''),
                    data.get('limit', 5)
                )
                response = {'success': True, 'results': results}
            
            else:
                response = {'success': True, 'status': 'CLDMEMORY API Ready', 'embeddings': 'Gemini'}
                
        except Exception as e:
            response = {'success': False, 'error': str(e)}
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

with socketserver.TCPServer(('0.0.0.0', 8006), MemoryHandler) as httpd:
    print('CLDMEMORY API running on port 8006')
    httpd.serve_forever()
" > /tmp/cldmemory_server.log 2>&1 &

echo $! > /tmp/cldmemory.pid
echo "✅ CLDMEMORY started (PID: $(cat /tmp/cldmemory.pid))"

# 2. Start unified memory daemon locally
echo "Starting Unified Memory daemon..."
python3 /home/milhy777/unified_memory_forai_daemon.py &
echo $! > /tmp/unified_daemon.pid
echo "✅ Unified daemon started (PID: $(cat /tmp/unified_daemon.pid))"

sleep 3

echo "🎯 Memory Stack Status:"
echo "- CLDMEMORY: http://localhost:8006 (Gemini embeddings)"
echo "- Unified daemon: PID $(cat /tmp/unified_daemon.pid 2>/dev/null || echo 'FAILED')"
echo "- Qdrant: http://192.168.0.58:6333 (collections)"
echo "- Zen Coordinator: http://192.168.0.58:8020 (orchestration)"

echo "🧪 Running basic tests..."
curl -s -X POST "http://localhost:8006" -d '{"action":"store","content":"Test memory","importance":0.8}' || echo "CLDMEMORY test failed"
curl -s -X POST "http://192.168.0.58:8020/mcp" -d '{"tool":"store_memory","arguments":{"content":"Coordinator test"}}' || echo "Coordinator test failed"

echo "✅ Memory stack startup complete!"