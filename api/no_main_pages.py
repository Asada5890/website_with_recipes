from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from core.security import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/about", response_class=HTMLResponse)
async def information_page(request: Request, current_user=Depends(get_current_user)):
    

    return templates.TemplateResponse(
        "information.html",
        {"request": request, "user": current_user}
    )
