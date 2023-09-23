from functools import wraps
from django.http import HttpRequest, JsonResponse
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.db.utils import IntegrityError
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from .models import LabTopic, LabEvent, CustomUser
import json

from django.utils import timezone


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
    if request.user.is_anonymous:
        return unauthenticated()

    events = (
        LabEvent.objects.filter(lab_datetime__gt=timezone.now())
        .annotate(num_topics=Count("topics"))
        .filter(num_topics__gte=1)
        .order_by("lab_datetime")
        .all()
    )

    return JsonResponse([event.json() for event in events], status=200, safe=False)


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

    if (link := event.links.filter(user=user).first()) is None:
        return JsonResponse(
            {"message": f"User `{user_id}` is not applied for event `{user_id}`"},
            status=400,
        )

    link.user = None
    link.save()

    return JsonResponse({}, status=204)
