from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

home_router = APIRouter()
templates = Jinja2Templates(directory="frontend/templates/home")


@home_router.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="home.html",
    )
