#!/usr/bin/env python3
"""
Unified Memory + FORAI Daemon
Combines memory tracking with automatic FORAI injection
"""
import os
import sys
import time
import sqlite3
import json
import subprocess
import ast
from datetime import datetime
from pathlib import Path
import hashlib

class UnifiedMemoryFORAI:
    def __init__(self, db_path="/tmp/unified_memory_forai.db"):
        self.db_path = db_path
        self.init_database()
        self.session_id = self.generate_session_id()
        
    def init_database(self):
        """Initialize unified database with memory + FORAI tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Memory table (existing)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                type TEXT DEFAULT 'forai_auto',
                importance REAL DEFAULT 0.5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                embedding BLOB,
                session_id TEXT,
                agent TEXT DEFAULT 'claude-code'
            )
        ''')
        
        # FORAI tracking table (new)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS forai_injections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                action TEXT NOT NULL,
                agent TEXT NOT NULL,
                session_id TEXT NOT NULL,
                context TEXT,
                file_hash_before TEXT,
                file_hash_after TEXT,
                syntax_valid BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Auto-test results table (new)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auto_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                test_type TEXT NOT NULL,
                result BOOLEAN NOT NULL,
                error_message TEXT,
                forai_injection_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (forai_injection_id) REFERENCES forai_injections (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def generate_session_id(self):
        """Generate unique session ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"unified_{timestamp}_{os.getpid()}"
    
    def compute_file_hash(self, file_path):
        """Compute file hash for change detection"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return None
    
    def generate_forai_header(self, file_path, context="Auto-generated", agent="claude-code"):
        """Generate FORAI header based on file type"""
        timestamp = datetime.now().isoformat()
        file_ext = Path(file_path).suffix.lower()
        
        # Comment styles by file extension  
        comment_styles = {
            '.py': '#',
            '.js': '//',
            '.css': '/*',
            '.html': '<!--',
            '.md': '<!--',
            '.sh': '#',
            '.sql': '--',
            '.yml': '#',
            '.yaml': '#'
        }
        
        comment_char = comment_styles.get(file_ext, '#')
        
        header_lines = [
            f" FORAI Analytics Headers - {timestamp}",
            f" Agent: {agent}",
            f" Session: {self.session_id}",
            f" Context: {context}",
            f" File: {os.path.basename(file_path)}",
            f" Auto-tracking: Enabled",
            f" Memory-integrated: True"
        ]
        
        if comment_char == '/*':
            return '/*\n' + '\n'.join(f' *{line}' for line in header_lines) + '\n */\n\n'
        elif comment_char == '<!--':
            return '<!--\n' + '\n'.join(f'  {line}' for line in header_lines) + '\n-->\n\n'
        else:
            return '\n'.join(f'{comment_char}{line}' for line in header_lines) + '\n\n'
    
    def inject_forai_to_file(self, file_path, context="File modification", agent="claude-code"):
        """Inject FORAI headers and track in database"""
        
        # Compute hash before modification
        hash_before = self.compute_file_hash(file_path)
        
        try:
            # Read existing content
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Check if FORAI already present
            if 'FORAI Analytics Headers' in original_content:
                print(f"⚠️  FORAI already present in {file_path}")
                return False
            
            # Generate and inject FORAI header
            forai_header = self.generate_forai_header(file_path, context, agent)
            new_content = forai_header + original_content
            
            # Write back with FORAI
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            # Compute hash after modification
            hash_after = self.compute_file_hash(file_path)
            
            # Test syntax validity
            syntax_valid = self.test_file_syntax(file_path)
            
            # Record in database
            forai_id = self.record_forai_injection(
                file_path, "header_injection", agent, context,
                hash_before, hash_after, syntax_valid
            )
            
            # Store in memory database
            self.store_memory(
                f"FORAI injected into {file_path} - {context}",
                f"forai,file_modification,{agent}",
                0.6
            )
            
            print(f"✅ FORAI injected into {file_path} (ID: {forai_id})")
            return forai_id
            
        except Exception as e:
            print(f"❌ Error injecting FORAI into {file_path}: {e}")
            return False
    
    def test_file_syntax(self, file_path):
        """Test if file has valid syntax after FORAI injection"""
        file_ext = Path(file_path).suffix.lower()
        
        try:
            if file_ext == '.py':
                # Python syntax check
                with open(file_path, 'r') as f:
                    ast.parse(f.read())
                return True
                
            elif file_ext == '.js':
                # JavaScript syntax check (requires node)
                result = subprocess.run(
                    ['node', '-c', file_path], 
                    capture_output=True, 
                    timeout=5
                )
                return result.returncode == 0
                
            elif file_ext == '.json':
                # JSON syntax check
                with open(file_path, 'r') as f:
                    json.load(f)
                return True
                
            # For other file types, assume valid
            return True
            
        except Exception as e:
            print(f"⚠️  Syntax check failed for {file_path}: {e}")
            return False
    
    def record_forai_injection(self, file_path, action, agent, context, hash_before, hash_after, syntax_valid):
        """Record FORAI injection in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO forai_injections 
            (file_path, action, agent, session_id, context, file_hash_before, file_hash_after, syntax_valid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (file_path, action, agent, self.session_id, context, hash_before, hash_after, syntax_valid))
        
        forai_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return forai_id
    
    def store_memory(self, content, tags="", importance=0.5):
        """Store in memory database (simplified version)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO memories (content, type, importance, session_id, agent)
            VALUES (?, ?, ?, ?, ?)
        ''', (content, "forai_auto", importance, self.session_id, "unified_system"))
        
        conn.commit()
        conn.close()
    
    def run_auto_tests(self, file_path, forai_injection_id):
        """Run comprehensive auto-tests after FORAI injection"""
        tests = []
        
        # Test 1: Syntax validity
        syntax_valid = self.test_file_syntax(file_path)
        tests.append(("syntax_check", syntax_valid, None if syntax_valid else "Syntax error detected"))
        
        # Test 2: File size check (ensure not too large)
        try:
            file_size = os.path.getsize(file_path)
            size_ok = file_size < 1000000  # 1MB limit
            tests.append(("size_check", size_ok, None if size_ok else f"File too large: {file_size} bytes"))
        except:
            tests.append(("size_check", False, "Could not check file size"))
        
        # Test 3: Encoding check
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read()
            tests.append(("encoding_check", True, None))
        except UnicodeDecodeError:
            tests.append(("encoding_check", False, "UTF-8 encoding error"))
        
        # Record test results
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for test_type, result, error_msg in tests:
            cursor.execute('''
                INSERT INTO auto_tests (file_path, test_type, result, error_message, forai_injection_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (file_path, test_type, result, error_msg, forai_injection_id))
        
        conn.commit()
        conn.close()
        
        # Summary
        passed = sum(1 for _, result, _ in tests if result)
        total = len(tests)
        
        print(f"🧪 Auto-tests: {passed}/{total} passed")
        
        if passed == total:
            print("✅ All tests passed!")
        else:
            print("⚠️  Some tests failed - check auto_tests table")
            
        return passed == total
    
    def process_file_with_full_pipeline(self, file_path, context="Auto-processing"):
        """Complete pipeline: FORAI injection + testing + memory storage"""
        print(f"\n🔄 Processing {file_path}...")
        
        # Step 1: Inject FORAI
        forai_id = self.inject_forai_to_file(file_path, context)
        
        if not forai_id:
            print("❌ FORAI injection failed")
            return False
        
        # Step 2: Run auto-tests
        tests_passed = self.run_auto_tests(file_path, forai_id)
        
        # Step 3: Update memory with results
        self.store_memory(
            f"Processed {file_path} - FORAI ID: {forai_id}, Tests: {'✅' if tests_passed else '❌'}",
            f"file_processing,forai_injection,auto_test",
            0.8 if tests_passed else 0.4
        )
        
        print(f"✅ Complete pipeline finished for {file_path}")
        return True
    
    def get_statistics(self):
        """Get system statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # FORAI injections count
        cursor.execute("SELECT COUNT(*) FROM forai_injections")
        forai_count = cursor.fetchone()[0]
        
        # Memory entries count  
        cursor.execute("SELECT COUNT(*) FROM memories")
        memory_count = cursor.fetchone()[0]
        
        # Auto-tests count
        cursor.execute("SELECT COUNT(*) FROM auto_tests WHERE result = 1")
        tests_passed = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM auto_tests")
        tests_total = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "forai_injections": forai_count,
            "memory_entries": memory_count,
            "tests_passed": tests_passed,
            "tests_total": tests_total,
            "session_id": self.session_id
        }

