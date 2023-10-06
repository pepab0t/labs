from functools import wraps
from django.http import HttpRequest, JsonResponse, HttpResponse
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, EmptyPage
from django.shortcuts import get_object_or_404
from django.db.utils import IntegrityError
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from .models import LabTopic, LabEvent, CustomUser, LinkTopicEvent
import json

from django.utils import timezone
from datetime import timedelta

EVENTS_PER_PAGE: int = 3
REQUESTS_PER_PAGE: int = 3


def unauthorized():
    return JsonResponse({"message": "unauthorized"}, status=403)


def unauthenticated():
    return JsonResponse({"message": "unauthenticated"}, status=401)


def staff_or_403(fn):
    @wraps(fn)
    def wrapper(request: HttpRequest, *args, **kwargs):
        if not request.user.is_staff:  # type: ignore
            return unauthorized()
        return fn(request, *args, **kwargs)

    return wrapper


def handle_validation(fn):
    @wraps(fn)
    def wrapper(request: HttpRequest, *args, **kwargs):
        try:
            return fn(request, *args, **kwargs)
        except ValidationError as e:
            return JsonResponse(
                {"message": ", ".join(e.messages), "error": "validation"}, status=422
            )

    return wrapper


@staff_or_403
@handle_validation
def new_topic(request: HttpRequest):
    if request.method != "POST":
        return unauthorized()

    topic: str | None = json.loads(request.body.decode("utf-8")).get("topic")
    if topic is None:
        return JsonResponse({"message": "missing parameter `topic`"}, status=422)

    lab_topic = LabTopic(title=topic, created_by=request.user)
    lab_topic.full_clean()
    try:
        lab_topic.save()
    except:
        return JsonResponse({"message": "topic already exist"}, status=422)

    lab_topic.refresh_from_db()
    return JsonResponse(lab_topic.json(), status=201)


def all_topics(request: HttpRequest):
    if request.method != "GET":
        return unauthorized()

    topics = LabTopic.objects.all()
    return JsonResponse([t.json() for t in topics], status=200, safe=False)


@staff_or_403
def remove_topic(request: HttpRequest):
    if request.method != "DELETE":
        return unauthorized()

    id: int | None = json.loads(request.body.decode("utf-8")).get("id")
    if id is None:
        return JsonResponse({"message": "missing parameter `topic`"}, status=422)

    try:
        LabTopic.objects.get(pk=id).delete()
    except LabTopic.DoesNotExist:
        return JsonResponse({"message": f"topic {id} does not exist"}, status=400)

    return JsonResponse({}, status=204)


@staff_or_403
def modify_topic(request: HttpRequest):
    if request.method != "PUT":
        return unauthorized()

    body = json.loads(request.body.decode("utf-8"))

    if (id := body.get("id")) is None or (new_title := body.get("topic")) is None:
        return JsonResponse(
            {"message": "payload expected to have `id` and `topic`"}, status=400
        )

    lab_topic = get_object_or_404(LabTopic, pk=id)

    lab_topic.title = new_title
    lab_topic.full_clean()
    try:
        lab_topic.save()
    except IntegrityError:
        return JsonResponse(
            {"message": f"Topic `{new_title}` already exists"}, status=422
        )

    lab_topic.refresh_from_db()
    return JsonResponse(lab_topic.json(), status=200)


def get_lab_events(request: HttpRequest):
    """page param starting from 1"""
    if request.user.is_anonymous:
        return unauthenticated()

    page = request.GET.get("page")
    if page is None or not page.isdigit():
        return JsonResponse({"message": "missing parameter `page` (int)"}, status=400)
    page_int: int = int(page)
    if page_int < 0:
        return JsonResponse({"message": "page must be greater or equal 1"}, status=400)

    events = (
        LabEvent.objects.filter(lab_datetime__gt=timezone.now())
        .filter(lab_datetime__gte=timezone.now())
        .annotate(num_topics=Count("topics"))
        .filter(num_topics__gte=1)
        .order_by("lab_datetime")
        .all()  # [EVENTS_PER_PAGE * (page_int - 1) : EVENTS_PER_PAGE * page_int]
    )

    paginator = Paginator(events, EVENTS_PER_PAGE)
    try:
        page = paginator.page(page_int)
    except EmptyPage:
        return JsonResponse({"message": "no more pages"})

    return JsonResponse(
        {"content": [event.json(request.user) for event in page], "has_next": page.has_next()}, status=200, safe=False  # type: ignore
    )


@staff_or_403
def approve_user(request: HttpRequest, id: int):
    user = CustomUser.objects.get(pk=id)

    if not user.approved and not user.cancelled:
        user.approved = True
        user.save()
        return JsonResponse({"message": f"{user.email} approved"}, status=200)

    return JsonResponse({"message": f"nothing to approve"}, status=200)


@staff_or_403
def decline_user(request: HttpRequest, id: int):
    user = CustomUser.objects.get(pk=id)

    if not user.cancelled:
        user.cancelled = True
        user.save()
        return JsonResponse({"message": f"{user.email} request cancelled"}, status=200)

    return JsonResponse({"message": f"nothing to cancel"}, status=200)


@staff_or_403
def remove_user_from_event(request: HttpRequest, event_id: int, user_id: int):
    try:
        user = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        return JsonResponse({"message": f"User `{user_id}` not found"}, status=404)

    try:
        event = LabEvent.objects.get(pk=event_id)
    except LabEvent.DoesNotExist:
        return JsonResponse({"message": f"Event `{user_id}` not found"}, status=404)

    if (link := event.links.filter(user=user).first()) is None:  # type: ignore
        return JsonResponse(
            {"message": f"User `{user_id}` is not applied for event `{user_id}`"},
            status=400,
        )

    link.user = None
    link.save()

    return JsonResponse({}, status=204)


@staff_or_403
def export_closed(request: HttpRequest):
    now = timezone.now()
    links = (
        LinkTopicEvent.objects.filter(event__lab_datetime__gte=now - timedelta(days=2))
        .filter(event__close_logout__lte=now)
        .all()
    )

    content: str = LinkTopicEvent.links_to_csv(links)

    response = HttpResponse(content, content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="closed_labs.csv"'

    return response


@staff_or_403
def export_history(request: HttpRequest):
    now = timezone.now()

    links = LinkTopicEvent.objects.filter(
        event__lab_datetime__lte=now, event__lab_datetime__gte=now - timedelta(weeks=30)
    ).all()

    content: str = LinkTopicEvent.links_to_csv(links)
    response = HttpResponse(content, content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="history_labs.csv"'

    return response


@staff_or_403
def get_reqister_requests(request: HttpRequest) -> HttpResponse:
    page: str | None = request.GET.get("page")

    if page is None:
        return JsonResponse({"message": "missing parameter `page` (int)"}, status=400)

    requests = (
        CustomUser.objects.filter(approved=False, cancelled=False)
        .order_by("date_joined")
        .all()
    )

    paginator = Paginator(requests, REQUESTS_PER_PAGE)

    try:
        p = paginator.page(page)
    except EmptyPage as e:
        return JsonResponse({"message": str(e)}, status=400)

    return JsonResponse(
        {
            "content": list(map(lambda u: u.json(), p.__iter__())),
            "has_next": p.has_next(),
        },
        safe=False,
    )
