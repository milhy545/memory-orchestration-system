# 🚨 KRITICKÁ DATABASE MIGRACE - BEZPEČNOSTNÍ PLÁN

## 📊 **AKTUÁLNÍ SITUACE:**

### **🗂️ ZJIŠTĚNÁ FOLDER STRUKTURA:**
```
/home/milhy777/memory-orchestration-system/
├── data/ (nově vytvořeno)
├── utils/conversation_memory.py ✅
├── bash_history_tracker.py ✅  
├── cldmemory_simple.py ✅
└── (všechny MCP servery) ✅
```

### **💾 DATABÁZE V /tmp/ (DOČASNÉ!):**
```
/tmp/cldmemory.db              1.5MB ⚠️ HLAVNÍ MEMORY!
/tmp/conversation_memory.db    48KB  ⚠️ KONVERZACE!
/tmp/bash_tracker.db          24KB  ⚠️ BASH HISTORIE!
/tmp/unified_memory_forai.db  20KB  ⚠️ FORAI TRACKING!
/tmp/claude_session_memory.db 16KB  ⚠️ SESSION DATA!
```

## 🛡️ **BEZPEČNÁ MIGRACE - KROK ZA KROKEM:**

### **KROK 1: BACKUP SOUČASNÝCH DAT**
```bash
# Vytvořit kompletní backup
tar -czf /home/milhy777/database_backup_$(date +%Y%m%d_%H%M%S).tar.gz /tmp/*.db

# Ověřit backup
tar -tzf /home/milhy777/database_backup_*.tar.gz | wc -l
```

### **KROK 2: ANALÝZA OBSAHU DATABÁZÍ**
```bash
# Zkontrolovat velikost a obsah
sqlite3 /tmp/cldmemory.db "SELECT COUNT(*) FROM memories;"
sqlite3 /tmp/conversation_memory.db "SELECT COUNT(*) FROM conversation_threads;"
sqlite3 /tmp/bash_tracker.db "SELECT COUNT(*) FROM bash_commands;"
```

### **KROK 3: PŘESUN DO PROJEKTU**
```bash
# Přesunout databáze do správné lokace
cp /tmp/cldmemory.db /home/milhy777/memory-orchestration-system/data/
cp /tmp/conversation_memory.db /home/milhy777/memory-orchestration-system/data/
cp /tmp/bash_tracker.db /home/milhy777/memory-orchestration-system/data/
cp /tmp/unified_memory_forai.db /home/milhy777/memory-orchestration-system/data/
```

### **KROK 4: AKTUALIZACE CONFIG PATHS**
- `utils/conversation_memory.py` - řádek 55
- `bash_history_tracker.py` - řádek 17  
- `cldmemory_simple.py` - config path
- Auto trackers paths

### **KROK 5: TESTOVÁNÍ INTEGRITY**
```bash
# Ověřit že vše funguje
python3 utils/conversation_memory.py
python3 bash_history_tracker.py --test
```

## ⚠️ **RIZIKA A PREVENCE:**

### **🚨 CO MŮŽE SELHAT:**
- Path konflikty v kódu
- Permission problémy  
- Database corruption při přesunu
- Služby pointing na staré lokace

### **🛡️ PREVENCE:**
1. **Kompletní backup PŘED** jakoukoliv změnou
2. **Postupný přesun** - jeden soubor po druhém
3. **Testování** po každém kroku
4. **Rollback plán** připravený

## 📋 **CHECKLIST PRO BEZPEČNOU MIGRACI:**

- [ ] Backup všech /tmp/*.db souborů
- [ ] Vytvoření /data/ adresáře  
- [ ] Analýza obsahu databází
- [ ] Postupný přesun databází
- [ ] Aktualizace config paths
- [ ] Test každé komponenty
- [ ] Ověření integrity dat
- [ ] Cleanup /tmp/ souborů

**POKRAČOVAT JEN KDYŽ MÁME BACKUP A ROLLBACK PLÁN!** 🛡️