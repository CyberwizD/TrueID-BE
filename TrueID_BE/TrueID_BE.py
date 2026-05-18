import reflex as rx

from TrueID_BE.api import app as fastapi_app


def code_panel(title: str, body: str) -> rx.Component:
    return rx.vstack(
        rx.text(
            title,
            size="2",
            weight="bold",
            color="#d6c3a0",
            text_transform="uppercase",
            letter_spacing="0.10em",
        ),
        rx.box(
            rx.text(
                body,
                font_family="monospace",
                white_space="pre-wrap",
                font_size="0.92rem",
                line_height="1.7",
                color="#e8edf7",
            ),
            width="100%",
            border="1px solid #242d3a",
            border_radius="20px",
            background="#0e131b",
            padding="20px",
        ),
        align="start",
        spacing="3",
        width="100%",
    )


def endpoint_card(
    method: str,
    path: str,
    summary: str,
    request_example: str,
    response_example: str,
) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.badge(
                    method,
                    color_scheme="gold",
                    variant="solid",
                    radius="full",
                    font_size="0.78rem",
                    padding_x="12px",
                    padding_y="4px",
                ),
                rx.text(
                    path,
                    font_family="monospace",
                    font_size="0.96rem",
                    color="#f5f7fb",
                ),
                spacing="3",
                align="center",
                wrap="wrap",
                width="100%",
            ),
            rx.text(
                summary,
                color="#96a1b5",
                font_size="0.98rem",
                line_height="1.7",
            ),
            code_panel("Request", request_example),
            code_panel("Response", response_example),
            spacing="5",
            align="start",
            width="100%",
        ),
        width="100%",
        border="1px solid #1d2531",
        border_radius="28px",
        background="linear-gradient(180deg, #121821 0%, #0d1218 100%)",
        padding="28px",
        box_shadow="0 18px 80px rgba(0, 0, 0, 0.28)",
    )


def info_card(title: str, body: str) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(
                title,
                color="#f5f7fb",
                font_size="1.05rem",
                font_weight="700",
            ),
            rx.text(
                body,
                color="#96a1b5",
                font_size="0.96rem",
                line_height="1.7",
            ),
            spacing="2",
            align="start",
        ),
        border="1px solid #1c2532",
        border_radius="24px",
        background="#11161f",
        padding="24px",
        width="100%",
    )


def index() -> rx.Component:
    return rx.box(
        rx.box(
            position="absolute",
            inset="0",
            background=(
                "radial-gradient(circle at top left, rgba(198, 166, 105, 0.18), transparent 28%), "
                "radial-gradient(circle at top right, rgba(70, 93, 140, 0.20), transparent 22%), "
                "#070a0f"
            ),
        ),
        rx.container(
            rx.vstack(
                rx.hstack(
                    rx.badge(
                        "TrueID API",
                        color_scheme="gold",
                        variant="surface",
                        radius="full",
                        font_size="0.8rem",
                        padding_x="12px",
                        padding_y="4px",
                    ),
                    rx.spacer(),
                    rx.link(
                        "Health check",
                        href="/health",
                        color="#d6c3a0",
                        font_weight="600",
                    ),
                    spacing="4",
                    width="100%",
                    align="center",
                ),
                rx.vstack(
                    rx.heading(
                        "Caller identity API documentation",
                        size="9",
                        color="#f5f7fb",
                        line_height="1.1",
                        max_width="760px",
                    ),
                    rx.text(
                        "Use the same deployment host as your mobile API base URL. "
                        "The endpoints below describe number lookup, spam reporting, "
                        "and contact contribution for TrueID integrations.",
                        color="#9aa5b9",
                        font_size="1.08rem",
                        line_height="1.8",
                        max_width="760px",
                    ),
                    spacing="4",
                    align="start",
                    width="100%",
                ),
                rx.grid(
                    info_card(
                        "Base URL",
                        "Use the current deployed host. Example: https://your-app.reflex.run",
                    ),
                    info_card(
                        "Authentication",
                        "Phase 1 endpoints are unauthenticated. Add your own gateway or auth layer if you expose this publicly.",
                    ),
                    info_card(
                        "Privacy",
                        "Responses return caller name, spam risk, and broad location only. Exact residential addresses are not exposed.",
                    ),
                    columns="3",
                    spacing="4",
                    width="100%",
                ),
                endpoint_card(
                    "GET",
                    "/health",
                    "Returns service health, deployment environment, and which data backend is active.",
                    "{}",
                    '{\n  "status": "ok",\n  "environment": "development",\n  "backend": "supabase"\n}',
                ),
                endpoint_card(
                    "POST",
                    "/api/v1/lookup",
                    "Looks up a phone number and returns the best-known caller identity, spam status, confidence score, and source signals.",
                    '{\n  "phone_number": "+2348012345678"\n}',
                    '{\n  "phone_number": "+2348012345678",\n  "name": "John Mechanic",\n  "location": "Lekki, Lagos",\n  "spam": false,\n  "confidence": 91,\n  "spam_score": 18,\n  "caller_type": "business",\n  "verified": true,\n  "match_strategy": "verified_profile",\n  "sources": [\n    {\n      "source": "profile",\n      "weight": 45,\n      "label": "Curated caller profile"\n    }\n  ]\n}',
                ),
                endpoint_card(
                    "POST",
                    "/api/v1/report-spam",
                    "Submits a spam or abuse report for a phone number and returns the updated spam status.",
                    '{\n  "phone_number": "+2347011112222",\n  "reason": "loan_spam",\n  "notes": "Aggressive repeat calls"\n}',
                    '{\n  "phone_number": "+2347011112222",\n  "spam_score": 72,\n  "spam": true,\n  "total_reports": 3\n}',
                ),
                endpoint_card(
                    "POST",
                    "/api/v1/upload-contacts",
                    "Uploads approved phone contacts from a device installation so the service can build crowdsourced identity consensus.",
                    '{\n  "user_id": "device-4c5c9c54",\n  "contacts": [\n    {\n      "phone_number": "+2348091234567",\n      "contact_name": "Chiamaka Okafor"\n    },\n    {\n      "phone_number": "+2348112223334",\n      "contact_name": "Tolu Dental Clinic"\n    }\n  ]\n}',
                    '{\n  "uploaded": 2,\n  "unique_numbers": 2,\n  "ignored_duplicates": 0\n}',
                ),
                code_panel(
                    "cURL example",
                    'curl -X POST "$BASE_URL/api/v1/lookup" \\\n  -H "Content-Type: application/json" \\\n  -d \'{\n    "phone_number": "+2348012345678"\n  }\'',
                ),
                rx.text(
                    "Status codes: 200 for success, 400 for malformed JSON, 422 for validation errors.",
                    color="#7f8aa0",
                    font_size="0.92rem",
                ),
                spacing="7",
                align="start",
                width="100%",
                padding_y="56px",
            ),
            max_width="1100px",
            position="relative",
        ),
        min_height="100vh",
        position="relative",
        overflow="hidden",
    )


app = rx.App(api_transformer=fastapi_app)
app.add_page(index, title="TrueID API Docs")
