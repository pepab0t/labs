import re
from django.shortcuts import render, redirect
from django.http.response import HttpResponse
from django.http import HttpRequest, HttpResponseRedirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.db.utils import IntegrityError

from .forms import LoginForm, RegisterForm, ValidationError
from .models import CustomUser

from django.contrib.admin.views.decorators import staff_member_required


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

    login(request, user)
    return redirect("home")


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
        user = CustomUser.objects.create_user(**form.to_model())  # type: ignore
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

    login(request, user)
    return redirect("home")


def logout_user(request: HttpRequest):
    logout(request)
    return redirect("login")


@staff_member_required(redirect_field_name="home")
def show_topics(request: HttpRequest):
    return render(request, "topics.html")
