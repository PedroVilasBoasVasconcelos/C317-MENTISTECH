from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

hero_router = APIRouter()
templates = Jinja2Templates(directory="frontend/templates/hero")


@hero_router.get("/initial", response_class=HTMLResponse)
async def get_hero(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="hero.html",
    )