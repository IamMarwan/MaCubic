import os
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine, get_db
from app.models import Document, User
from app.security import (
    create_session_token,
    hash_password,
    read_session_token,
    verify_password,
)
from app.services import format_file_size, save_and_analyze_upload

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "change-this-secret-before-production",
)

UPLOAD_DIR = PROJECT_DIR / os.getenv(
    "UPLOAD_DIR",
    "data/uploads",
)

SESSION_COOKIE = "week17_session"


def seed_admin_user() -> None:
    admin_email = os.getenv(
        "ADMIN_EMAIL",
        "admin@cubic.local",
    ).strip().lower()

    admin_password = os.getenv(
        "ADMIN_PASSWORD",
        "Admin123!",
    )

    admin_name = os.getenv(
        "ADMIN_NAME",
        "System Administrator",
    )

    with SessionLocal() as database:
        existing_admin = database.scalar(
            select(User).where(
                User.email == admin_email
            )
        )

        if existing_admin:
            return

        admin = User(
            full_name=admin_name,
            email=admin_email,
            password_hash=hash_password(admin_password),
            role="admin",
            is_active=True,
        )

        database.add(admin)
        database.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    Base.metadata.create_all(bind=engine)
    seed_admin_user()

    yield


app = FastAPI(
    title="Final AI Document Control Assistant",
    version="1.0.0",
    description=(
        "Production-ready document management "
        "and analysis application."
    ),
    lifespan=lifespan,
)

app.mount(
    "/static",
    StaticFiles(
        directory=str(BASE_DIR / "static")
    ),
    name="static",
)

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)

templates.env.filters["filesize"] = format_file_size


def get_current_user(
    request: Request,
    database: Session,
) -> User | None:
    token = request.cookies.get(SESSION_COOKIE)

    session_data = read_session_token(
        SECRET_KEY,
        token,
    )

    if not session_data:
        return None

    user = database.get(
        User,
        session_data["user_id"],
    )

    if not user or not user.is_active:
        return None

    return user


def redirect_with_message(
    path: str,
    message: str,
) -> RedirectResponse:
    separator = "&" if "?" in path else "?"

    return RedirectResponse(
        url=f"{path}{separator}message={quote(message)}",
        status_code=303,
    )


@app.get("/health")
def health_check() -> dict:
    return {
        "status": "healthy",
        "application": (
            "Final AI Document Control Assistant"
        ),
        "version": "1.0.0",
    }


@app.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    database: Session = Depends(get_db),
):
    user = get_current_user(
        request,
        database,
    )

    if user:
        return RedirectResponse(
            "/dashboard",
            status_code=303,
        )

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "user": None,
        },
    )


@app.get("/register", response_class=HTMLResponse)
def register_page(
    request: Request,
    database: Session = Depends(get_db),
):
    if get_current_user(request, database):
        return RedirectResponse(
            "/dashboard",
            status_code=303,
        )

    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={
            "user": None,
            "error": None,
        },
    )


@app.post("/register", response_class=HTMLResponse)
def register_user(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    database: Session = Depends(get_db),
):
    full_name = full_name.strip()
    email = email.strip().lower()

    if len(full_name) < 2:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "user": None,
                "error": (
                    "Full name must contain "
                    "at least two characters."
                ),
            },
            status_code=400,
        )

    if "@" not in email or "." not in email:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "user": None,
                "error": (
                    "Enter a valid email address."
                ),
            },
            status_code=400,
        )

    if len(password) < 6:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "user": None,
                "error": (
                    "Password must contain "
                    "at least six characters."
                ),
            },
            status_code=400,
        )

    existing_user = database.scalar(
        select(User).where(
            User.email == email
        )
    )

    if existing_user:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "user": None,
                "error": (
                    "An account with this "
                    "email already exists."
                ),
            },
            status_code=400,
        )

    user = User(
        full_name=full_name,
        email=email,
        password_hash=hash_password(password),
        role="user",
        is_active=True,
    )

    database.add(user)
    database.commit()
    database.refresh(user)

    token = create_session_token(
        SECRET_KEY,
        user.id,
    )

    response = RedirectResponse(
        "/dashboard",
        status_code=303,
    )

    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60 * 8,
    )

    return response


@app.get("/login", response_class=HTMLResponse)
def login_page(
    request: Request,
    database: Session = Depends(get_db),
):
    if get_current_user(request, database):
        return RedirectResponse(
            "/dashboard",
            status_code=303,
        )

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "user": None,
            "error": None,
        },
    )


@app.post("/login", response_class=HTMLResponse)
def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    database: Session = Depends(get_db),
):
    email = email.strip().lower()

    user = database.scalar(
        select(User).where(
            User.email == email
        )
    )

    if not user or not verify_password(
        password,
        user.password_hash,
    ):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "user": None,
                "error": (
                    "Incorrect email or password."
                ),
            },
            status_code=400,
        )

    if not user.is_active:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "user": None,
                "error": (
                    "This account is inactive."
                ),
            },
            status_code=403,
        )

    token = create_session_token(
        SECRET_KEY,
        user.id,
    )

    response = RedirectResponse(
        "/dashboard",
        status_code=303,
    )

    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60 * 8,
    )

    return response