# Demo usage
if __name__ == "__main__":
    print("🚀 UNIFIED MEMORY + FORAI DAEMON")
    print("=" * 50)
    
    daemon = UnifiedMemoryFORAI()
    
    # Demo file processing
    demo_file = "/home/milhy777/library_demo/unified_demo.py"
    
    # Create demo file
    with open(demo_file, 'w') as f:
        f.write('''def hello_unified():
    """Demo function for unified system"""
    return "Hello from Unified Memory + FORAI!"

if __name__ == "__main__":
    print(hello_unified())
''')
    
    # Process with full pipeline
    daemon.process_file_with_full_pipeline(
        demo_file, 
        "Demo of unified memory + FORAI system"
    )
    
    # Show statistics
    stats = daemon.get_statistics()
    print("\n📊 SYSTEM STATISTICS:")
    print(f"   FORAI Injections: {stats['forai_injections']}")
    print(f"   Memory Entries: {stats['memory_entries']}")
    print(f"   Tests Passed: {stats['tests_passed']}/{stats['tests_total']}")
    print(f"   Session ID: {stats['session_id']}")
    
    print("\n🎯 UNIFIED SYSTEM READY!")
    print("✅ FORAI injection")
    print("✅ Auto-testing") 
    print("✅ Memory integration")
    print("✅ Database tracking")
    print("✅ No duplicity")