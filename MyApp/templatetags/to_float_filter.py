from django import template

register = template.Library()


@register.filter
def to_float(value):
    value = str(value)
    return value.replace('.', ',')
