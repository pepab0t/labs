from django import template
import typing as t

register = template.Library()


@register.simple_tag
def call(obj, method_name: str, *args):
    method: t.Callable[..., t.Any] = getattr(obj, method_name)
    return method(*args)
