#\!/bin/bash
# Orchestration Service Monitor
curl -s http://localhost:8020/health > /home/orchestration/monitoring/status/zen_coordinator.json
curl -s http://localhost:8007/health > /home/orchestration/monitoring/status/memory_mcp.json
docker ps --format "{{.Names}},{{.Status}}" | grep mcp > /home/orchestration/monitoring/status/containers.csv
echo "Monitoring updated: $(date)" > /home/orchestration/monitoring/status/last_update.txt
