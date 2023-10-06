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
from .models import CustomUser, LabTopic, LabEvent, LinkTopicEvent, MAX_USER_APPLIES
from .utils import render_error, render_event_page

from django.contrib.admin.views.decorators import staff_member_required


def error(request: HttpRequest):
    return render_error(request, ["error one", "error two"])


@staff_member_required(redirect_field_name="home")
def create_users(request: HttpRequest):
    for i in range(1, 15):
        CustomUser.objects.create_user(  # type: ignore
            email=f"foo{i}@fs.cvut.cz",
            fullname="Foo Baz",
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


def apply_event(request: HttpRequest, event: LabEvent, form: ApplyEventForm):
    if event.close_login < timezone.now():
        return render_event_page(
            request, event, form, login_message="Čas na přihlášení vypršel"
        )

    if event.capacity <= (num_applied_users := event.get_number_applied_users()):
        return render_event_page(
            request, event, form, num_applied_users=num_applied_users
        )

    if not request.user.can_apply():  # type: ignore
        return render_event_page(
            request,
            event,
            form,
            num_applied_users=num_applied_users,
            general_error=f"Maximální počet přihlášených cvičení je: {MAX_USER_APPLIES}",
        )

    if form.is_valid():
        topic_id = int(form.cleaned_data["topics"])
        topic = LabTopic.objects.get(pk=topic_id)

        link = LinkTopicEvent.objects.filter(event=event, topic=topic).first()

        if link.user is None:  # type: ignore
            link.user = request.user  # type: ignore
            link.save()  # type: ignore
            return redirect("apply_event", id=event.id)  # type: ignore

    return render_event_page(request, event, form, num_applied_users=num_applied_users)


def logout_event(request: HttpRequest, event: LabEvent, form: ApplyEventForm):
    if event.close_logout < timezone.now():
        return render_event_page(
            request, event, form, logout_message="Čas na odhlášení vypršel"
        )

    topic = event.get_user_topic(request.user)

    link = LinkTopicEvent.objects.filter(
        user=request.user, event=event, topic=topic
    ).first()

    if link is not None:
        link.user = None
        link.save()

    return redirect("apply_event", id=event.id)  # type: ignore


@login_required
def event_page(request: HttpRequest, id: int):
    try:
        event = LabEvent.objects.get(pk=id)
    except LabEvent.DoesNotExist:
        return render_error(request, ["Cvičení neexistuje!"])

    free_topics = event.get_free_topics_radios()

    if not free_topics:
        form = ApplyEventForm()
    else:
        form = ApplyEventForm(
            free_topics,  # type: ignore
            request.POST or None,
            initial={"topics": free_topics[0][0]},  # type: ignore
        )

    if request.method == "POST":
        if request.user.is_staff:  # type: ignore
            return render_event_page(request, event, form)

        operation = request.GET.get("operation")

        match operation:
            case "apply":
                return apply_event(request, event, form)
            case "logout":
                return logout_event(request, event, form)
            case _:
                raise Exception("unsupported value for `operation`")

    return render_event_page(request, event, form)


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


@staff_member_required(redirect_field_name="home")
def export_page(request: HttpRequest):
    return render(request, "export.html")


@staff_member_required(redirect_field_name="home")
def delete_event(request: HttpRequest, event_id: int):
    event = LabEvent.objects.get(pk=event_id)
    event.delete()

    return redirect("home")
