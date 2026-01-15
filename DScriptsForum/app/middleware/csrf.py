import secrets
from starlette.types import ASGIApp, Scope, Receive, Send
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.datastructures import MutableHeaders

class CSRFMiddleware:
    def __init__(self, app: ASGIApp, secret_key: str):
        self.app = app
        self.exempt_paths = ["/docs", "/redoc", "/openapi.json", "/static"]
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        
        # 1. Get token from cookie or create new one
        cookie_token = request.cookies.get("csrf_token")
        if not cookie_token:
            cookie_token = secrets.token_urlsafe(32)
            is_new_token = True
        else:
            is_new_token = False
            
        # Make token available to templates via request.state.csrf_token
        scope.setdefault("state", {})["csrf_token"] = cookie_token
        
        # 2. Skip validation for safe methods and exempt paths
        is_safe = request.method in ("GET", "HEAD", "OPTIONS", "TRACE")
        is_exempt = any(request.url.path.startswith(path) for path in self.exempt_paths)
        
        if is_safe or is_exempt:
            async def send_wrapper(message: Send):
                if message["type"] == "http.response.start":
                    if is_new_token or request.method == "GET":
                        headers = MutableHeaders(scope=message)
                        headers.append("Set-Cookie", f"csrf_token={cookie_token}; Path=/; SameSite=Lax; HttpOnly")
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
            return

        # 3. For POST, PUT, DELETE, PATCH: Validate CSRF
        # Read body to check form data
        body = await request.body()
        
        # Parse form data
        async def mock_receive():
            return {"type": "http.request", "body": body}
            
        temp_request = Request(scope, receive=mock_receive)
        try:
            form_data = await temp_request.form()
            form_token = form_data.get("csrf_token")
        except Exception as e:
            print(f"Error parsing form data in CSRF middleware: {e}")
            form_token = None
            
        if not cookie_token or not form_token or cookie_token != form_token:
            print(f"CSRF Validation Failed: Cookie({cookie_token}) != Form({form_token})")
            response = HTMLResponse(
                content="""
                <html>
                    <head><title>CSRF Validation Failed</title></head>
                    <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                        <h1>Security Error</h1>
                        <p>CSRF token missing or invalid. Please refresh the page and try again.</p>
                        <a href="javascript:history.back()">Go Back</a>
                    </body>
                </html>
                """,
                status_code=403
            )
            await response(scope, receive, send)
            return

        # 4. Replay body for FastAPI
        async def receive_with_body():
            return {"type": "http.request", "body": body}

        await self.app(scope, receive_with_body, send)
