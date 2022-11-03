from django import template

register = template.Library()

@register.filter
def access_dict(dict, key):
    """Access given dict with given key, then returns value"""
    return dict[key]