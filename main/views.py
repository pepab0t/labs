import re
from django.shortcuts import render, redirect
from django.http.response import HttpResponse
from django.http import HttpRequest, HttpResponseRedirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.db.utils import IntegrityError
from django.utils import timezone

from .forms import (
    LoginForm,
    RegisterForm,
    ValidationError,
    CreateEventForm,
    ApplyEventForm,
)
from .models import CustomUser, LabTopic, LabEvent, LinkTopicEvent

from django.contrib.admin.views.decorators import staff_member_required


def create_users(request: HttpRequest):
    for i in range(1, 15):
        CustomUser.objects.create_user(  # type: ignore
            email=f"foo{i}@fs.cvut.cz",
            fullname="Foo baz",
            password="1111",
            approved=False,
        )

    return HttpResponse("good")


def login_wrapper(request: HttpRequest, user):
    if user.approved:
        login(request, user)
        return redirect("home")

    if user.cancelled:
        return render(
            request,
            "not_approved.html",
            {"default_title": True, "message": "Vaše registrace byla zamítnuta!"},
        )

    return render(
        request,
        "not_approved.html",
        {
            "default_title": True,
            "message": "Vaše registrace ještě nebyla potvrzena správcem.",
        },
    )


@login_required
def home(request: HttpRequest):
    return render(request, "home.html")


def login_user(request: HttpRequest):
    if request.method == "GET":
        return render(
            request,
            "login.html",
            {
                "form": LoginForm(),
                "title": "Přihlášení",
                "login_only": True,
                "default_title": True,
            },
        )

    form = LoginForm(request.POST)
    if not form.is_valid():
        return render(
            request,
            "login.html",
            {
                "form": form,
                "title": "Přihlášení",
                "login_only": True,
                "default_title": True,
            },
        )

    if (
        user := authenticate(
            request,
            username=form.cleaned_data["email"],
            password=form.cleaned_data["password"],
        )
    ) is None:
        form.add_error(
            "email", ValidationError("Nesprávný email nebo heslo", code="invalid")
        )
        return render(
            request,
            "login.html",
            {
                "form": form,
                "title": "Přihlášení",
                "login_only": True,
                "default_title": True,
            },
        )

    return login_wrapper(request, user)


def register_user(request: HttpRequest):
    if request.method == "GET":
        return render(
            request,
            "login.html",
            {
                "form": RegisterForm(),
                "title": "Registrace",
                "login_only": False,
                "default_title": True,
            },
        )

    form = RegisterForm(request.POST)
    if not form.is_valid():
        return render(
            request,
            "login.html",
            {
                "form": form,
                "title": "Registrace",
                "login_only": False,
                "default_title": True,
            },
        )

    try:
        user = CustomUser.objects.create_user(**form.to_model(), approved=False)  # type: ignore
    except ValidationError as e:
        for field, errors in e.error_dict.items():
            for error in errors:
                form.add_error(field, error)
        return render(
            request,
            "login.html",
            {
                "form": form,
                "title": "Registrace",
                "login_only": False,
                "default_title": True,
            },
        )
    except IntegrityError as e:
        form.add_error(
            "email", ValidationError("Email je již zaregistrován", code="invalid")
        )
        return render(
            request,
            "login.html",
            {
                "form": form,
                "title": "Registrace",
                "login_only": False,
                "default_title": True,
            },
        )

    return login_wrapper(request, user)


def logout_user(request: HttpRequest):
    logout(request)
    return redirect("login")


@staff_member_required(redirect_field_name="home")
def show_topics(request: HttpRequest):
    return render(request, "topics.html")


@staff_member_required(redirect_field_name="home")
def create_event(request: HttpRequest):
    topics = [(topic.id, topic.title) for topic in LabTopic.objects.all()]  # type: ignore
    form = CreateEventForm(topics, initial={"capacity": 1})

    if request.method == "POST":
        form = CreateEventForm(topics, request.POST)
        if not form.is_valid():
            return render(request, "create_event.html", {"form": form})

        lab_event = LabEvent(
            capacity=form.cleaned_data["capacity"],
            close_login=form.cleaned_data["close_login"],
            close_logout=form.cleaned_data["close_logout"],
            lab_datetime=form.cleaned_data["lab_datetime"],
        )
        lab_event.created_by = request.user
        try:
            lab_event.save()
        except ValidationError as e:
            return render(request, "create_event.html", {"form": form})

        for topic_id in form.cleaned_data["topics"]:
            lab_topic = LabTopic.objects.get(pk=int(topic_id))
            lab_event.topics.add(lab_topic)

        return redirect("home")

    return render(request, "create_event.html", {"form": form})


@login_required
def apply_to_event(request: HttpRequest, id: int):
    event = LabEvent.objects.get(pk=id)
    free_topics = event.get_free_topics()

    if not free_topics:
        return render(
            request,
            "apply_event.html",
            {"event": event, "form": ApplyEventForm(), "free_topics": free_topics},
        )

    if request.method == "POST":
        form = ApplyEventForm(
            [(topic.id, topic.title) for topic in free_topics],  # type: ignore
            request.POST,
            initial={"topics": free_topics[0].id},  # type: ignore
        )

        if event.capacity <= event.get_number_applied_users():
            return render(
                request,
                "apply_event.html",
                {"event": event, "form": form, "free_topics": free_topics},
            )

        if form.is_valid():
            topic_id = int(form.cleaned_data["topics"])
            topic = LabTopic.objects.get(pk=topic_id)

            link = LinkTopicEvent.objects.filter(event=event, topic=topic).first()

            if link.user is None:
                link.user = request.user
                link.save()

                return redirect("apply_event", id=id)  # type: ignore

            return render(
                request,
                "apply_event.html",
                {"event": event, "form": form, "free_topics": free_topics},
            )

    else:
        form = ApplyEventForm(
            [(topic.id, topic.title) for topic in free_topics],  # type: ignore
            initial={"topics": free_topics[0].id},  # type: ignore
        )

    print(event.get_user_topic(request.user))

    return render(
        request,
        "apply_event.html",
        {"event": event, "form": form, "free_topics": free_topics},
    )


@login_required
def logout_event(request: HttpRequest, id: int):
    event = LabEvent.objects.get(pk=id)
    topic = event.get_user_topic(request.user)

    link = LinkTopicEvent.objects.filter(
        user=request.user, event=event, topic=topic
    ).first()

    if link is None:
        return redirect("apply_event", id=id)

    link.user = None
    link.save()

    return redirect("apply_event", id=id)


@login_required
def my_labs(request: HttpRequest):
    events = LabEvent.get_user_events(request.user)  # type: ignore
    return render(request, "my_labs.html", {"events": events})


@staff_member_required(redirect_field_name="home")
def approve_registration_page(request: HttpRequest):
    users = CustomUser.objects.filter(approved=False, cancelled=False).order_by(
        "date_joined"
    )[:10]
    return render(request, "approve_registration.html", {"users": users})
