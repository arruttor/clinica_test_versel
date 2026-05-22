from django import template

register = template.Library()


@register.filter
def keyvalue(dictionary, key):
    """Acessa um dicionário por chave dinâmica no template: dict|keyvalue:key"""
    if isinstance(dictionary, dict):
        return dictionary.get(key, [])
    return []
