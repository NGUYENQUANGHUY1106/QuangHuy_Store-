from django import template


register = template.Library()


@register.filter
def vnd(value):
    return f'{int(value):,}'.replace(',', '.') + '₫'
