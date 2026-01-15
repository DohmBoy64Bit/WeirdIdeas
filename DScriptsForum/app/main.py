from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from app.config import settings
from app.routes import auth_routes, forum_routes, script_routes
from app.utils.security import create_access_token
from app.services import script_service
from app.extensions import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.utils.rate_limit import limiter, rate_limit_exceeded_handler
from app.middleware.csrf import CSRFMiddleware

# Lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: could run migrations here if desired, or init connections
    print(f"Starting up {settings.PROJECT_NAME}")
    yield
    # Shutdown
    print("Shutting down...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Rate Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# CSRF Protection
app.add_middleware(CSRFMiddleware, secret_key=settings.SECRET_KEY)

# Mount Static Files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Routes
app.include_router(auth_routes.router)
app.include_router(forum_routes.router)
app.include_router(script_routes.router)
from app.routes import admin_routes, notification_routes, user_routes
app.include_router(admin_routes.router)
app.include_router(notification_routes.router)
app.include_router(user_routes.router)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' cdn.tailwindcss.com unpkg.com cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' cdn.tailwindcss.com; "
        "img-src 'self' data:; "
        "font-src 'self';"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Home Route
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: AsyncSession = Depends(get_db)):
    # Fetch real data
    recent_scripts = await script_service.get_recent_scripts(db, limit=6)
    trending_scripts = await script_service.get_trending_scripts(db, limit=3)
    
    # Get user (optional)
    from app.dependencies import get_current_user_opt
    user = await get_current_user_opt(request, db)
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "user": user,
        "recent_scripts": recent_scripts,
        "trending_scripts": trending_scripts
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
