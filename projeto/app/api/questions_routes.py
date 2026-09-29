from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

questions_router = APIRouter()
templates = Jinja2Templates(directory="frontend/templates/questions")


@questions_router.get("/questions", response_class=HTMLResponse)
async def get_questions(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="questions.html",
    )
