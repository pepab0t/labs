from django.core.exceptions import ValidationError
from django import forms
from typing import Any, Callable
from django.utils.translation import gettext_lazy as _

# from django.core.validators import MinValueValidator, MaxValueValidator, EmailValidator
from datetime import datetime
from django.utils import timezone

import re


def minimum_after_n_days(days: int):
    def validator(value: datetime):
        if timezone.now() + timezone.timedelta(days=days) > value:
            if days == 1:
                raise ValidationError(f"Datum musí být nejméně {days} den od teď")
            elif days in {2, 3, 4}:
                raise ValidationError(f"Datum musí být nejméně {days} dny od teď")
            else:
                raise ValidationError(f"Datum musí být nejméně {days} dní od teď")

    return validator


def cvut_email(value: str):
    if re.search(f"^.+@fs.cvut.cz$", value) is None:
        raise ValidationError("Netolerovaná doména", code="invalid")


def create_datetime_widget(dt_factory: Callable[[], datetime]):
    return forms.DateTimeInput(
        attrs={
            "type": "datetime-local",
            "class": "form-control",
            "value": dt_factory().strftime("%Y-%m-%dT09:00"),
        },
        format="%Y-%m-%d %H:%M",
    )


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
        input_formats=["%Y-%m-%d %H:%M"],
        widget=create_datetime_widget(
            lambda: timezone.now() + timezone.timedelta(days=7)
        ),
    )
    close_login = forms.DateTimeField(
        required=True,
        label="Uzávěr přihlášení",
        input_formats=["%Y-%m-%d %H:%M"],
        widget=create_datetime_widget(
            lambda: timezone.now() + timezone.timedelta(days=5)
        ),
    )
    close_logout = forms.DateTimeField(
        required=True,
        label="Uzávěr odhlášení",
        input_formats=["%Y-%m-%d %H:%M"],
        widget=create_datetime_widget(
            lambda: timezone.now() + timezone.timedelta(days=6)
        ),
    )

    def __init__(self, topics, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["topics"] = forms.MultipleChoiceField(
            choices=topics,
            widget=forms.CheckboxSelectMultiple,
            label="Vyberte témata:",
            initial=[c[0] for c in topics],
            required=True,
        )

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean()

        if any(
            [
                key not in cleaned
                for key in (
                    "lab_datetime",
                    "close_logout",
                    "close_login",
                    "topics",
                    "capacity",
                )
            ]
        ):
            return cleaned

        if cleaned["close_logout"] >= cleaned["lab_datetime"]:
            self.add_error(
                "close_logout",
                ValidationError(message="Uzávěr odhlášení musí být dříve než událost"),
            )
            return cleaned

        # if cleaned["close_logout"] <= cleaned["close_login"]:
        #     self.add_error(
        #         "close_login",
        #         ValidationError(
        #             message="Uzávěr přihlášení musí být dříve než uzávěr odhlášení"
        #         ),
        #     )
        #     return cleaned

        if len(cleaned["topics"]) < cleaned["capacity"]:
            self.add_error(
                "capacity",
                ValidationError(
                    message="Kapacita nemůže být vyšší než počet dostupných témat"
                ),
            )
            return cleaned

        return cleaned


class ApplyEventForm(forms.Form):
    def __init__(self, choices=list(), *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["topics"] = forms.ChoiceField(
            widget=forms.RadioSelect, choices=choices, label="Témata", required=True
        )

    @property
    def choices(self):
        return self.fields["topics"].choices
