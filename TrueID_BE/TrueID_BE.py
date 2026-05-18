import reflex as rx
from TrueID_BE.api import app as fastapi_app

def index() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.badge("TrueID backend console", color_scheme="amber", variant="surface"),
            rx.heading("Caller identity API is ready.", size="8"),
            rx.text(
                "Use FastAPI for the mobile-facing API and keep this Reflex page as a lightweight internal console placeholder.",
                size="4",
                color_scheme="gray",
            ),
            rx.vstack(
                rx.text("GET /health"),
                rx.text("POST /api/v1/lookup"),
                rx.text("POST /api/v1/report-spam"),
                rx.text("POST /api/v1/upload-contacts"),
                align="start",
                spacing="2",
                width="100%",
            ),
            rx.link("Open API docs", href="/docs", is_external=True),
            align="start",
            spacing="6",
            width="100%",
            max_width="720px",
        ),
        padding="48px",
        min_height="100vh",
        background="linear-gradient(180deg, #fffaf0 0%, #f4efe3 100%)",
    )

app = rx.App(api_transformer=fastapi_app)
app.add_page(index)
