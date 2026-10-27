from app.main import app as fastapi_app


class VercelPathMiddleware:
    """Adjusts ASGI scope['path'] when running behind Vercel serverless rewrites."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            path = scope.get("path", "")
            for prefix in ["/api/index.py", "/api/index", "/api"]:
                if path == prefix:
                    scope["path"] = "/"
                    break
                elif path.startswith(prefix + "/"):
                    scope["path"] = path[len(prefix):]
                    break
        await self.app(scope, receive, send)


app = VercelPathMiddleware(fastapi_app)
