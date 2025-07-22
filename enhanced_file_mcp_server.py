#!/usr/bin/env python3
"""
Enhanced File Operations MCP Server
Pokročilé operace se soubory: compression, encryption, monitoring, sync
"""
import json
import sys
import os
import shutil
import hashlib
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import stat
import time
import subprocess

# Optional imports
try:
    import zipfile
    import tarfile
    import gzip
    COMPRESSION_AVAILABLE = True
except ImportError:
    COMPRESSION_AVAILABLE = False

try:
    from cryptography.fernet import Fernet
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False

try:
    import watchdog
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False

class EnhancedFileMCPServer:
    def __init__(self):
        self.watchers = {}
        self.encryption_keys = {}
        
    def get_tools(self):
        """Return available enhanced file tools"""
        tools = [
            {
                "name": "file_analyze",
                "description": "Analyze file properties (size, type, permissions, hash)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to file to analyze"
                        },
                        "include_hash": {
                            "type": "boolean",
                            "default": True,
                            "description": "Calculate file hash (MD5, SHA256)"
                        },
                        "include_content_preview": {
                            "type": "boolean",
                            "default": False,
                            "description": "Include first few lines for text files"
                        }
                    },
                    "required": ["file_path"]
                }
            },
            {
                "name": "directory_scan",
                "description": "Recursive directory analysis with filters",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "directory_path": {
                            "type": "string",
                            "description": "Directory to scan"
                        },
                        "max_depth": {
                            "type": "number",
                            "default": 5,
                            "description": "Maximum recursion depth"
                        },
                        "file_extensions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by file extensions (e.g., ['.py', '.js'])"
                        },
                        "min_size": {
                            "type": "number",
                            "description": "Minimum file size in bytes"
                        },
                        "max_size": {
                            "type": "number",
                            "description": "Maximum file size in bytes"
                        },
                        "modified_since": {
                            "type": "string",
                            "description": "Modified since date (ISO format)"
                        },
                        "include_stats": {
                            "type": "boolean",
                            "default": True,
                            "description": "Include detailed statistics"
                        }
                    },
                    "required": ["directory_path"]
                }
            },
            {
                "name": "file_compress",
                "description": "Compress files/directories",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "source_path": {
                            "type": "string",
                            "description": "File or directory to compress"
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Output archive path"
                        },
                        "format": {
                            "type": "string",
                            "enum": ["zip", "tar", "tar.gz", "tar.bz2", "gz"],
                            "default": "zip",
                            "description": "Compression format"
                        },
                        "compression_level": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 9,
                            "default": 6,
                            "description": "Compression level (0=none, 9=max)"
                        },
                        "exclude_patterns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Patterns to exclude (glob style)"
                        }
                    },
                    "required": ["source_path", "output_path"]
                }
            },
            {
                "name": "file_extract",
                "description": "Extract compressed archives",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "archive_path": {
                            "type": "string",
                            "description": "Path to archive file"
                        },
                        "extract_path": {
                            "type": "string",
                            "description": "Directory to extract to"
                        },
                        "members": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific files to extract (empty = all)"
                        },
                        "create_directory": {
                            "type": "boolean",
                            "default": True,
                            "description": "Create extraction directory if it doesn't exist"
                        }
                    },
                    "required": ["archive_path", "extract_path"]
                }
            },
            {
                "name": "file_encrypt",
                "description": "Encrypt file with password",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "File to encrypt"
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Encrypted file output path"
                        },
                        "password": {
                            "type": "string",
                            "description": "Encryption password"
                        },
                        "key_name": {
                            "type": "string",
                            "description": "Name to store encryption key under"
                        }
                    },
                    "required": ["file_path", "password"]
                }
            },
            {
                "name": "file_decrypt",
                "description": "Decrypt encrypted file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "encrypted_file": {
                            "type": "string",
                            "description": "Encrypted file path"
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Decrypted file output path"
                        },
                        "password": {
                            "type": "string",
                            "description": "Decryption password"
                        },
                        "key_name": {
                            "type": "string",
                            "description": "Stored encryption key name"
                        }
                    },
                    "required": ["encrypted_file"]
                }
            },
            {
                "name": "file_monitor_start",
                "description": "Start monitoring directory for changes",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "directory_path": {
                            "type": "string",
                            "description": "Directory to monitor"
                        },
                        "monitor_name": {
                            "type": "string",
                            "description": "Unique name for this monitor"
                        },
                        "recursive": {
                            "type": "boolean",
                            "default": True,
                            "description": "Monitor subdirectories"
                        },
                        "events": {
                            "type": "array",
                            "items": {"type": "string", "enum": ["created", "modified", "deleted", "moved"]},
                            "default": ["created", "modified", "deleted"],
                            "description": "Events to monitor"
                        },
                        "file_patterns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "File patterns to monitor (glob style)"
                        }
                    },
                    "required": ["directory_path", "monitor_name"]
                }
            },
            {
                "name": "file_monitor_stop",
                "description": "Stop file monitoring",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "monitor_name": {
                            "type": "string",
                            "description": "Monitor name to stop"
                        }
                    },
                    "required": ["monitor_name"]
                }
            },
            {
                "name": "file_monitor_status",
                "description": "Get status of active file monitors",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "file_sync",
                "description": "Synchronize directories (like rsync)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "source_path": {
                            "type": "string",
                            "description": "Source directory"
                        },
                        "destination_path": {
                            "type": "string",
                            "description": "Destination directory"
                        },
                        "mode": {
                            "type": "string",
                            "enum": ["mirror", "backup", "sync"],
                            "default": "sync",
                            "description": "Sync mode"
                        },
                        "delete_extra": {
                            "type": "boolean",
                            "default": False,
                            "description": "Delete files in destination not in source"
                        },
                        "exclude_patterns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Patterns to exclude"
                        },
                        "dry_run": {
                            "type": "boolean",
                            "default": False,
                            "description": "Show what would be done without doing it"
                        }
                    },
                    "required": ["source_path", "destination_path"]
                }
            },
            {
                "name": "file_duplicate_finder",
                "description": "Find duplicate files by content hash",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "directory_path": {
                            "type": "string",
                            "description": "Directory to search for duplicates"
                        },
                        "recursive": {
                            "type": "boolean",
                            "default": True,
                            "description": "Search subdirectories"
                        },
                        "min_size": {
                            "type": "number",
                            "default": 1024,
                            "description": "Minimum file size to consider"
                        },
                        "hash_algorithm": {
                            "type": "string",
                            "enum": ["md5", "sha1", "sha256"],
                            "default": "md5",
                            "description": "Hash algorithm to use"
                        }
                    },
                    "required": ["directory_path"]
                }
            },
            {
                "name": "file_permissions_batch",
                "description": "Batch change file permissions",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "directory_path": {
                            "type": "string",
                            "description": "Directory to process"
                        },
                        "file_mode": {
                            "type": "string",
                            "description": "File permissions (octal like '644')"
                        },
                        "dir_mode": {
                            "type": "string",
                            "description": "Directory permissions (octal like '755')"
                        },
                        "recursive": {
                            "type": "boolean",
                            "default": True,
                            "description": "Apply recursively"
                        },
                        "file_patterns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "File patterns to match"
                        }
                    },
                    "required": ["directory_path"]
                }
            }
        ]
        
        return tools
    
    def analyze_file(self, file_path: str, include_hash: bool = True, include_content_preview: bool = False) -> Dict:
        """Analyze file properties"""
        try:
            path = Path(file_path)
            if not path.exists():
                return {"success": False, "error": f"File {file_path} does not exist"}
            
            stat_info = path.stat()
            
            analysis = {
                "path": str(path.absolute()),
                "name": path.name,
                "size": stat_info.st_size,
                "size_human": self._format_size(stat_info.st_size),
                "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(stat_info.st_atime).isoformat(),
                "permissions": oct(stat.S_IMODE(stat_info.st_mode)),
                "owner_uid": stat_info.st_uid,
                "group_gid": stat_info.st_gid,
                "is_file": path.is_file(),
                "is_directory": path.is_dir(),
                "is_symlink": path.is_symlink()
            }
            
            if path.is_file():
                # MIME type detection
                mime_type, encoding = mimetypes.guess_type(str(path))
                analysis["mime_type"] = mime_type
                analysis["encoding"] = encoding
                
                # Hash calculation
                if include_hash and stat_info.st_size < 100 * 1024 * 1024:  # Skip large files
                    try:
                        with open(path, 'rb') as f:
                            content = f.read()
                            analysis["md5"] = hashlib.md5(content).hexdigest()
                            analysis["sha256"] = hashlib.sha256(content).hexdigest()
                    except Exception as e:
                        analysis["hash_error"] = str(e)
                
                # Content preview for text files
                if include_content_preview and mime_type and mime_type.startswith('text'):
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()[:10]  # First 10 lines
                            analysis["content_preview"] = lines
                            analysis["line_count"] = len(lines)
                    except Exception as e:
                        analysis["preview_error"] = str(e)
            
            return {"success": True, "data": analysis}
            
        except Exception as e:
            return {"success": False, "error": f"File analysis failed: {str(e)}"}
    
    def scan_directory(self, directory_path: str, max_depth: int = 5, file_extensions: List[str] = None,
                      min_size: int = None, max_size: int = None, modified_since: str = None,
                      include_stats: bool = True) -> Dict:
        """Recursive directory scanning with filters"""
        try:
            root_path = Path(directory_path)
            if not root_path.exists():
                return {"success": False, "error": f"Directory {directory_path} does not exist"}
            
            if not root_path.is_dir():
                return {"success": False, "error": f"{directory_path} is not a directory"}
            
            # Parse modified_since if provided
            modified_since_timestamp = None
            if modified_since:
                try:
                    modified_since_timestamp = datetime.fromisoformat(modified_since).timestamp()
                except ValueError:
                    return {"success": False, "error": f"Invalid date format: {modified_since}"}
            
            files = []
            directories = []
            total_size = 0
            total_files = 0
            
            def scan_recursive(current_path: Path, current_depth: int):
                nonlocal total_size, total_files
                
                if current_depth > max_depth:
                    return
                
                try:
                    for item in current_path.iterdir():
                        if item.is_file():
                            # Apply filters
                            stat_info = item.stat()
                            
                            # Size filter
                            if min_size and stat_info.st_size < min_size:
                                continue
                            if max_size and stat_info.st_size > max_size:
                                continue
                            
                            # Extension filter
                            if file_extensions and item.suffix.lower() not in [ext.lower() for ext in file_extensions]:
                                continue
                            
                            # Modified date filter
                            if modified_since_timestamp and stat_info.st_mtime < modified_since_timestamp:
                                continue
                            
                            file_info = {
                                "path": str(item.absolute()),
                                "name": item.name,
                                "size": stat_info.st_size,
                                "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                                "extension": item.suffix
                            }
                            
                            files.append(file_info)
                            total_size += stat_info.st_size
                            total_files += 1
                            
                        elif item.is_dir():
                            dir_info = {
                                "path": str(item.absolute()),
                                "name": item.name,
                                "depth": current_depth
                            }
                            directories.append(dir_info)
                            
                            # Recursive scan
                            scan_recursive(item, current_depth + 1)
                            
                except PermissionError:
                    pass  # Skip directories we can't access
            
            scan_recursive(root_path, 0)
            
            result = {
                "directory": str(root_path.absolute()),
                "scan_date": datetime.now().isoformat(),
                "files": files,
                "directories": directories
            }
            
            if include_stats:
                result["statistics"] = {
                    "total_files": total_files,
                    "total_directories": len(directories),
                    "total_size": total_size,
                    "total_size_human": self._format_size(total_size),
                    "average_file_size": total_size / total_files if total_files > 0 else 0
                }
            
            return {"success": True, "data": result}
            
        except Exception as e:
            return {"success": False, "error": f"Directory scan failed: {str(e)}"}
    
    def compress_file(self, source_path: str, output_path: str, format: str = "zip",
                     compression_level: int = 6, exclude_patterns: List[str] = None) -> Dict:
        """Compress files or directories"""
        if not COMPRESSION_AVAILABLE:
            return {"success": False, "error": "Compression libraries not available"}
        
        try:
            source = Path(source_path)
            if not source.exists():
                return {"success": False, "error": f"Source {source_path} does not exist"}
            
            output = Path(output_path)
            
            if format == "zip":
                with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, compresslevel=compression_level) as zf:
                    if source.is_file():
                        zf.write(source, source.name)
                    else:
                        for file_path in source.rglob('*'):
                            if file_path.is_file():
                                if not self._should_exclude(file_path, exclude_patterns):
                                    zf.write(file_path, file_path.relative_to(source))
                                    
            elif format.startswith("tar"):
                mode = "w"
                if format == "tar.gz":
                    mode = "w:gz"
                elif format == "tar.bz2":
                    mode = "w:bz2"
                
                with tarfile.open(output, mode) as tf:
                    tf.add(source, arcname=source.name)
            
            elif format == "gz" and source.is_file():
                with open(source, 'rb') as f_in:
                    with gzip.open(output, 'wb', compresslevel=compression_level) as f_out:
                        shutil.copyfileobj(f_in, f_out)
            
            # Calculate compression ratio
            original_size = self._get_size(source)
            compressed_size = output.stat().st_size
            compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
            
            return {
                "success": True,
                "message": f"Compressed {source_path} to {output_path}",
                "original_size": original_size,
                "compressed_size": compressed_size,
                "compression_ratio": f"{compression_ratio:.1f}%",
                "format": format
            }
            
        except Exception as e:
            return {"success": False, "error": f"Compression failed: {str(e)}"}
    
    def extract_file(self, archive_path: str, extract_path: str, members: List[str] = None,
                    create_directory: bool = True) -> Dict:
        """Extract compressed archives"""
        if not COMPRESSION_AVAILABLE:
            return {"success": False, "error": "Compression libraries not available"}
        
        try:
            archive = Path(archive_path)
            if not archive.exists():
                return {"success": False, "error": f"Archive {archive_path} does not exist"}
            
            extract_dir = Path(extract_path)
            if create_directory:
                extract_dir.mkdir(parents=True, exist_ok=True)
            
            extracted_files = []
            
            if archive.suffix.lower() == '.zip':
                with zipfile.ZipFile(archive, 'r') as zf:
                    if members:
                        for member in members:
                            zf.extract(member, extract_dir)
                            extracted_files.append(member)
                    else:
                        zf.extractall(extract_dir)
                        extracted_files = zf.namelist()
                        
            elif archive.suffix.lower() in ['.tar', '.tar.gz', '.tar.bz2', '.tgz']:
                with tarfile.open(archive, 'r:*') as tf:
                    if members:
                        for member in members:
                            tf.extract(member, extract_dir)
                            extracted_files.append(member)
                    else:
                        tf.extractall(extract_dir)
                        extracted_files = tf.getnames()
                        
            elif archive.suffix.lower() == '.gz':
                # Single file gzip
                output_file = extract_dir / archive.stem
                with gzip.open(archive, 'rb') as f_in:
                    with open(output_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                extracted_files = [str(output_file)]
            
            return {
                "success": True,
                "message": f"Extracted {len(extracted_files)} files from {archive_path}",
                "extracted_files": extracted_files,
                "extract_path": str(extract_dir.absolute())
            }
            
        except Exception as e:
            return {"success": False, "error": f"Extraction failed: {str(e)}"}
    
    def encrypt_file(self, file_path: str, password: str, output_path: str = None, key_name: str = None) -> Dict:
        """Encrypt file with password"""
        if not ENCRYPTION_AVAILABLE:
            return {"success": False, "error": "Encryption library (cryptography) not available"}
        
        try:
            source = Path(file_path)
            if not source.exists():
                return {"success": False, "error": f"File {file_path} does not exist"}
            
            # Generate key from password
            key = Fernet.generate_key()
            fernet = Fernet(key)
            
            # Store key for later use
            if key_name:
                self.encryption_keys[key_name] = key
            
            # Read and encrypt file
            with open(source, 'rb') as f:
                data = f.read()
            
            encrypted_data = fernet.encrypt(data)
            
            # Determine output path
            if not output_path:
                output_path = str(source) + '.encrypted'
            
            # Write encrypted file
            with open(output_path, 'wb') as f:
                f.write(encrypted_data)
            
            return {
                "success": True,
                "message": f"File encrypted: {output_path}",
                "encrypted_file": output_path,
                "key_stored": key_name is not None
            }
            
        except Exception as e:
            return {"success": False, "error": f"Encryption failed: {str(e)}"}
    
    def decrypt_file(self, encrypted_file: str, password: str = None, output_path: str = None, key_name: str = None) -> Dict:
        """Decrypt encrypted file"""
        if not ENCRYPTION_AVAILABLE:
            return {"success": False, "error": "Encryption library (cryptography) not available"}
        
        try:
            source = Path(encrypted_file)
            if not source.exists():
                return {"success": False, "error": f"Encrypted file {encrypted_file} does not exist"}
            
            # Get decryption key
            if key_name and key_name in self.encryption_keys:
                key = self.encryption_keys[key_name]
            elif password:
                # For now, this is a simplified approach - in practice you'd need to store/derive keys properly
                return {"success": False, "error": "Password-based decryption not implemented yet"}
            else:
                return {"success": False, "error": "No decryption key or password provided"}
            
            fernet = Fernet(key)
            
            # Read and decrypt file
            with open(source, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = fernet.decrypt(encrypted_data)
            
            # Determine output path
            if not output_path:
                output_path = str(source).replace('.encrypted', '')
            
            # Write decrypted file
            with open(output_path, 'wb') as f:
                f.write(decrypted_data)
            
            return {
                "success": True,
                "message": f"File decrypted: {output_path}",
                "decrypted_file": output_path
            }
            
        except Exception as e:
            return {"success": False, "error": f"Decryption failed: {str(e)}"}
    
    def find_duplicates(self, directory_path: str, recursive: bool = True, min_size: int = 1024,
                       hash_algorithm: str = "md5") -> Dict:
        """Find duplicate files by content hash"""
        try:
            root_path = Path(directory_path)
            if not root_path.exists() or not root_path.is_dir():
                return {"success": False, "error": f"Directory {directory_path} does not exist"}
            
            # Hash algorithm selection
            if hash_algorithm == "md5":
                hasher_class = hashlib.md5
            elif hash_algorithm == "sha1":
                hasher_class = hashlib.sha1
            elif hash_algorithm == "sha256":
                hasher_class = hashlib.sha256
            else:
                return {"success": False, "error": f"Unsupported hash algorithm: {hash_algorithm}"}
            
            file_hashes = {}
            duplicates = {}
            
            # Scan files
            files_to_check = root_path.rglob('*') if recursive else root_path.iterdir()
            
            for file_path in files_to_check:
                if file_path.is_file() and file_path.stat().st_size >= min_size:
                    try:
                        # Calculate hash
                        hasher = hasher_class()
                        with open(file_path, 'rb') as f:
                            for chunk in iter(lambda: f.read(4096), b""):
                                hasher.update(chunk)
                        
                        file_hash = hasher.hexdigest()
                        
                        if file_hash in file_hashes:
                            # Duplicate found
                            if file_hash not in duplicates:
                                duplicates[file_hash] = {
                                    "hash": file_hash,
                                    "size": file_path.stat().st_size,
                                    "files": [str(file_hashes[file_hash])]
                                }
                            duplicates[file_hash]["files"].append(str(file_path.absolute()))
                        else:
                            file_hashes[file_hash] = file_path.absolute()
                            
                    except Exception as e:
                        continue  # Skip files we can't read
            
            # Calculate space savings
            total_wasted_space = 0
            for duplicate_group in duplicates.values():
                # All files except one are wasted space
                wasted_files = len(duplicate_group["files"]) - 1
                total_wasted_space += duplicate_group["size"] * wasted_files
            
            return {
                "success": True,
                "data": {
                    "duplicate_groups": list(duplicates.values()),
                    "total_duplicate_groups": len(duplicates),
                    "total_duplicate_files": sum(len(group["files"]) for group in duplicates.values()),
                    "total_wasted_space": total_wasted_space,
                    "total_wasted_space_human": self._format_size(total_wasted_space),
                    "hash_algorithm": hash_algorithm
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"Duplicate search failed: {str(e)}"}
    
    def sync_directories(self, source_path: str, destination_path: str, mode: str = "sync",
                        delete_extra: bool = False, exclude_patterns: List[str] = None,
                        dry_run: bool = False) -> Dict:
        """Synchronize directories"""
        try:
            source = Path(source_path)
            dest = Path(destination_path)
            
            if not source.exists():
                return {"success": False, "error": f"Source directory {source_path} does not exist"}
            
            if not source.is_dir():
                return {"success": False, "error": f"Source {source_path} is not a directory"}
            
            # Create destination if it doesn't exist
            if not dry_run:
                dest.mkdir(parents=True, exist_ok=True)
            
            operations = []
            
            # Copy/update files from source to destination
            for source_file in source.rglob('*'):
                if source_file.is_file():
                    if self._should_exclude(source_file, exclude_patterns):
                        continue
                    
                    relative_path = source_file.relative_to(source)
                    dest_file = dest / relative_path
                    
                    should_copy = False
                    operation_type = ""
                    
                    if not dest_file.exists():
                        should_copy = True
                        operation_type = "CREATE"
                    else:
                        # Compare modification times and sizes
                        source_stat = source_file.stat()
                        dest_stat = dest_file.stat()
                        
                        if (source_stat.st_mtime > dest_stat.st_mtime or 
                            source_stat.st_size != dest_stat.st_size):
                            should_copy = True
                            operation_type = "UPDATE"
                    
                    if should_copy:
                        operations.append({
                            "operation": operation_type,
                            "source": str(source_file),
                            "destination": str(dest_file)
                        })
                        
                        if not dry_run:
                            dest_file.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(source_file, dest_file)
            
            # Delete extra files in destination (if requested)
            if delete_extra:
                for dest_file in dest.rglob('*'):
                    if dest_file.is_file():
                        relative_path = dest_file.relative_to(dest)
                        source_file = source / relative_path
                        
                        if not source_file.exists():
                            operations.append({
                                "operation": "DELETE",
                                "source": "",
                                "destination": str(dest_file)
                            })
                            
                            if not dry_run:
                                dest_file.unlink()
            
            return {
                "success": True,
                "data": {
                    "source": str(source.absolute()),
                    "destination": str(dest.absolute()),
                    "mode": mode,
                    "dry_run": dry_run,
                    "operations": operations,
                    "total_operations": len(operations),
                    "created": len([op for op in operations if op["operation"] == "CREATE"]),
                    "updated": len([op for op in operations if op["operation"] == "UPDATE"]),
                    "deleted": len([op for op in operations if op["operation"] == "DELETE"])
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"Directory sync failed: {str(e)}"}
    
    def batch_permissions(self, directory_path: str, file_mode: str = None, dir_mode: str = None,
                         recursive: bool = True, file_patterns: List[str] = None) -> Dict:
        """Batch change file permissions"""
        try:
            root_path = Path(directory_path)
            if not root_path.exists():
                return {"success": False, "error": f"Directory {directory_path} does not exist"}
            
            changes = []
            
            # Convert octal strings to integers
            file_mode_int = int(file_mode, 8) if file_mode else None
            dir_mode_int = int(dir_mode, 8) if dir_mode else None
            
            paths_to_process = root_path.rglob('*') if recursive else root_path.iterdir()
            
            for path in paths_to_process:
                should_process = True
                
                # Check file patterns
                if file_patterns and path.is_file():
                    import fnmatch
                    should_process = any(fnmatch.fnmatch(path.name, pattern) for pattern in file_patterns)
                
                if should_process:
                    if path.is_file() and file_mode_int:
                        old_mode = oct(stat.S_IMODE(path.stat().st_mode))
                        path.chmod(file_mode_int)
                        changes.append({
                            "path": str(path),
                            "type": "file",
                            "old_mode": old_mode,
                            "new_mode": file_mode
                        })
                    elif path.is_dir() and dir_mode_int:
                        old_mode = oct(stat.S_IMODE(path.stat().st_mode))
                        path.chmod(dir_mode_int)
                        changes.append({
                            "path": str(path),
                            "type": "directory", 
                            "old_mode": old_mode,
                            "new_mode": dir_mode
                        })
            
            return {
                "success": True,
                "data": {
                    "directory": str(root_path.absolute()),
                    "changes": changes,
                    "total_changes": len(changes),
                    "files_changed": len([c for c in changes if c["type"] == "file"]),
                    "directories_changed": len([c for c in changes if c["type"] == "directory"])
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"Permission batch change failed: {str(e)}"}
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"
    
    def _get_size(self, path: Path) -> int:
        """Get total size of file or directory"""
        if path.is_file():
            return path.stat().st_size
        elif path.is_dir():
            return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        return 0
    
    def _should_exclude(self, file_path: Path, exclude_patterns: List[str]) -> bool:
        """Check if file should be excluded based on patterns"""
        if not exclude_patterns:
            return False
        
        import fnmatch
        path_str = str(file_path)
        return any(fnmatch.fnmatch(path_str, pattern) for pattern in exclude_patterns)
    
    def handle_tool_call(self, tool_name: str, arguments: Dict) -> Dict:
        """Handle enhanced file tool calls"""
        try:
            if tool_name == "file_analyze":
                return self.analyze_file(**arguments)
            elif tool_name == "directory_scan":
                return self.scan_directory(**arguments)
            elif tool_name == "file_compress":
                return self.compress_file(**arguments)
            elif tool_name == "file_extract":
                return self.extract_file(**arguments)
            elif tool_name == "file_encrypt":
                return self.encrypt_file(**arguments)
            elif tool_name == "file_decrypt":
                return self.decrypt_file(**arguments)
            elif tool_name == "file_duplicate_finder":
                return self.find_duplicates(**arguments)
            elif tool_name == "file_sync":
                return self.sync_directories(**arguments)
            elif tool_name == "file_permissions_batch":
                return self.batch_permissions(**arguments)
            # File monitoring tools would need watchdog implementation
            elif tool_name in ["file_monitor_start", "file_monitor_stop", "file_monitor_status"]:
                return {"success": False, "error": "File monitoring not implemented yet (requires watchdog library)"}
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}
                
        except Exception as e:
            return {"success": False, "error": f"Tool execution failed: {str(e)}"}

def main():
    """Main MCP server loop for Enhanced File Operations"""
    server = EnhancedFileMCPServer()
    
    print("📁 Enhanced File Operations MCP Server Started", file=sys.stderr)
    print(f"🗜️ Compression: {'✅ Available' if COMPRESSION_AVAILABLE else '❌ Missing'}", file=sys.stderr)
    print(f"🔐 Encryption: {'✅ Available' if ENCRYPTION_AVAILABLE else '❌ Missing (pip install cryptography)'}", file=sys.stderr)
    print(f"👁️ Monitoring: {'✅ Available' if MONITORING_AVAILABLE else '❌ Missing (pip install watchdog)'}", file=sys.stderr)
    
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            request = json.loads(line)
            method = request.get("method", "")
            
            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {
                            "name": "Enhanced File Operations MCP Server",
                            "version": "1.0.0"
                        }
                    }
                }
            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {"tools": server.get_tools()}
                }
            elif method == "tools/call":
                params = request.get("params", {})
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})
                
                result = server.handle_tool_call(tool_name, arguments)
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                }
            elif method == "notifications/initialized":
                continue  # No response needed
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            print(json.dumps(response))
            sys.stdout.flush()
            
        except json.JSONDecodeError:
            error_response = {
                "jsonrpc": "2.0",
                "id": 1,
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()

if __name__ == "__main__":
    main()