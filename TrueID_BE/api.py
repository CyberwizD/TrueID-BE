from functools import lru_cache

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from TrueID_BE.config import Settings, get_settings
from TrueID_BE.repository import BaseRepository, build_repository
from TrueID_BE.schemas import (
    HealthResponse,
    LookupRequest,
    LookupResponse,
    SpamReportRequest,
    SpamReportResponse,
    UploadContactsRequest,
    UploadContactsResponse,
)
from TrueID_BE.services.identity import IdentityService


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="TrueID caller identification and spam intelligence API",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get("/health", response_model=HealthResponse)
    def health_check(current_settings: Settings = Depends(get_settings)) -> HealthResponse:
        return HealthResponse(
            status="ok",
            environment=current_settings.environment,
            backend=current_settings.resolved_backend,
        )

    @application.post(f"{settings.api_prefix}/lookup", response_model=LookupResponse)
    def lookup_caller(
        payload: LookupRequest,
        service: IdentityService = Depends(get_identity_service),
    ) -> LookupResponse:
        return service.lookup(payload.phone_number)

    @application.post(f"{settings.api_prefix}/report-spam", response_model=SpamReportResponse)
    def report_spam(
        payload: SpamReportRequest,
        service: IdentityService = Depends(get_identity_service),
    ) -> SpamReportResponse:
        return service.report_spam(
            phone_number=payload.phone_number,
            reason=payload.reason,
            reporter_id=payload.reporter_id,
            notes=payload.notes,
        )

    @application.post(
        f"{settings.api_prefix}/upload-contacts",
        response_model=UploadContactsResponse,
    )
    def upload_contacts(
        payload: UploadContactsRequest,
        service: IdentityService = Depends(get_identity_service),
    ) -> UploadContactsResponse:
        return service.upload_contacts(payload.user_id, payload.contacts)

    return application


@lru_cache
def get_repository() -> BaseRepository:
    return build_repository(get_settings())


def get_identity_service(
    repository: BaseRepository = Depends(get_repository),
    settings: Settings = Depends(get_settings),
) -> IdentityService:
    return IdentityService(repository=repository, settings=settings)


app = create_app()
