#!/usr/bin/env python3
"""
Simple HTTP proxy for Render deployment
Routes traffic between Flask (frontend) and FastAPI (backend)
"""

import asyncio
import aiohttp
from aiohttp import web, ClientSession
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
FLASK_HOST = "127.0.0.1"
FLASK_PORT = 5000
FASTAPI_HOST = "127.0.0.1"
FASTAPI_PORT = 8000
PROXY_PORT = int(os.environ.get('PORT', 10000))

class ReverseProxy:
    def __init__(self):
        self.session = None
    
    async def init_session(self):
        """Initialize HTTP session"""
        self.session = ClientSession()
    
    async def close_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    async def health_check(self, request):
        """Health check endpoint"""
        try:
            # Check Flask
            flask_url = f"http://{FLASK_HOST}:{FLASK_PORT}/health"
            async with self.session.get(flask_url, timeout=5) as resp:
                flask_ok = resp.status == 200
            
            # Check FastAPI
            fastapi_url = f"http://{FASTAPI_HOST}:{FASTAPI_PORT}/health"
            async with self.session.get(fastapi_url, timeout=5) as resp:
                fastapi_ok = resp.status == 200
            
            if flask_ok and fastapi_ok:
                return web.json_response({
                    "status": "healthy",
                    "flask": "ok",
                    "fastapi": "ok",
                    "proxy": "ok"
                })
            else:
                return web.json_response({
                    "status": "unhealthy",
                    "flask": "ok" if flask_ok else "error",
                    "fastapi": "ok" if fastapi_ok else "error"
                }, status=503)
        
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return web.json_response({
                "status": "error",
                "message": str(e)
            }, status=503)
    
    async def proxy_to_fastapi(self, request):
        """Proxy API requests to FastAPI"""
        try:
            # Construct target URL
            path = request.path_qs.replace("/api", "", 1)
            target_url = f"http://{FASTAPI_HOST}:{FASTAPI_PORT}{path}"
            
            # Prepare headers
            headers = dict(request.headers)
            headers.pop('Host', None)
            
            # Forward request
            async with self.session.request(
                method=request.method,
                url=target_url,
                headers=headers,
                data=await request.read(),
                timeout=30
            ) as resp:
                # Read response
                body = await resp.read()
                
                # Return response
                return web.Response(
                    body=body,
                    status=resp.status,
                    headers=resp.headers
                )
        
        except Exception as e:
            logger.error(f"FastAPI proxy error: {e}")
            return web.json_response({
                "error": "Backend service unavailable"
            }, status=503)
    
    async def proxy_to_flask(self, request):
        """Proxy web requests to Flask"""
        try:
            # Construct target URL
            target_url = f"http://{FLASK_HOST}:{FLASK_PORT}{request.path_qs}"
            
            # Prepare headers
            headers = dict(request.headers)
            headers.pop('Host', None)
            
            # Forward request
            async with self.session.request(
                method=request.method,
                url=target_url,
                headers=headers,
                data=await request.read(),
                timeout=30
            ) as resp:
                # Read response
                body = await resp.read()
                
                # Return response
                return web.Response(
                    body=body,
                    status=resp.status,
                    headers=resp.headers
                )
        
        except Exception as e:
            logger.error(f"Flask proxy error: {e}")
            return web.json_response({
                "error": "Frontend service unavailable"
            }, status=503)

async def create_app():
    """Create and configure the proxy application"""
    proxy = ReverseProxy()
    await proxy.init_session()
    
    app = web.Application()
    
    # Health check
    app.router.add_get('/health', proxy.health_check)
    app.router.add_head('/health', proxy.health_check)
    
    # API routes to FastAPI
    app.router.add_route('*', '/api/{path:.*}', proxy.proxy_to_fastapi)
    
    # All other routes to Flask
    app.router.add_route('*', '/{path:.*}', proxy.proxy_to_flask)
    
    # Cleanup on shutdown
    async def cleanup(app):
        await proxy.close_session()
    
    app.on_cleanup.append(cleanup)
    
    return app

async def main():
    """Main entry point"""
    logger.info(f"Starting proxy server on port {PROXY_PORT}")
    logger.info(f"Flask backend: {FLASK_HOST}:{FLASK_PORT}")
    logger.info(f"FastAPI backend: {FASTAPI_HOST}:{FASTAPI_PORT}")
    
    app = await create_app()
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', PROXY_PORT)
    await site.start()
    
    logger.info("Proxy server started successfully")
    
    # Keep running
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        logger.info("Shutting down proxy server")
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
