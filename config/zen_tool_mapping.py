# Správné mapování MCP nástrojů pro ZEN Coordinator
TOOL_MAPPING = {
    # Filesystem tools - správné názvy
    'list_files': {'service': 'filesystem', 'tool': 'file_list', 'port': 8001},
    'read_file': {'service': 'filesystem', 'tool': 'file_read', 'port': 8001},
    'write_file': {'service': 'filesystem', 'tool': 'file_write', 'port': 8001},
    
    # Terminal tools - správné názvy  
    'execute_command': {'service': 'terminal', 'tool': 'terminal_exec', 'port': 8003},
    'shell_command': {'service': 'terminal', 'tool': 'shell_command', 'port': 8003},
    
    # Git tools - správné názvy
    'git_execute': {'service': 'git', 'tool': 'git_status', 'port': 8002},
    'git_status': {'service': 'git', 'tool': 'git_status', 'port': 8002},
    
    # Memory tools - fungující
    'search_memories': {'service': 'memory', 'tool': 'search_memories', 'port': 8006},
    'store_memory': {'service': 'memory', 'tool': 'store_memory', 'port': 8006},
}
