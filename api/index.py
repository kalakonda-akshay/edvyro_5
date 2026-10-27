from app.main import app as fastapi_app
from fastapi.responses import JSONResponse


async def app(scope, receive, send):
    if scope["type"] == "http":
        headers = dict(scope.get("headers", []))
        # Check what Vercel sends
        path = scope.get("path", "")
        # Vercel sends x-forwarded-uri or x-matched-path or x-real-ip
        forwarded_path = headers.get(b"x-forwarded-uri", b"").decode("utf-8") or headers.get(b"x-matched-path", b"").decode("utf-8")
        if forwarded_path:
            scope["path"] = forwarded_path
        elif path.startswith("/api/index.py"):
            scope["path"] = path.replace("/api/index.py", "") or "/"
        elif path.startswith("/api/index"):
            scope["path"] = path.replace("/api/index", "") or "/"

    await fastapi_app(scope, receive, send)
