#!/usr/bin/env python3
"""
Docker MCP Server - Integrace s Docker API
Poskytuje AI kontrolu nad Docker kontejnery, images, networks, volumes
"""
import json
import sys
import docker
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

class DockerMCPServer:
    def __init__(self):
        try:
            self.client = docker.from_env()
            self.connected = True
        except Exception as e:
            self.client = None
            self.connected = False
            print(f"⚠️ Docker connection failed: {e}", file=sys.stderr)
    
    def get_tools(self):
        """Return available Docker tools"""
        return [
            {
                "name": "docker_list_containers",
                "description": "List Docker containers",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "all": {
                            "type": "boolean",
                            "default": False,
                            "description": "Show all containers (including stopped)"
                        },
                        "filters": {
                            "type": "object",
                            "description": "Filters to apply (e.g., {'status': 'running'})"
                        }
                    }
                }
            },
            {
                "name": "docker_get_container_info",
                "description": "Get detailed container information",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "container_id": {
                            "type": "string",
                            "description": "Container ID or name"
                        }
                    },
                    "required": ["container_id"]
                }
            },
            {
                "name": "docker_start_container",
                "description": "Start a Docker container",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "container_id": {
                            "type": "string",
                            "description": "Container ID or name"
                        }
                    },
                    "required": ["container_id"]
                }
            },
            {
                "name": "docker_stop_container",
                "description": "Stop a Docker container",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "container_id": {
                            "type": "string",
                            "description": "Container ID or name"
                        },
                        "timeout": {
                            "type": "number",
                            "default": 10,
                            "description": "Seconds to wait before force killing"
                        }
                    },
                    "required": ["container_id"]
                }
            },
            {
                "name": "docker_restart_container",
                "description": "Restart a Docker container",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "container_id": {
                            "type": "string",
                            "description": "Container ID or name"
                        },
                        "timeout": {
                            "type": "number",
                            "default": 10,
                            "description": "Seconds to wait before force killing"
                        }
                    },
                    "required": ["container_id"]
                }
            },
            {
                "name": "docker_remove_container",
                "description": "Remove a Docker container",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "container_id": {
                            "type": "string",
                            "description": "Container ID or name"
                        },
                        "force": {
                            "type": "boolean",
                            "default": False,
                            "description": "Force removal of running container"
                        },
                        "volumes": {
                            "type": "boolean",
                            "default": False,
                            "description": "Remove associated volumes"
                        }
                    },
                    "required": ["container_id"]
                }
            },
            {
                "name": "docker_create_container",
                "description": "Create a new Docker container",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "image": {
                            "type": "string",
                            "description": "Docker image name"
                        },
                        "name": {
                            "type": "string",
                            "description": "Container name"
                        },
                        "command": {
                            "type": "string",
                            "description": "Command to run in container"
                        },
                        "environment": {
                            "type": "object",
                            "description": "Environment variables"
                        },
                        "ports": {
                            "type": "object",
                            "description": "Port mappings (e.g., {'8080/tcp': 8080})"
                        },
                        "volumes": {
                            "type": "object",
                            "description": "Volume mappings"
                        },
                        "detach": {
                            "type": "boolean",
                            "default": True,
                            "description": "Run container in background"
                        }
                    },
                    "required": ["image"]
                }
            },
            {
                "name": "docker_list_images",
                "description": "List Docker images",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "all": {
                            "type": "boolean",
                            "default": False,
                            "description": "Show all images (including intermediate)"
                        },
                        "filters": {
                            "type": "object",
                            "description": "Filters to apply"
                        }
                    }
                }
            },
            {
                "name": "docker_pull_image",
                "description": "Pull Docker image from registry",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "repository": {
                            "type": "string",
                            "description": "Image repository (e.g., 'nginx', 'python:3.9')"
                        },
                        "tag": {
                            "type": "string",
                            "default": "latest",
                            "description": "Image tag"
                        }
                    },
                    "required": ["repository"]
                }
            },
            {
                "name": "docker_remove_image",
                "description": "Remove Docker image",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "image_id": {
                            "type": "string",
                            "description": "Image ID or name"
                        },
                        "force": {
                            "type": "boolean",
                            "default": False,
                            "description": "Force removal"
                        }
                    },
                    "required": ["image_id"]
                }
            },
            {
                "name": "docker_get_container_logs",
                "description": "Get container logs",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "container_id": {
                            "type": "string",
                            "description": "Container ID or name"
                        },
                        "tail": {
                            "type": "number",
                            "default": 100,
                            "description": "Number of lines to tail"
                        },
                        "timestamps": {
                            "type": "boolean",
                            "default": True,
                            "description": "Include timestamps"
                        }
                    },
                    "required": ["container_id"]
                }
            },
            {
                "name": "docker_execute_command",
                "description": "Execute command in running container",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "container_id": {
                            "type": "string",
                            "description": "Container ID or name"
                        },
                        "command": {
                            "type": "string",
                            "description": "Command to execute"
                        },
                        "workdir": {
                            "type": "string",
                            "description": "Working directory"
                        }
                    },
                    "required": ["container_id", "command"]
                }
            },
            {
                "name": "docker_list_networks",
                "description": "List Docker networks",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "filters": {
                            "type": "object",
                            "description": "Filters to apply"
                        }
                    }
                }
            },
            {
                "name": "docker_create_network",
                "description": "Create Docker network",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Network name"
                        },
                        "driver": {
                            "type": "string",
                            "default": "bridge",
                            "description": "Network driver"
                        },
                        "options": {
                            "type": "object",
                            "description": "Network options"
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "docker_list_volumes",
                "description": "List Docker volumes",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "filters": {
                            "type": "object",
                            "description": "Filters to apply"
                        }
                    }
                }
            },
            {
                "name": "docker_create_volume",
                "description": "Create Docker volume",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Volume name"
                        },
                        "driver": {
                            "type": "string",
                            "default": "local",
                            "description": "Volume driver"
                        },
                        "driver_opts": {
                            "type": "object",
                            "description": "Driver options"
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "docker_system_info",
                "description": "Get Docker system information",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "docker_system_prune",
                "description": "Clean up Docker system (remove unused containers, networks, images)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "all": {
                            "type": "boolean",
                            "default": False,
                            "description": "Remove all unused images, not just dangling"
                        },
                        "volumes": {
                            "type": "boolean", 
                            "default": False,
                            "description": "Remove unused volumes"
                        }
                    }
                }
            }
        ]
    
    def check_connection(self):
        """Check Docker connection"""
        if not self.connected:
            return {"success": False, "error": "Docker daemon not accessible"}
        return {"success": True}
    
    def list_containers(self, all: bool = False, filters: Dict = None) -> Dict:
        """List Docker containers"""
        check = self.check_connection()
        if not check["success"]:
            return check
        
        try:
            containers = self.client.containers.list(all=all, filters=filters)
            container_list = []
            
            for container in containers:
                container_info = {
                    "id": container.id[:12],
                    "name": container.name,
                    "image": container.image.tags[0] if container.image.tags else container.image.id[:12],
                    "status": container.status,
                    "created": container.attrs.get("Created", ""),
                    "ports": container.ports
                }
                container_list.append(container_info)
            
            return {"success": True, "data": container_list}
            
        except Exception as e:
            return {"success": False, "error": f"Failed to list containers: {str(e)}"}
    
    def get_container_info(self, container_id: str) -> Dict:
        """Get detailed container information"""
        check = self.check_connection()
        if not check["success"]:
            return check
        
        try:
            container = self.client.containers.get(container_id)
            info = {
                "id": container.id,
                "name": container.name,
                "image": container.image.tags[0] if container.image.tags else container.image.id[:12],
                "status": container.status,
                "created": container.attrs.get("Created", ""),
                "ports": container.ports,
                "environment": container.attrs.get("Config", {}).get("Env", []),
                "mounts": [{"source": m["Source"], "destination": m["Destination"], "type": m["Type"]} 
                          for m in container.attrs.get("Mounts", [])],
                "network_settings": container.attrs.get("NetworkSettings", {}),
                "restart_policy": container.attrs.get("HostConfig", {}).get("RestartPolicy", {}),
                "resource_limits": {
                    "memory": container.attrs.get("HostConfig", {}).get("Memory", 0),
                    "cpu_quota": container.attrs.get("HostConfig", {}).get("CpuQuota", 0),
                    "cpu_shares": container.attrs.get("HostConfig", {}).get("CpuShares", 0)
                }
            }
            
            return {"success": True, "data": info}
            
        except docker.errors.NotFound:
            return {"success": False, "error": f"Container {container_id} not found"}
        except Exception as e:
            return {"success": False, "error": f"Failed to get container info: {str(e)}"}
    
    def start_container(self, container_id: str) -> Dict:
        """Start Docker container"""
        check = self.check_connection()
        if not check["success"]:
            return check
        
        try:
            container = self.client.containers.get(container_id)
            container.start()
            return {"success": True, "message": f"Container {container_id} started"}
            
        except docker.errors.NotFound:
            return {"success": False, "error": f"Container {container_id} not found"}
        except Exception as e:
            return {"success": False, "error": f"Failed to start container: {str(e)}"}
    
    def stop_container(self, container_id: str, timeout: int = 10) -> Dict:
        """Stop Docker container"""
        check = self.check_connection()
        if not check["success"]:
            return check
        
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=timeout)
            return {"success": True, "message": f"Container {container_id} stopped"}
            
        except docker.errors.NotFound:
            return {"success": False, "error": f"Container {container_id} not found"}
        except Exception as e:
            return {"success": False, "error": f"Failed to stop container: {str(e)}"}
    
    def restart_container(self, container_id: str, timeout: int = 10) -> Dict:
        """Restart Docker container"""
        check = self.check_connection()
        if not check["success"]:
            return check
        
        try:
            container = self.client.containers.get(container_id)
            container.restart(timeout=timeout)
            return {"success": True, "message": f"Container {container_id} restarted"}
            
        except docker.errors.NotFound:
            return {"success": False, "error": f"Container {container_id} not found"}
        except Exception as e:
            return {"success": False, "error": f"Failed to restart container: {str(e)}"}
    
    def remove_container(self, container_id: str, force: bool = False, volumes: bool = False) -> Dict:
        """Remove Docker container"""
        check = self.check_connection()
        if not check["success"]:
            return check
        
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=force, v=volumes)
            return {"success": True, "message": f"Container {container_id} removed"}
            
        except docker.errors.NotFound:
            return {"success": False, "error": f"Container {container_id} not found"}
        except Exception as e:
            return {"success": False, "error": f"Failed to remove container: {str(e)}"}
    
    def create_container(self, image: str, name: str = "", command: str = "", environment: Dict = None, 
                        ports: Dict = None, volumes: Dict = None, detach: bool = True) -> Dict:
        """Create new Docker container"""
        check = self.check_connection()
        if not check["success"]:
            return check
        
        try:
            kwargs = {"image": image, "detach": detach}
            
            if name:
                kwargs["name"] = name
            if command:
                kwargs["command"] = command
            if environment:
                kwargs["environment"] = environment
            if ports:
                kwargs["ports"] = ports
            if volumes:
                kwargs["volumes"] = volumes
            
            container = self.client.containers.create(**kwargs)
            
            return {
                "success": True, 
                "message": f"Container created: {container.id[:12]}",
                "container_id": container.id,
                "container_name": container.name
            }
            
        except docker.errors.ImageNotFound:
            return {"success": False, "error": f"Image {image} not found"}
        except Exception as e:
            return {"success": False, "error": f"Failed to create container: {str(e)}"}
    
    def list_images(self, all: bool = False, filters: Dict = None) -> Dict:
        """List Docker images"""
        check = self.check_connection()
        if not check["success"]:
            return check
        
        try:
            images = self.client.images.list(all=all, filters=filters)
            image_list = []
            
            for image in images:
                image_info = {
                    "id": image.id.split(':')[1][:12],
                    "tags": image.tags,
                    "size": image.attrs.get("Size", 0),
                    "created": image.attrs.get("Created", ""),
                    "architecture": image.attrs.get("Architecture", ""),
                    "os": image.attrs.get("Os", "")
                }
                image_list.append(image_info)
            
            return {"success": True, "data": image_list}
            
        except Exception as e:
            return {"success": False, "error": f"Failed to list images: {str(e)}"}
    
    def pull_image(self, repository: str, tag: str = "latest") -> Dict:
        """Pull Docker image from registry"""
        check = self.check_connection()
        if not check["success"]:
            return check
        
        try:
            image = self.client.images.pull(repository, tag=tag)
            return {
                "success": True, 
                "message": f"Image pulled: {repository}:{tag}",
                "image_id": image.id
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to pull image: {str(e)}"}
    
    def remove_image(self, image_id: str, force: bool = False) -> Dict:
        """Remove Docker image"""
        check = self.check_connection()
        if not check["success"]:
            return check
        
        try:
            self.client.images.remove(image_id, force=force)
            return {"success": True, "message": f"Image {image_id} removed"}
            
        except docker.errors.ImageNotFound:
            return {"success": False, "error": f"Image {image_id} not found"}
        except Exception as e:
            return {"success": False, "error": f"Failed to remove image: {str(e)}"}
    
    def get_container_logs(self, container_id: str, tail: int = 100, timestamps: bool = True) -> Dict:
        """Get container logs"""
        check = self.check_connection()
        if not check["success"]:
            return check
        
        try:
            container = self.client.containers.get(container_id)
            logs = container.logs(tail=tail, timestamps=timestamps).decode('utf-8')
            
            return {"success": True, "data": logs}
            
        except docker.errors.NotFound:
            return {"success": False, "error": f"Container {container_id} not found"}
        except Exception as e:
            return {"success": False, "error": f"Failed to get logs: {str(e)}"}
    
    def execute_command(self, container_id: str, command: str, workdir: str = None) -> Dict:
        """Execute command in running container"""
        check = self.check_connection()
        if not check["success"]:
            return check
        
        try:
            container = self.client.containers.get(container_id)
            
            if container.status != "running":
                return {"success": False, "error": f"Container {container_id} is not running"}
            
            exec_result = container.exec_run(command, workdir=workdir)
            
            return {
                "success": True,
                "exit_code": exec_result.exit_code,
                "output": exec_result.output.decode('utf-8')
            }
            
        except docker.errors.NotFound:
            return {"success": False, "error": f"Container {container_id} not found"}
        except Exception as e:
            return {"success": False, "error": f"Failed to execute command: {str(e)}"}
    
    def list_networks(self, filters: Dict = None) -> Dict:
        """List Docker networks"""
        check = self.check_connection()
        if not check["success"]:
            return check
        
        try:
            networks = self.client.networks.list(filters=filters)
            network_list = []
            
            for network in networks:
                network_info = {
                    "id": network.id[:12],
                    "name": network.name,
                    "driver": network.attrs.get("Driver", ""),
                    "scope": network.attrs.get("Scope", ""),
                    "created": network.attrs.get("Created", ""),
                    "containers": list(network.attrs.get("Containers", {}).keys())
                }
                network_list.append(network_info)
            
            return {"success": True, "data": network_list}
            
        except Exception as e:
            return {"success": False, "error": f"Failed to list networks: {str(e)}"}
    
    def create_network(self, name: str, driver: str = "bridge", options: Dict = None) -> Dict:
        """Create Docker network"""
        check = self.check_connection()
        if not check["success"]:
            return check
        
        try:
            network = self.client.networks.create(name, driver=driver, options=options)
            return {
                "success": True,
                "message": f"Network created: {name}",
                "network_id": network.id
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to create network: {str(e)}"}
    
    def list_volumes(self, filters: Dict = None) -> Dict:
        """List Docker volumes"""
        check = self.check_connection()
        if not check["success"]:
            return check
        
        try:
            volumes = self.client.volumes.list(filters=filters)
            volume_list = []
            
            for volume in volumes:
                volume_info = {
                    "name": volume.name,
                    "driver": volume.attrs.get("Driver", ""),
                    "mountpoint": volume.attrs.get("Mountpoint", ""),
                    "created": volume.attrs.get("CreatedAt", ""),
                    "scope": volume.attrs.get("Scope", "")
                }
                volume_list.append(volume_info)
            
            return {"success": True, "data": volume_list}
            
        except Exception as e:
            return {"success": False, "error": f"Failed to list volumes: {str(e)}"}
    
    def create_volume(self, name: str, driver: str = "local", driver_opts: Dict = None) -> Dict:
        """Create Docker volume"""
        check = self.check_connection()
        if not check["success"]:
            return check
        
        try:
            volume = self.client.volumes.create(name, driver=driver, driver_opts=driver_opts)
            return {
                "success": True,
                "message": f"Volume created: {name}",
                "volume_name": volume.name
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to create volume: {str(e)}"}
    
    def system_info(self) -> Dict:
        """Get Docker system information"""
        check = self.check_connection()
        if not check["success"]:
            return check
        
        try:
            info = self.client.info()
            
            filtered_info = {
                "containers": info.get("Containers", 0),
                "containers_running": info.get("ContainersRunning", 0),
                "containers_paused": info.get("ContainersPaused", 0),
                "containers_stopped": info.get("ContainersStopped", 0),
                "images": info.get("Images", 0),
                "server_version": info.get("ServerVersion", ""),
                "docker_root_dir": info.get("DockerRootDir", ""),
                "operating_system": info.get("OperatingSystem", ""),
                "architecture": info.get("Architecture", ""),
                "memory_total": info.get("MemTotal", 0),
                "cpus": info.get("NCPU", 0)
            }
            
            return {"success": True, "data": filtered_info}
            
        except Exception as e:
            return {"success": False, "error": f"Failed to get system info: {str(e)}"}
    
    def system_prune(self, all: bool = False, volumes: bool = False) -> Dict:
        """Clean up Docker system"""
        check = self.check_connection()
        if not check["success"]:
            return check
        
        try:
            # Prune containers
            container_prune = self.client.containers.prune()
            
            # Prune networks
            network_prune = self.client.networks.prune()
            
            # Prune images
            image_prune = self.client.images.prune(filters={'dangling': False} if all else None)
            
            result = {
                "containers_deleted": container_prune.get('ContainersDeleted', []),
                "space_reclaimed": container_prune.get('SpaceReclaimed', 0),
                "networks_deleted": network_prune.get('NetworksDeleted', []),
                "images_deleted": image_prune.get('ImagesDeleted', []),
                "images_space_reclaimed": image_prune.get('SpaceReclaimed', 0)
            }
            
            # Prune volumes if requested
            if volumes:
                volume_prune = self.client.volumes.prune()
                result["volumes_deleted"] = volume_prune.get('VolumesDeleted', [])
                result["volumes_space_reclaimed"] = volume_prune.get('SpaceReclaimed', 0)
            
            return {"success": True, "data": result}
            
        except Exception as e:
            return {"success": False, "error": f"Failed to prune system: {str(e)}"}
    
    def handle_tool_call(self, tool_name: str, arguments: Dict) -> Dict:
        """Handle Docker tool calls"""
        try:
            if tool_name == "docker_list_containers":
                return self.list_containers(**arguments)
            elif tool_name == "docker_get_container_info":
                return self.get_container_info(**arguments)
            elif tool_name == "docker_start_container":
                return self.start_container(**arguments)
            elif tool_name == "docker_stop_container":
                return self.stop_container(**arguments)
            elif tool_name == "docker_restart_container":
                return self.restart_container(**arguments)
            elif tool_name == "docker_remove_container":
                return self.remove_container(**arguments)
            elif tool_name == "docker_create_container":
                return self.create_container(**arguments)
            elif tool_name == "docker_list_images":
                return self.list_images(**arguments)
            elif tool_name == "docker_pull_image":
                return self.pull_image(**arguments)
            elif tool_name == "docker_remove_image":
                return self.remove_image(**arguments)
            elif tool_name == "docker_get_container_logs":
                return self.get_container_logs(**arguments)
            elif tool_name == "docker_execute_command":
                return self.execute_command(**arguments)
            elif tool_name == "docker_list_networks":
                return self.list_networks(**arguments)
            elif tool_name == "docker_create_network":
                return self.create_network(**arguments)
            elif tool_name == "docker_list_volumes":
                return self.list_volumes(**arguments)
            elif tool_name == "docker_create_volume":
                return self.create_volume(**arguments)
            elif tool_name == "docker_system_info":
                return self.system_info()
            elif tool_name == "docker_system_prune":
                return self.system_prune(**arguments)
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}
                
        except Exception as e:
            return {"success": False, "error": f"Tool execution failed: {str(e)}"}

def main():
    """Main MCP server loop for Docker integration"""
    server = DockerMCPServer()
    
    print("🐳 Docker MCP Server Started", file=sys.stderr)
    print(f"🔗 Docker Connection: {'✅ Connected' if server.connected else '❌ Failed'}", file=sys.stderr)
    
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
                            "name": "Docker MCP Server",
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