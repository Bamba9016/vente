# your_app/templatetags/custom_filters.py

from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Renvoie la valeur pour une clé dans un dictionnaire"""
    if dictionary is not None:
        return dictionary.get(key)
    return None
