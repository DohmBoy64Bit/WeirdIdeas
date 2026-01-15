from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from starlette.responses import HTMLResponse

limiter = Limiter(key_func=get_remote_address)

def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return HTMLResponse(
        content="""
        <html>
            <head><title>Rate Limit Exceeded</title></head>
            <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <h1>Too Many Requests</h1>
                <p>You've made too many requests. Please try again later.</p>
                <a href="/">Return Home</a>
            </body>
        </html>
        """,
        status_code=429
    )
