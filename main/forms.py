from django.core.exceptions import ValidationError
from django import forms
from typing import Any
from django.utils.translation import gettext_lazy as _

import re


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
            self.add_error("password", ValidationError("Hesla se neshoduji"))

        return cleaned_data

    def to_model(self) -> dict[str, str]:
        return {k: v for k, v in self.cleaned_data.items() if k != "password_confirm"}
