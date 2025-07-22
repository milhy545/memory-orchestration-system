#!/usr/bin/env python3
"""
GitHub MCP Server - Integrace s GitHub API
Poskytuje přístup k GitHub repositories, issues, pull requests, commits
"""
import json
import sys
import requests
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

class GitHubMCPServer:
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.base_url = "https://api.github.com"
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHub-MCP-Server/1.0'
        }
        
        if self.github_token:
            self.headers['Authorization'] = f'token {self.github_token}'
    
    def get_tools(self):
        """Return available GitHub tools"""
        return [
            {
                "name": "github_list_repos",
                "description": "List GitHub repositories for user/organization",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "username": {
                            "type": "string",
                            "description": "GitHub username or organization"
                        },
                        "type": {
                            "type": "string",
                            "enum": ["all", "owner", "member", "public", "private"],
                            "default": "owner",
                            "description": "Repository type to list"
                        },
                        "sort": {
                            "type": "string", 
                            "enum": ["created", "updated", "pushed", "full_name"],
                            "default": "updated",
                            "description": "Sort repositories by"
                        },
                        "per_page": {
                            "type": "number",
                            "default": 30,
                            "description": "Number of repositories per page"
                        }
                    },
                    "required": ["username"]
                }
            },
            {
                "name": "github_get_repo_info",
                "description": "Get detailed information about a repository",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "owner": {
                            "type": "string",
                            "description": "Repository owner"
                        },
                        "repo": {
                            "type": "string", 
                            "description": "Repository name"
                        }
                    },
                    "required": ["owner", "repo"]
                }
            },
            {
                "name": "github_list_issues",
                "description": "List issues in a repository",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "owner": {
                            "type": "string",
                            "description": "Repository owner"
                        },
                        "repo": {
                            "type": "string",
                            "description": "Repository name"  
                        },
                        "state": {
                            "type": "string",
                            "enum": ["open", "closed", "all"],
                            "default": "open",
                            "description": "Issue state"
                        },
                        "labels": {
                            "type": "string",
                            "description": "Comma-separated list of labels"
                        },
                        "sort": {
                            "type": "string",
                            "enum": ["created", "updated", "comments"],
                            "default": "updated",
                            "description": "Sort issues by"
                        },
                        "per_page": {
                            "type": "number", 
                            "default": 30,
                            "description": "Number of issues per page"
                        }
                    },
                    "required": ["owner", "repo"]
                }
            },
            {
                "name": "github_create_issue",
                "description": "Create a new issue in repository",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "owner": {
                            "type": "string",
                            "description": "Repository owner"
                        },
                        "repo": {
                            "type": "string",
                            "description": "Repository name"
                        },
                        "title": {
                            "type": "string",
                            "description": "Issue title"
                        },
                        "body": {
                            "type": "string",
                            "description": "Issue description"
                        },
                        "assignees": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "GitHub usernames to assign"
                        },
                        "labels": {
                            "type": "array", 
                            "items": {"type": "string"},
                            "description": "Labels to apply"
                        }
                    },
                    "required": ["owner", "repo", "title"]
                }
            },
            {
                "name": "github_list_commits",
                "description": "List commits in a repository",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "owner": {
                            "type": "string",
                            "description": "Repository owner"
                        },
                        "repo": {
                            "type": "string",
                            "description": "Repository name"
                        },
                        "sha": {
                            "type": "string",
                            "description": "SHA or branch to start listing from"
                        },
                        "path": {
                            "type": "string",
                            "description": "Only commits containing this file path"
                        },
                        "since": {
                            "type": "string",
                            "description": "Only commits after this date (ISO 8601)"
                        },
                        "until": {
                            "type": "string", 
                            "description": "Only commits before this date (ISO 8601)"
                        },
                        "per_page": {
                            "type": "number",
                            "default": 30,
                            "description": "Number of commits per page"
                        }
                    },
                    "required": ["owner", "repo"]
                }
            },
            {
                "name": "github_get_file_content",
                "description": "Get file content from repository",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "owner": {
                            "type": "string",
                            "description": "Repository owner"
                        },
                        "repo": {
                            "type": "string", 
                            "description": "Repository name"
                        },
                        "path": {
                            "type": "string",
                            "description": "File path in repository"
                        },
                        "ref": {
                            "type": "string",
                            "description": "Branch, tag, or commit SHA (default: default branch)"
                        }
                    },
                    "required": ["owner", "repo", "path"]
                }
            },
            {
                "name": "github_list_pull_requests",
                "description": "List pull requests in repository", 
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "owner": {
                            "type": "string",
                            "description": "Repository owner"
                        },
                        "repo": {
                            "type": "string",
                            "description": "Repository name"
                        },
                        "state": {
                            "type": "string",
                            "enum": ["open", "closed", "all"],
                            "default": "open",
                            "description": "Pull request state"
                        },
                        "head": {
                            "type": "string",
                            "description": "Filter by head branch (owner:branch)"
                        },
                        "base": {
                            "type": "string", 
                            "description": "Filter by base branch"
                        },
                        "sort": {
                            "type": "string",
                            "enum": ["created", "updated", "popularity", "long-running"],
                            "default": "created",
                            "description": "Sort pull requests by"
                        },
                        "per_page": {
                            "type": "number",
                            "default": 30,
                            "description": "Number of pull requests per page"
                        }
                    },
                    "required": ["owner", "repo"]
                }
            },
            {
                "name": "github_search_code",
                "description": "Search code across GitHub",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (supports GitHub search syntax)"
                        },
                        "sort": {
                            "type": "string",
                            "enum": ["indexed", "best-match"],
                            "default": "best-match",
                            "description": "Sort results by"
                        },
                        "per_page": {
                            "type": "number",
                            "default": 30,
                            "description": "Number of results per page"
                        }
                    },
                    "required": ["query"]
                }
            }
        ]
    
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
        """Make request to GitHub API"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=data, params=params, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=self.headers, json=data, params=params, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=self.headers, params=params, timeout=30)
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}
            
            if response.status_code in [200, 201]:
                return {"success": True, "data": response.json()}
            else:
                return {
                    "success": False, 
                    "error": f"GitHub API error: {response.status_code}",
                    "message": response.text
                }
                
        except requests.RequestException as e:
            return {"success": False, "error": f"Request failed: {str(e)}"}
    
    def list_repos(self, username: str, type: str = "owner", sort: str = "updated", per_page: int = 30) -> Dict:
        """List repositories for user/organization"""
        params = {
            "type": type,
            "sort": sort, 
            "per_page": per_page
        }
        
        endpoint = f"users/{username}/repos"
        return self.make_request("GET", endpoint, params=params)
    
    def get_repo_info(self, owner: str, repo: str) -> Dict:
        """Get repository information"""
        endpoint = f"repos/{owner}/{repo}"
        return self.make_request("GET", endpoint)
    
    def list_issues(self, owner: str, repo: str, state: str = "open", labels: str = "", sort: str = "updated", per_page: int = 30) -> Dict:
        """List repository issues"""
        params = {
            "state": state,
            "sort": sort,
            "per_page": per_page
        }
        
        if labels:
            params["labels"] = labels
        
        endpoint = f"repos/{owner}/{repo}/issues"
        return self.make_request("GET", endpoint, params=params)
    
    def create_issue(self, owner: str, repo: str, title: str, body: str = "", assignees: List[str] = None, labels: List[str] = None) -> Dict:
        """Create new issue"""
        data = {
            "title": title,
            "body": body
        }
        
        if assignees:
            data["assignees"] = assignees
        if labels:
            data["labels"] = labels
        
        endpoint = f"repos/{owner}/{repo}/issues"
        return self.make_request("POST", endpoint, data=data)
    
    def list_commits(self, owner: str, repo: str, sha: str = "", path: str = "", since: str = "", until: str = "", per_page: int = 30) -> Dict:
        """List repository commits"""
        params = {"per_page": per_page}
        
        if sha:
            params["sha"] = sha
        if path:
            params["path"] = path
        if since:
            params["since"] = since
        if until:
            params["until"] = until
        
        endpoint = f"repos/{owner}/{repo}/commits"
        return self.make_request("GET", endpoint, params=params)
    
    def get_file_content(self, owner: str, repo: str, path: str, ref: str = "") -> Dict:
        """Get file content from repository"""
        params = {}
        if ref:
            params["ref"] = ref
        
        endpoint = f"repos/{owner}/{repo}/contents/{path}"
        result = self.make_request("GET", endpoint, params=params)
        
        # Decode base64 content if available
        if result.get("success") and "content" in result.get("data", {}):
            import base64
            try:
                encoded_content = result["data"]["content"].replace('\n', '')
                decoded_content = base64.b64decode(encoded_content).decode('utf-8')
                result["data"]["decoded_content"] = decoded_content
            except Exception as e:
                result["decode_error"] = str(e)
        
        return result
    
    def list_pull_requests(self, owner: str, repo: str, state: str = "open", head: str = "", base: str = "", sort: str = "created", per_page: int = 30) -> Dict:
        """List pull requests"""
        params = {
            "state": state,
            "sort": sort,
            "per_page": per_page
        }
        
        if head:
            params["head"] = head
        if base:
            params["base"] = base
        
        endpoint = f"repos/{owner}/{repo}/pulls"
        return self.make_request("GET", endpoint, params=params)
    
    def search_code(self, query: str, sort: str = "best-match", per_page: int = 30) -> Dict:
        """Search code across GitHub"""
        params = {
            "q": query,
            "sort": sort,
            "per_page": per_page
        }
        
        endpoint = "search/code"
        return self.make_request("GET", endpoint, params=params)
    
    def handle_tool_call(self, tool_name: str, arguments: Dict) -> Dict:
        """Handle GitHub tool calls"""
        try:
            if tool_name == "github_list_repos":
                return self.list_repos(**arguments)
            elif tool_name == "github_get_repo_info":
                return self.get_repo_info(**arguments) 
            elif tool_name == "github_list_issues":
                return self.list_issues(**arguments)
            elif tool_name == "github_create_issue":
                return self.create_issue(**arguments)
            elif tool_name == "github_list_commits":
                return self.list_commits(**arguments)
            elif tool_name == "github_get_file_content":
                return self.get_file_content(**arguments)
            elif tool_name == "github_list_pull_requests":
                return self.list_pull_requests(**arguments)
            elif tool_name == "github_search_code":
                return self.search_code(**arguments)
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}
                
        except Exception as e:
            return {"success": False, "error": f"Tool execution failed: {str(e)}"}

def main():
    """Main MCP server loop for GitHub integration"""
    server = GitHubMCPServer()
    
    print("🐙 GitHub MCP Server Started", file=sys.stderr)
    print(f"🔑 GitHub Token: {'✅ Configured' if server.github_token else '❌ Missing'}", file=sys.stderr)
    
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
                            "name": "GitHub MCP Server",
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