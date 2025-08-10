#\!/bin/bash
# Backup script for orchestrace databases
DATE=$(date +%Y%m%d_%H%M)

# Backup from original /tmp location to orchestrace
cp /tmp/unified_memory_forai.db /home/orchestration/data/backups/unified_memory_forai_${DATE}.db
cp /tmp/cldmemory.db /home/orchestration/data/backups/cldmemory_${DATE}.db

# Also backup the copy in databases folder  
cp /home/orchestration/data/databases/unified_memory_forai.db /home/orchestration/data/backups/unified_memory_forai_persistent_${DATE}.db
cp /home/orchestration/data/databases/cldmemory.db /home/orchestration/data/backups/cldmemory_persistent_${DATE}.db

echo "Databases backed up at $(date)"
ls -la /home/orchestration/data/backups/
