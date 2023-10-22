from django import template
import typing as t
from datetime import datetime
from ..utils import repr_format

register = template.Library()


@register.filter
def date_string(value: datetime):
    return repr_format(value)


@register.simple_tag
def call(obj, method_name: str, *args):
    method: t.Callable[..., t.Any] = getattr(obj, method_name)
    return method(*args)
