from functools import wraps
from django.http import HttpRequest, JsonResponse
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.db.utils import IntegrityError
from .models import LabTopic
import json


def unauthorized():
    return JsonResponse({"message": "unauthorized"}, status=403)


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
