from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

register_router = APIRouter()
templates = Jinja2Templates(directory="frontend/templates/register")


@register_router.get("/autheticate", response_class=HTMLResponse)
async def get_autheticate(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
    )
