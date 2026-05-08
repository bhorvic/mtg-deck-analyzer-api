from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes.decks import router as deck_router
from app.core.config import settings
from app.core.rate_limit import SlidingWindowRateLimiter

app = FastAPI(title=settings.app_name, version=settings.version)
app.include_router(deck_router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
analyze_rate_limiter = SlidingWindowRateLimiter(
    max_requests=settings.analyze_rate_limit_requests,
    window_seconds=settings.analyze_rate_limit_window_seconds,
)


def get_request_ip(request: Request) -> str:
    forwarded_ip = request.headers.get("cf-connecting-ip") or request.headers.get("x-forwarded-for")
    if forwarded_ip:
        return forwarded_ip.split(",", 1)[0].strip()
    return request.client.host if request.client else "unknown"


@app.middleware("http")
async def rate_limit_analyze_requests(request: Request, call_next):
    if request.method == "POST" and request.url.path == "/deck/analyze":
        allowed, retry_after = analyze_rate_limiter.allow(get_request_ip(request))
        if not allowed:
            return JSONResponse(
                status_code=429,
                headers={"Retry-After": str(int(retry_after))},
                content={
                    "detail": "Rate limit reached for deck analysis. Please wait a minute and try again.",
                },
            )
    return await call_next(request)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
