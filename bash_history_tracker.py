#!/usr/bin/env python3
"""
Bash History Tracker for Memory Orchestration System
Automatically tracks bash history and integrates with conversation memory
"""
import os
import time
import json
import sqlite3
import threading
import hashlib
from datetime import datetime
from pathlib import Path
from utils.conversation_memory import get_manager, create_thread, add_turn

class BashHistoryTracker:
    """Tracks bash history and integrates with conversation memory"""
    
    def __init__(self):
        self.bash_history_path = os.path.expanduser("~/.bash_history")
        self.tracker_db = "/home/milhy777/memory-orchestration-system/data/bash_tracker.db"
        self.last_known_size = 0
        self.running = True
        self.session_thread_id = None
        
        # Initialize tracker database
        self.init_tracker_db()
        
        # Get current history size
        self.update_history_size()
        
        # Create conversation thread for this session
        self.session_thread_id = create_thread(f"bash_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        print(f"🎯 Bash History Tracker initialized")
        print(f"📁 History file: {self.bash_history_path}")
        print(f"💾 Tracker DB: {self.tracker_db}")
        print(f"🧵 Session thread: {self.session_thread_id}")
    
    def init_tracker_db(self):
        """Initialize bash history tracking database"""
        with sqlite3.connect(self.tracker_db) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bash_commands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    command TEXT NOT NULL,
                    command_hash TEXT UNIQUE,
                    timestamp TEXT NOT NULL,
                    session_id TEXT,
                    context TEXT,
                    memory_stored INTEGER DEFAULT 0
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_command_hash ON bash_commands(command_hash)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON bash_commands(timestamp)')
            conn.commit()
    
    def update_history_size(self):
        """Update the known size of bash history"""
        if os.path.exists(self.bash_history_path):
            with open(self.bash_history_path, 'r', encoding='utf-8', errors='ignore') as f:
                self.last_known_size = sum(1 for _ in f)
        else:
            self.last_known_size = 0
    
    def get_command_hash(self, command):
        """Generate hash for command deduplication"""
        return hashlib.md5(command.encode()).hexdigest()
    
    def check_for_new_commands(self):
        """Check for new commands in bash history"""
        if not os.path.exists(self.bash_history_path):
            return []
        
        try:
            with open(self.bash_history_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                current_size = len(lines)
                
                if current_size > self.last_known_size:
                    # Get new commands
                    new_commands = lines[self.last_known_size:current_size]
                    self.last_known_size = current_size
                    
                    # Filter and clean commands
                    clean_commands = []
                    for cmd in new_commands:
                        cmd = cmd.strip()
                        if cmd and not cmd.startswith('#'):
                            clean_commands.append(cmd)
                    
                    return clean_commands
                    
        except Exception as e:
            print(f"Error reading bash history: {e}")
            
        return []
    
    def store_commands(self, commands):
        """Store new commands in tracker database and conversation memory"""
        if not commands:
            return
        
        timestamp = datetime.now().isoformat()
        session_id = self.session_thread_id
        
        stored_count = 0
        memory_stored_count = 0
        
        with sqlite3.connect(self.tracker_db) as conn:
            cursor = conn.cursor()
            
            for cmd in commands:
                cmd_hash = self.get_command_hash(cmd)
                
                # Check if command already exists
                cursor.execute('SELECT id FROM bash_commands WHERE command_hash = ?', (cmd_hash,))
                if cursor.fetchone():
                    continue  # Skip duplicate
                
                # Store in tracker DB
                cursor.execute('''
                    INSERT INTO bash_commands (command, command_hash, timestamp, session_id)
                    VALUES (?, ?, ?, ?)
                ''', (cmd, cmd_hash, timestamp, session_id))
                stored_count += 1
                
                # Store in conversation memory if interesting
                if self.is_interesting_command(cmd):
                    try:
                        add_turn(
                            self.session_thread_id,
                            'bash_command',
                            {'command': cmd, 'timestamp': timestamp},
                            {'executed': True, 'tracked': True, 'hash': cmd_hash},
                            token_count=len(cmd) // 4 + 10  # Rough token estimate
                        )
                        memory_stored_count += 1
                    except Exception as e:
                        print(f"Error storing in conversation memory: {e}")
            
            conn.commit()
        
        if stored_count > 0:
            print(f"📝 Stored {stored_count} new commands ({memory_stored_count} in conversation memory)")
    
    def is_interesting_command(self, command):
        """Determine if a command is interesting enough to store in conversation memory"""
        # Skip very short commands
        if len(command) < 3:
            return False
        
        # Skip basic navigation
        basic_commands = ['ls', 'cd', 'pwd', 'clear', 'exit', 'history']
        cmd_start = command.split()[0] if command.split() else ''
        if cmd_start in basic_commands:
            return False
        
        # Include interesting patterns
        interesting_patterns = [
            'python', 'pip', 'npm', 'git', 'docker', 'sudo', 'systemctl',
            'grep', 'find', 'sed', 'awk', 'curl', 'wget', 'ssh', 'scp',
            'vi', 'nano', 'cat', 'head', 'tail', 'less', 'more',
            'chmod', 'chown', 'tar', 'zip', 'unzip', 'rsync',
            'ps', 'top', 'htop', 'kill', 'killall', 'nohup'
        ]
        
        return any(pattern in command.lower() for pattern in interesting_patterns)
    
    def start_monitoring(self):
        """Start monitoring bash history in background thread"""
        def monitor_loop():
            while self.running:
                try:
                    new_commands = self.check_for_new_commands()
                    if new_commands:
                        self.store_commands(new_commands)
                    time.sleep(2)  # Check every 2 seconds
                except Exception as e:
                    print(f"Error in monitor loop: {e}")
                    time.sleep(5)  # Wait longer on error
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("🔄 Bash history monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring bash history"""
        self.running = False
        print("⏹️ Bash history monitoring stopped")
    
    def get_statistics(self):
        """Get bash history tracking statistics"""
        with sqlite3.connect(self.tracker_db) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM bash_commands')
            total_commands = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM bash_commands WHERE memory_stored = 1')
            memory_stored = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM bash_commands 
                WHERE timestamp > datetime('now', '-1 hour')
            ''')
            recent_commands = cursor.fetchone()[0]
        
        return {
            'total_tracked_commands': total_commands,
            'memory_stored_commands': memory_stored,
            'recent_commands_1h': recent_commands,
            'session_thread_id': self.session_thread_id,
            'history_file_size': self.last_known_size,
            'tracker_db': self.tracker_db
        }
    
    def get_recent_commands(self, limit=10):
        """Get recent tracked commands"""
        with sqlite3.connect(self.tracker_db) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT command, timestamp FROM bash_commands 
                ORDER BY timestamp DESC LIMIT ?
            ''', (limit,))
            return cursor.fetchall()

def main():
    """Main function to run bash history tracker"""
    tracker = BashHistoryTracker()
    tracker.start_monitoring()
    
    try:
        # Keep running and show stats periodically
        while True:
            time.sleep(30)  # Show stats every 30 seconds
            stats = tracker.get_statistics()
            print(f"📊 Stats: {stats['total_tracked_commands']} tracked, {stats['memory_stored_commands']} in memory, {stats['recent_commands_1h']} recent")
            
    except KeyboardInterrupt:
        print("🛑 Stopping bash history tracker...")
        tracker.stop_monitoring()
        
        # Final statistics
        final_stats = tracker.get_statistics()
        print(f"📈 Final stats: {json.dumps(final_stats, indent=2)}")

if __name__ == "__main__":
    main()