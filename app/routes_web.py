from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(directory="templates")
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/events", response_class=HTMLResponse)
def events(request: Request):
    return templates.TemplateResponse("events.html", {"request": request})


@router.get("/blocked", response_class=HTMLResponse)
def blocked(request: Request):
    return templates.TemplateResponse("blocked.html", {"request": request})


@router.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})
