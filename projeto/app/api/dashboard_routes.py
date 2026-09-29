from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

dashboard_router = APIRouter()
templates = Jinja2Templates(directory="frontend/templates/dashboard")


@dashboard_router.get("/dashboards", response_class=HTMLResponse)
async def get_dashboards(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
    )