@app.get("/logout")
def logout():
    response = RedirectResponse(
        "/",
        status_code=303,
    )

    response.delete_cookie(SESSION_COOKIE)

    return response


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    search: str = "",
    database: Session = Depends(get_db),
):
    user = get_current_user(
        request,
        database,
    )

    if not user:
        return RedirectResponse(
            "/login",
            status_code=303,
        )

    query = select(Document).order_by(
        Document.uploaded_at.desc()
    )

    if user.role != "admin":
        query = query.where(
            Document.owner_id == user.id
        )

    if search.strip():
        search_term = f"%{search.strip()}%"

        query = query.where(
            or_(
                Document.original_name.ilike(
                    search_term
                ),
                Document.summary.ilike(
                    search_term
                ),
                Document.keywords.ilike(
                    search_term
                ),
            )
        )

    documents = list(
        database.scalars(query).all()
    )

    if user.role == "admin":
        total_documents = database.scalar(
            select(func.count(Document.id))
        ) or 0

        total_users = database.scalar(
            select(func.count(User.id))
        ) or 0
    else:
        total_documents = database.scalar(
            select(func.count(Document.id)).where(
                Document.owner_id == user.id
            )
        ) or 0

        total_users = 0

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "user": user,
            "documents": documents,
            "search": search,
            "total_documents": total_documents,
            "total_users": total_users,
        },
    )


@app.post("/documents/upload")
async def upload_document(
    request: Request,
    document: UploadFile = File(...),
    database: Session = Depends(get_db),
):
    user = get_current_user(
        request,
        database,
    )

    if not user:
        return RedirectResponse(
            "/login",
            status_code=303,
        )

    try:
        file_data = await save_and_analyze_upload(
            document,
            UPLOAD_DIR,
        )

    except ValueError as error:
        return redirect_with_message(
            "/dashboard",
            str(error),
        )

    database_document = Document(
        **file_data,
        owner_id=user.id,
    )

    database.add(database_document)
    database.commit()

    return redirect_with_message(
        "/dashboard",
        (
            "Document uploaded and "
            "analyzed successfully."
        ),
    )


@app.get("/documents/{document_id}/download")
def download_document(
    document_id: int,
    request: Request,
    database: Session = Depends(get_db),
):
    user = get_current_user(
        request,
        database,
    )

    if not user:
        return RedirectResponse(
            "/login",
            status_code=303,
        )

    document = database.get(
        Document,
        document_id,
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    if (
        user.role != "admin"
        and document.owner_id != user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    file_path = UPLOAD_DIR / document.stored_name

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Stored file not found",
        )

    return FileResponse(
        path=file_path,
        filename=document.original_name,
        media_type="application/octet-stream",
    )


@app.post("/documents/{document_id}/delete")
def delete_document(
    document_id: int,
    request: Request,
    database: Session = Depends(get_db),
):
    user = get_current_user(
        request,
        database,
    )

    if not user:
        return RedirectResponse(
            "/login",
            status_code=303,
        )

    document = database.get(
        Document,
        document_id,
    )

    if not document:
        return redirect_with_message(
            "/dashboard",
            "Document not found.",
        )

    if (
        user.role != "admin"
        and document.owner_id != user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    file_path = UPLOAD_DIR / document.stored_name

    if file_path.exists():
        file_path.unlink()

    database.delete(document)
    database.commit()

    return redirect_with_message(
        "/dashboard",
        "Document deleted successfully.",
    )


@app.get("/admin/users", response_class=HTMLResponse)
def users_page(
    request: Request,
    database: Session = Depends(get_db),
):
    user = get_current_user(
        request,
        database,
    )

    if not user:
        return RedirectResponse(
            "/login",
            status_code=303,
        )

    if user.role != "admin":
        return RedirectResponse(
            "/dashboard",
            status_code=303,
        )

    users = list(
        database.scalars(
            select(User).order_by(
                User.created_at.desc()
            )
        ).all()
    )

    return templates.TemplateResponse(
        request=request,
        name="users.html",
        context={
            "user": user,
            "users": users,
        },
    )


@app.post("/admin/users/{user_id}/toggle")
def toggle_user_status(
    user_id: int,
    request: Request,
    database: Session = Depends(get_db),
):
    current_user = get_current_user(
        request,
        database,
    )

    if not current_user:
        return RedirectResponse(
            "/login",
            status_code=303,
        )

    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail=(
                "Administrator access required"
            ),
        )

    target_user = database.get(
        User,
        user_id,
    )

    if not target_user:
        return redirect_with_message(
            "/admin/users",
            "User not found.",
        )

    if target_user.id == current_user.id:
        return redirect_with_message(
            "/admin/users",
            (
                "You cannot deactivate "
                "your own account."
            ),
        )

    target_user.is_active = (
        not target_user.is_active
    )

    database.commit()

    return redirect_with_message(
        "/admin/users",
        "User account status updated.",
    )
