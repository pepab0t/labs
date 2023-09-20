from django.core.exceptions import ValidationError
from django import forms
from typing import Any
from django.utils.translation import gettext_lazy as _

# from django.core.validators import MinValueValidator, MaxValueValidator, EmailValidator
from datetime import datetime, timedelta
from django.utils import timezone

import re


def minimum_after_n_days(days: int):
    def validator(value: datetime):
        if timezone.now() + timedelta(days=days) > value:
            raise ValidationError(f"Date must be at least after {days} days from now")

    return validator


def cvut_email(value: str):
    if re.search(f"^.+@fs.cvut.cz$", value) is None:
        raise ValidationError("Netolerovaná doména", code="invalid")


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email", validators=[cvut_email])
    password = forms.CharField(label="Heslo", widget=forms.PasswordInput())


class RegisterForm(LoginForm):
    fullname = forms.CharField(label="Jméno a příjmění", max_length=100, min_length=5)
    password_confirm = forms.CharField(
        label="Heslo znovu", widget=forms.PasswordInput()
    )

    field_order = ["fullname", "email", "password", "password_confirm"]

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()

        if not cleaned_data["password"] == cleaned_data["password_confirm"]:
            self.add_error("password", ValidationError("Hesla se neshodují"))

        return cleaned_data

    def to_model(self) -> dict[str, str]:
        return {k: v for k, v in self.cleaned_data.items() if k != "password_confirm"}


class CreateEventForm(forms.Form):
    capacity = forms.IntegerField(
        initial=1, required=True, label="Kapacita:", min_value=1, max_value=1_000
    )

    lab_datetime = forms.DateTimeField(
        required=True,
        validators=[minimum_after_n_days(5)],
        label="Datum a čas",
        input_formats=["%d.%m.%Y %H:%M"],
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-control"},
            format="%d.%m.%Y %H:%M",
        ),
    )
    close_login = forms.DateTimeField(
        required=True,
        label="Uzávěr přihlášení",
        input_formats=["%d.%m.%Y %H:%M"],
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-control"},
            format="%d.%m.%Y %H:%M",
        ),
    )
    close_logout = forms.DateTimeField(
        required=True,
        label="Uzávěr odhlášení",
        input_formats=["%d.%m.%Y %H:%M"],
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-utc", "class": "form-control"},
            format="%d.%m.%Y %H:%M",
        ),
    )

    def __init__(self, topics, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["topics"] = forms.MultipleChoiceField(
            choices=topics,
            widget=forms.CheckboxSelectMultiple,
            label="Vyberte možnosti:",
            initial=[c[0] for c in topics],
            required=True,
        )
