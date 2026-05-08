from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes.decks import router as deck_router
from app.core.config import settings

app = FastAPI(title=settings.app_name, version=settings.version)
app.include_router(deck_router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
