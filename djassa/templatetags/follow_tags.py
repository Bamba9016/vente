from django import template
from djassa.models import Follow  # Remplacez par le chemin correct de votre modèle Follow

register = template.Library()

@register.filter
def is_following(user, followed_user):
    """
    Vérifie si `user` suit `followed_user`.
    """
    return Follow.objects.filter(follower=user, following=followed_user).exists()
