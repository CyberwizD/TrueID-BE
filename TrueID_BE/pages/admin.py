import reflex as rx

from TrueID_BE.api import get_repository
from TrueID_BE.schemas import CallLogRecord

class CallLogDisplay(rx.Base):
    id: str
    caller_number: str
    callee_identifier: str
    resolved_name: str
    created_at: str

class AdminState(rx.State):
    call_logs: list[CallLogDisplay] = []

    def load_logs(self):
        repository = get_repository()
        logs = repository.get_call_logs()
        self.call_logs = [
            CallLogDisplay(
                id=str(log.id),
                caller_number=log.caller_number or "Unknown",
                callee_identifier=log.callee_identifier or "Unknown",
                resolved_name=log.resolved_name or "",
                created_at=log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "Unknown"
            )
            for log in logs
        ]
        
        if not self.call_logs:
            self.call_logs = [
                CallLogDisplay(
                    id="dummy",
                    caller_number="No DB Connection",
                    callee_identifier="Or empty table",
                    resolved_name="Check .env vars",
                    created_at="Now"
                )
            ]


def admin_page() -> rx.Component:
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
                        "TrueID Admin",
                        color_scheme="red",
                        variant="surface",
                        radius="full",
                        font_size="0.8rem",
                        padding_x="12px",
                        padding_y="4px",
                    ),
                    rx.spacer(),
                    rx.link(
                        "Back to Home",
                        href="/",
                        color="#d6c3a0",
                        font_weight="600",
                    ),
                    spacing="4",
                    width="100%",
                    align="center",
                ),
                rx.vstack(
                    rx.heading(
                        "Call Log Dashboard",
                        size="9",
                        color="#f5f7fb",
                        line_height="1.1",
                    ),
                    rx.text(
                        "View all recent lookup requests processed by the backend.",
                        color="#9aa5b9",
                        font_size="1.08rem",
                    ),
                    rx.button(
                        "Refresh Logs",
                        on_click=AdminState.load_logs,
                        color_scheme="blue",
                        variant="soft",
                        margin_top="10px",
                    ),
                    spacing="4",
                    align="start",
                    width="100%",
                ),
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Date & Time"),
                                rx.table.column_header_cell("Caller"),
                                rx.table.column_header_cell("Callee"),
                                rx.table.column_header_cell("Resolved Name"),
                            ),
                        ),
                        rx.table.body(
                            rx.foreach(
                                AdminState.call_logs,
                                lambda log: rx.table.row(
                                    rx.table.cell(log.created_at),
                                    rx.table.cell(log.caller_number),
                                    rx.table.cell(log.callee_identifier),
                                    rx.table.cell(log.resolved_name),
                                )
                            )
                        ),
                        width="100%",
                        variant="surface",
                    ),
                    width="100%",
                    margin_top="32px",
                    border="1px solid #1c2532",
                    border_radius="16px",
                    overflow="hidden",
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
