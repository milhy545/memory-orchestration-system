#!/usr/bin/env python3
"""
Network MCP Service - HTTP requests, API calls, webhooks
Port: 8006
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
import httpx
import json
import socket
import ssl
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging
import uuid
from urllib.parse import urlparse
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Network MCP Service",
    description="HTTP requests, API calls, webhooks, and network diagnostics",
    version="1.0.0"
)

# Request/Response Models
class HttpRequest(BaseModel):
    """HTTP request configuration"""
    url: HttpUrl
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    body: Optional[Union[str, Dict]] = None
    timeout: Optional[int] = 30
    follow_redirects: Optional[bool] = True

class HttpResponse(BaseModel):
    """HTTP response data"""
    status_code: int
    headers: Dict[str, str]
    body: str
    response_time: float
    url: str
    redirected: bool = False

class WebhookConfig(BaseModel):
    """Webhook configuration"""
    webhook_id: str
    url: HttpUrl
    secret: Optional[str] = None
    events: List[str] = []
    active: bool = True

class DnsLookup(BaseModel):
    """DNS lookup request"""
    hostname: str
    record_type: str = "A"  # A, AAAA, MX, CNAME, TXT, NS

class ApiTestConfig(BaseModel):
    """API testing configuration"""
    base_url: HttpUrl
    endpoints: List[str]
    headers: Optional[Dict[str, str]] = None
    expected_status: int = 200

# In-memory storage for webhooks (in production, use Redis/DB)
active_webhooks: Dict[str, WebhookConfig] = {}
webhook_logs: List[Dict] = []

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Network MCP",
        "port": 8006,
        "timestamp": datetime.now().isoformat(),
        "features": ["http_requests", "webhooks", "dns_lookup", "api_testing"]
    }

@app.post("/tools/http_request")
async def http_request_tool(request: HttpRequest) -> HttpResponse:
    """
    Execute HTTP request with comprehensive response data
    
    Tool: http_request
    Description: Make HTTP requests to any URL with custom headers and body
    """
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(follow_redirects=request.follow_redirects) as client:
            # Prepare request data
            kwargs = {
                "method": request.method.upper(),
                "url": str(request.url),
                "timeout": request.timeout or 30
            }
            
            if request.headers:
                kwargs["headers"] = request.headers
                
            if request.body:
                if isinstance(request.body, dict):
                    kwargs["json"] = request.body
                else:
                    kwargs["content"] = request.body
            
            # Execute request
            response = await client.request(**kwargs)
            response_time = time.time() - start_time
            
            # Build response object
            return HttpResponse(
                status_code=response.status_code,
                headers=dict(response.headers),
                body=response.text,
                response_time=response_time,
                url=str(response.url),
                redirected=(str(response.url) != str(request.url))
            )
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="Request timeout")
    except Exception as e:
        logger.error(f"HTTP request failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")

@app.post("/tools/webhook_create")
async def webhook_create_tool(config: WebhookConfig) -> Dict[str, Any]:
    """
    Create and register a webhook endpoint
    
    Tool: webhook_create
    Description: Create webhook endpoints for receiving external notifications
    """
    if not config.webhook_id:
        config.webhook_id = str(uuid.uuid4())
    
    # Store webhook configuration
    active_webhooks[config.webhook_id] = config
    
    # Generate webhook URL
    webhook_url = f"http://localhost:8006/webhooks/{config.webhook_id}"
    
    logger.info(f"Created webhook {config.webhook_id} for URL: {config.url}")
    
    return {
        "webhook_id": config.webhook_id,
        "webhook_url": webhook_url,
        "target_url": str(config.url),
        "events": config.events,
        "active": config.active,
        "created_at": datetime.now().isoformat()
    }

@app.post("/webhooks/{webhook_id}")
async def webhook_receiver(webhook_id: str, payload: Dict[str, Any], background_tasks: BackgroundTasks):
    """Receive webhook payloads and forward them"""
    
    if webhook_id not in active_webhooks:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    webhook_config = active_webhooks[webhook_id]
    
    if not webhook_config.active:
        raise HTTPException(status_code=410, detail="Webhook inactive")
    
    # Log webhook receipt
    log_entry = {
        "webhook_id": webhook_id,
        "timestamp": datetime.now().isoformat(),
        "payload": payload,
        "source_ip": "unknown"  # In production, get from request
    }
    webhook_logs.append(log_entry)
    
    # Forward to target URL in background
    background_tasks.add_task(forward_webhook, webhook_config, payload)
    
    return {"status": "received", "webhook_id": webhook_id}

async def forward_webhook(config: WebhookConfig, payload: Dict[str, Any]):
    """Forward webhook payload to target URL"""
    try:
        async with httpx.AsyncClient() as client:
            headers = {"Content-Type": "application/json"}
            if config.secret:
                headers["X-Webhook-Secret"] = config.secret
                
            response = await client.post(
                str(config.url),
                json=payload,
                headers=headers,
                timeout=30
            )
            
            logger.info(f"Forwarded webhook {config.webhook_id} to {config.url}, status: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Failed to forward webhook {config.webhook_id}: {str(e)}")

@app.post("/tools/dns_lookup")
async def dns_lookup_tool(lookup: DnsLookup) -> Dict[str, Any]:
    """
    Perform DNS lookup with support for multiple record types
    
    Tool: dns_lookup  
    Description: Look up DNS records for hostnames (A, AAAA, MX, CNAME, TXT, NS)
    """
    try:
        import dns.resolver
        
        resolver = dns.resolver.Resolver()
        resolver.timeout = 10
        
        # Perform DNS query
        answers = resolver.resolve(lookup.hostname, lookup.record_type)
        
        results = []
        for answer in answers:
            results.append(str(answer))
        
        return {
            "hostname": lookup.hostname,
            "record_type": lookup.record_type,
            "results": results,
            "ttl": answers.ttl if hasattr(answers, 'ttl') else None,
            "timestamp": datetime.now().isoformat()
        }
        
    except ImportError:
        # Fallback to socket for basic A record lookup
        if lookup.record_type.upper() == "A":
            try:
                ip = socket.gethostbyname(lookup.hostname)
                return {
                    "hostname": lookup.hostname,
                    "record_type": "A",
                    "results": [ip],
                    "ttl": None,
                    "timestamp": datetime.now().isoformat(),
                    "method": "socket_fallback"
                }
            except socket.gaierror as e:
                raise HTTPException(status_code=404, detail=f"DNS resolution failed: {str(e)}")
        else:
            raise HTTPException(status_code=501, detail="Advanced DNS lookup requires dnspython package")
            
    except Exception as e:
        logger.error(f"DNS lookup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"DNS lookup failed: {str(e)}")

@app.post("/tools/api_test")
async def api_test_tool(config: ApiTestConfig) -> Dict[str, Any]:
    """
    Test multiple API endpoints for availability and response times
    
    Tool: api_test
    Description: Test API endpoints for availability, response times, and expected status codes
    """
    results = []
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        for endpoint in config.endpoints:
            endpoint_start = time.time()
            
            try:
                # Construct full URL
                if endpoint.startswith('/'):
                    full_url = str(config.base_url).rstrip('/') + endpoint
                else:
                    full_url = f"{config.base_url}/{endpoint.lstrip('/')}"
                
                # Make request
                response = await client.get(
                    full_url,
                    headers=config.headers or {},
                    timeout=30
                )
                
                endpoint_time = time.time() - endpoint_start
                
                # Check if status matches expected
                status_ok = response.status_code == config.expected_status
                
                results.append({
                    "endpoint": endpoint,
                    "url": full_url,
                    "status_code": response.status_code,
                    "expected_status": config.expected_status,
                    "status_ok": status_ok,
                    "response_time": endpoint_time,
                    "content_length": len(response.content),
                    "headers": dict(response.headers)
                })
                
            except Exception as e:
                endpoint_time = time.time() - endpoint_start
                results.append({
                    "endpoint": endpoint,
                    "url": full_url if 'full_url' in locals() else endpoint,
                    "status_code": None,
                    "expected_status": config.expected_status,
                    "status_ok": False,
                    "response_time": endpoint_time,
                    "error": str(e)
                })
    
    total_time = time.time() - start_time
    successful = sum(1 for r in results if r.get("status_ok", False))
    
    return {
        "base_url": str(config.base_url),
        "total_endpoints": len(config.endpoints),
        "successful_endpoints": successful,
        "failed_endpoints": len(config.endpoints) - successful,
        "total_time": total_time,
        "average_response_time": total_time / len(config.endpoints) if config.endpoints else 0,
        "results": results,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/tools/list")
async def list_tools():
    """List all available MCP tools"""
    return {
        "tools": [
            {
                "name": "http_request",
                "description": "Make HTTP requests to any URL with custom headers and body",
                "parameters": {
                    "url": "string (required)",
                    "method": "string (default: GET)",
                    "headers": "object (optional)",
                    "body": "string|object (optional)",
                    "timeout": "integer (default: 30)",
                    "follow_redirects": "boolean (default: true)"
                }
            },
            {
                "name": "webhook_create",
                "description": "Create webhook endpoints for receiving external notifications",
                "parameters": {
                    "webhook_id": "string (optional, auto-generated)",
                    "url": "string (required)",
                    "secret": "string (optional)",
                    "events": "array (optional)",
                    "active": "boolean (default: true)"
                }
            },
            {
                "name": "dns_lookup",
                "description": "Look up DNS records for hostnames (A, AAAA, MX, CNAME, TXT, NS)",
                "parameters": {
                    "hostname": "string (required)",
                    "record_type": "string (default: A)"
                }
            },
            {
                "name": "api_test",
                "description": "Test API endpoints for availability, response times, and status codes",
                "parameters": {
                    "base_url": "string (required)",
                    "endpoints": "array (required)",
                    "headers": "object (optional)",
                    "expected_status": "integer (default: 200)"
                }
            }
        ]
    }

@app.get("/webhooks")
async def list_webhooks():
    """List all active webhooks"""
    return {
        "active_webhooks": len(active_webhooks),
        "webhooks": [
            {
                "webhook_id": wid,
                "target_url": str(config.url),
                "events": config.events,
                "active": config.active
            }
            for wid, config in active_webhooks.items()
        ]
    }

@app.get("/webhook-logs")
async def get_webhook_logs(limit: int = 50):
    """Get recent webhook logs"""
    return {
        "total_logs": len(webhook_logs),
        "logs": webhook_logs[-limit:] if webhook_logs else []
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)