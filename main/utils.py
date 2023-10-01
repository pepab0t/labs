from typing import Protocol, TYPE_CHECKING
from django.shortcuts import render as _render
from django.http import HttpRequest

if TYPE_CHECKING:
    from .models import LabEvent
    from .forms import ApplyEventForm


class DateFormatable(Protocol):
    def strftime(self, __format: str) -> str:
        ...


REPR_FORMAT = r"%d.%m.%Y %H:%M"
OFFICIAL_FORMAT = r"%Y-%m-%d %H:%M:%S"


def repr_format(d: DateFormatable):
    return d.strftime(REPR_FORMAT)


def official_format(d: DateFormatable):
    return d.strftime(OFFICIAL_FORMAT)


def render_error(request: HttpRequest, errors: list[str]):
    return _render(request, "error_page.html", {"errors": errors})


def render_event_page(
    request: HttpRequest,
    event: "LabEvent",
    form: "ApplyEventForm | None" = None,
    login_message: str = "",
    logout_message: str = "",
    general_error: str = "",
    num_applied_users: int | None = None,
):
    if request.user.is_staff:  # type: ignore
        return _render(
            request,
            "apply_event.html",
            {"event": event},
        )

    return _render(
        request,
        "apply_event.html",
        {
            "event": event,
            "form": form,
            "any_free_topics": form is not None and len(form.choices) != 0,
            "logout_message": logout_message,
            "login_message": login_message,
            "general_error": general_error,
            "num_applied_users": num_applied_users,
        },
    )
