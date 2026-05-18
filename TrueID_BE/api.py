from functools import lru_cache

from fastapi import HTTPException
from pydantic import ValidationError
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from TrueID_BE.config import Settings, get_settings
from TrueID_BE.repository import BaseRepository, build_repository
from TrueID_BE.schemas import (
    HealthResponse,
    LookupRequest,
    SpamReportRequest,
    UploadContactsRequest,
)
from TrueID_BE.services.identity import IdentityService


def create_app() -> Starlette:
    settings = get_settings()
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ]

    return Starlette(
        debug=settings.environment == "development",
        middleware=middleware,
        routes=[
            Route("/health", endpoint=health_check, methods=["GET"]),
            Route(f"{settings.api_prefix}/lookup", endpoint=lookup_caller, methods=["POST"]),
            Route(f"{settings.api_prefix}/report-spam", endpoint=report_spam, methods=["POST"]),
            Route(
                f"{settings.api_prefix}/upload-contacts",
                endpoint=upload_contacts,
                methods=["POST"],
            ),
        ],
    )


async def health_check(_: Request) -> JSONResponse:
    current_settings = get_settings()
    payload = HealthResponse(
        status="ok",
        environment=current_settings.environment,
        backend=current_settings.resolved_backend,
    )
    return JSONResponse(payload.model_dump(mode="json"))


async def lookup_caller(request: Request) -> JSONResponse:
    payload = await _parse_body(request, LookupRequest)
    service = get_identity_service()
    response = service.lookup(payload.phone_number)
    return JSONResponse(response.model_dump(mode="json"))


async def report_spam(request: Request) -> JSONResponse:
    payload = await _parse_body(request, SpamReportRequest)
    service = get_identity_service()
    response = service.report_spam(
        phone_number=payload.phone_number,
        reason=payload.reason,
        reporter_id=payload.reporter_id,
        notes=payload.notes,
    )
    return JSONResponse(response.model_dump(mode="json"))


async def upload_contacts(request: Request) -> JSONResponse:
    payload = await _parse_body(request, UploadContactsRequest)
    service = get_identity_service()
    response = service.upload_contacts(payload.user_id, payload.contacts)
    return JSONResponse(response.model_dump(mode="json"))


async def _parse_body(request: Request, schema):
    try:
        body = await request.json()
        return schema.model_validate(body)
    except ValidationError as error:
        return _raise_http_exception(422, error.errors())
    except ValueError as error:
        return _raise_http_exception(400, str(error))


def _raise_http_exception(status_code: int, detail):
    raise HTTPException(status_code=status_code, detail=detail)


@lru_cache
def get_repository() -> BaseRepository:
    return build_repository(get_settings())


def get_identity_service() -> IdentityService:
    return IdentityService(repository=get_repository(), settings=get_settings())


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


app = create_app()
app.add_exception_handler(HTTPException, http_exception_handler)
