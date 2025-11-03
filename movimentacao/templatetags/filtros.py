from django import template
import re

register = template.Library()


@register.filter
def somente_numeros(value):
    return re.sub(r"\D", "", str(value))


@register.filter
def simNao(value):
    if value:
        return "Sim"
    else:
        return "Não"


@register.filter
def mostrar_classe(value):
    return value.__class__._meta.verbose_name.title()


@register.filter
def remover_char(texto, char):
    return str(texto).replace(char, "")


@register.filter
def to_str(texto):
    return str(texto)


@register.filter
def to_int(value):
    return int(value)


@register.filter
def to_str(value):
    return str(value)


@register.simple_tag(takes_context=True)
def param_replace(context, **kwargs):
    """
    Return encoded URL parameters that are the same as the current
    request's parameters, only with the specified GET parameters added or changed.

    It also removes any empty parameters to keep things neat,
    so you can remove a parm by setting it to ``""``.

    For example, if you're on the page ``/things/?with_frosting=true&page=5``,
    then

    <a href="/things/?{% param_replace page=3 %}">Page 3</a>

    would expand to

    <a href="/things/?with_frosting=true&page=3">Page 3</a>

    Based on
    https://stackoverflow.com/questions/22734695/next-and-before-links-for-a-django-paginated-query/22735278#22735278
    """
    d = context["request"].GET.copy()
    for k, v in kwargs.items():
        d[k] = v
    for k in [k for k, v in d.items() if not v]:
        del d[k]
    return d.urlencode()
