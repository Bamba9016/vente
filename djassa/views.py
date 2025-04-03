import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, update_session_auth_hash, logout
from django.contrib import messages
from django.views.decorators.http import require_POST

from . import models
from .forms import InscriptionForm, LoginForm, UserProfileForm, PasswordUpdateForm, PublicationForm, DemandeForm, \
    MessageForm
from .models import Publication, Comment, Share, Like, Follow, CustomUser, Demande, Friend, Message

logger = logging.getLogger(__name__)

def inscription_view(request):
    if request.method == 'POST':
        form = InscriptionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Inscription réussie ! Vous pouvez maintenant vous connecter.")
            return redirect('login')
    else:
        form = InscriptionForm()
    return render(request, 'djassa/inscription.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['mot_de_passe']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('accueil')
            else:
                messages.error(request, "Nom d’utilisateur ou mot de passe invalide.")
    else:
        form = LoginForm()
    return render(request, 'djassa/connexion.html', {'form': form})


@login_required(login_url='/login/')
def accueil_view(request):
    user = request.user
    if not user.profile_picture:
        user.profile_picture = 'https://cdn.jsdelivr.net/npm/twemoji@14.0.2/assets/72x72/1f464.png'  # Assure-toi que ce fichier existe dans ton dossier media

    publications = Publication.objects.exclude(author=user).order_by('created_at')
    follow_status = {}
    comments = {}

    for publication in publications:
        # Vérifier le statut de suivi
        is_following = Follow.objects.filter(follower=request.user, following=publication.author).exists()
        follow_status[publication.id] = is_following

        # Récupérer les commentaires pour chaque publication
        comments[publication.id] = list(Comment.objects.filter(publication=publication))

    context = {
        'publications': publications,
        'follow_status': follow_status,
        'comments': comments  # Inclure les commentaires dans le contexte
    }
    return render(request, 'djassa/djassaman/accuiel.html', context)

@login_required(login_url='/login/')
def modifier_profile_view(request):
    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if profile_form.is_valid():
            profile_form.save()
            return redirect('profile')
    else:
        profile_form = UserProfileForm(instance=request.user)

    return render(request, 'djassa/djassaman/modifier_profil.html', {'profile_form': profile_form})

@login_required(login_url='/login/')
def change_password(request):
    if request.method == 'POST':
        password_form = PasswordUpdateForm(user=request.user, data=request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)  # Important for keeping the user logged in after password change
            return redirect('profile')
    else:
        password_form = PasswordUpdateForm(user=request.user)

    return render(request, 'djassa/djassaman/change_password.html', {'password_form': password_form})

@login_required(login_url='/login/')
def profile_view(request):
    user = request.user
    user_publications = Publication.objects.filter(author=user).order_by('-created_at')
    return render(request, 'djassa/djassaman/profile.html', {
        'user': user,
        'user_publications': user_publications
    })

@login_required(login_url='/login/')
def profilepublication_view(request, user_id):

    viewuser = get_object_or_404(CustomUser, id=user_id)
    user_publications = Publication.objects.filter(author=viewuser).order_by('-created_at')
    # Vérifie si l'utilisateur connecté suit cet utilisateur
    is_following = Follow.objects.filter(follower=request.user, following=viewuser).exists()

    return render(request, 'djassa/djassaman/profilepublication.html', {
        'viewuser': viewuser,
        'user_publications': user_publications,
        'is_following': is_following,

    })
@login_required(login_url='/login/')
def logout_view(request):
    logout(request)
    return redirect('login')  # Redirige vers la page de connexion après déconnexion



@login_required(login_url='/login/')
def publication_view(request):
    if request.method == 'POST':
        form = PublicationForm(request.POST, request.FILES)

        if form.is_valid():
            publication = form.save(commit=False)
            publication.author = request.user
            publication.save()
            return redirect('accueil')  # Redirige vers la page d'accueil après publication
    else:
        form = PublicationForm()
    return render(request, 'djassa/djassaman/publication.html', {'form': form})

@login_required(login_url='/login/')
def publication_list(request):
    publications = Publication.objects.all().order_by('-created_at')  # Trier par date de création décroissante
    data = {
        'publications': [
            {
                'id': publication.id,
                'author': {
                    'first_name': publication.author.first_name,
                    'last_name': publication.author.last_name,
                    'profile_picture': publication.author.profile_picture.url if publication.author.profile_picture else None,
                },
                'content': publication.content,
                'created_at': publication.created_at.strftime('%d %b %Y, %H:%M'),
                'image': publication.image.url if publication.image else None,
                'video': publication.video.url if publication.video else None,
            }
            for publication in publications
        ]
    }
    return JsonResponse(data)
@login_required
def like_publication(request, publication_id):
    publication = get_object_or_404(Publication, id=publication_id)
    like_exists = Like.objects.filter(publication=publication, user=request.user).exists()

    if like_exists:
        Like.objects.filter(publication=publication, user=request.user).delete()
        liked = False
    else:
        Like.objects.create(publication=publication, user=request.user)
        liked = True

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Réponse JSON pour les requêtes AJAX
        return JsonResponse({
            'liked': liked,
            'likes_count': publication.like_set.count()
        })

    # Redirection pour les requêtes classiques
    next_url = request.GET.get('next', 'accueil')
    return redirect(next_url)


@login_required
def comment_publication(request, publication_id):
    if request.method == 'POST':
        publication = get_object_or_404(Publication, id=publication_id)
        content = request.POST.get('comment')
        if content.strip():  # Vérifie que le commentaire n'est pas vide
            Comment.objects.create(publication=publication, user=request.user, content=content)
            messages.success(request, 'Comment added!')
        else:
            messages.error(request, 'Comment cannot be empty.')

    # Récupérer le paramètre `next`
    next_url = request.GET.get('next','accueil' )  # Par défaut, redirige vers 'accueil'
    return redirect(next_url)

@login_required
def share_publication(request, publication_id):
    publication = get_object_or_404(Publication, id=publication_id)
    if not Share.objects.filter(publication=publication, user=request.user).exists():
        Share.objects.create(publication=publication, user=request.user)
        messages.success(request, 'Publication shared!')
    else:
        messages.info(request, 'You already shared this publication.')

    # Récupérer le paramètre `next`
    next_url = request.GET.get('next', 'accueil')  # Par défaut, redirige vers 'accueil'
    return redirect(next_url)


@login_required
def subscribe_view(request, user_id):
    user_to_follow = get_object_or_404(CustomUser, id=user_id)
    if user_to_follow != request.user:
        with transaction.atomic():
            if not Follow.objects.filter(follower=request.user, following=user_to_follow).exists():
                Follow.objects.create(follower=request.user, following=user_to_follow)
                messages.success(request, f"You are now following {user_to_follow.username}!")
            else:
                messages.info(request, f"You are already following {user_to_follow.username}.")

    # Récupérer le paramètre `next`
    next_url = request.GET.get('next', 'accueil')  # Par défaut, redirige vers 'accueil'
    return redirect(next_url)


@login_required
def unsubscribe_view(request, user_id):
    user_to_unfollow = get_object_or_404(CustomUser, id=user_id)

    try:
        follow_relation = Follow.objects.get(follower=request.user, following=user_to_unfollow)
        follow_relation.delete()
        logger.info(f"Unfollowed user {user_to_unfollow} successfully.")
    except Follow.DoesNotExist:
        logger.warning(f"No follow relationship found for user {user_to_unfollow}.")

    next_url = request.GET.get('next', 'accueil')  # Par défaut, redirige vers 'accueil'
    return redirect(next_url)





@login_required
def page_de_vente(request):
    return render(request, 'djassa/djassaman/djassa.html')

@login_required
def enregistrer_demande(request):
    if request.method == 'POST':
        form = DemandeForm(request.POST)
        if form.is_valid():
            demande = form.save(commit=False)
            demande.author = request.user
            demande.save()
            return redirect('page_de_vente')  # Redirige vers la liste des demandes
    else:
        form = DemandeForm()
    return render(request, 'djassa/djassaman/enregistrer_demande.html', {'form': form})


@login_required
def choisir_categorie(request):
    categories = [cat[0] for cat in Publication.CATEGORIES_CHOICES]  # Liste des catégories
    return render(request, 'djassa/djassaman/choisir_categorie.html', {'categories': categories})

@login_required
def voir_demandes(request, categorie):
    demandes = Demande.objects.filter(categorie=categorie)
    return render(request, 'djassa/djassaman/voir_demande.html',  {'demandes': demandes, 'categorie': categorie})

@login_required(login_url='/login/')
def abonnements_view(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    abonnements = Follow.objects.filter(follower=user).select_related('following')
    return render(request, 'djassa/djassaman/abonnements.html', {'abonnements': abonnements, 'profile_user': user})

@login_required(login_url='/login/')
def abonnes_view(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    abonnes = Follow.objects.filter(following=user).select_related('follower')
    amis = []  # Liste pour stocker les amis

    for abonne in abonnes:
        # Vérifie si l'abonné suit également l'utilisateur
        if Follow.objects.filter(follower=abonne.follower, following=user).exists():
            amis.append(abonne)
    return render(request, 'djassa/djassaman/abonnes.html', {'abonnes': abonnes, 'amis': amis, 'profile_user': user})

@login_required(login_url='/login/')
def amis_view(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    amis = Friend.objects.filter(user=user).select_related('friend')
    return render(request, 'djassa/djassaman/amis.html', {'amis': amis, 'profile_user': user})


@login_required(login_url='/login/')
def viewabonnements_view(request, viewuser_id):
    viewuser = get_object_or_404(CustomUser, id=viewuser_id)
    abonnements = Follow.objects.filter(follower=viewuser).select_related('following')
    publications = Publication.objects.select_related('author')  # Chargez les auteurs avec les publications

    return render(request, 'djassa/djassaman/viewabonnements.html', {'abonnements': abonnements, 'profile_user': viewuser,'publications': publications,
})

@login_required(login_url='/login/')
def viewabonnes_view(request, viewuser_id):
    viewuser = get_object_or_404(CustomUser, id=viewuser_id)
    abonnes = Follow.objects.filter(following=viewuser).select_related('follower')
    amis = []  # Liste pour stocker les amis

    for abonne in abonnes:
        # Vérifie si l'abonné suit également l'utilisateur
        if Follow.objects.filter(follower=abonne.follower, following=viewuser).exists():
            amis.append(abonne)
    return render(request, 'djassa/djassaman/viewabonnes.html', {'abonnes': abonnes, 'amis': amis, 'profile_user': viewuser})

@login_required(login_url='/login/')
def viewamis_view(request, viewuser_id):
    viewuser = get_object_or_404(CustomUser, id=viewuser_id)
    amis = Friend.objects.filter(user=viewuser).select_related('friend')
    return render(request, 'djassa/djassaman/viewamis.html', {'amis': amis, 'profile_user': viewuser})


@login_required
def inbox(request):
    """Afficher la liste des conversations de l'utilisateur"""

    conversations = Message.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).order_by('-timestamp')

    users = set()
    for msg in conversations:
        users.add(msg.sender)
        users.add(msg.recipient)
    users.discard(request.user)  # Ne pas afficher soi-même

    return render(request, 'djassa/djassaman/inbox.html', {'users': users})


@login_required
def conversation(request, user_id):
    """Afficher une conversation entre deux utilisateurs"""
    recipient = get_object_or_404(CustomUser, id=user_id)

    messages = Message.objects.filter(
        (Q(sender=request.user, recipient=recipient) |
         Q(sender=recipient, recipient=request.user))
    ).order_by('timestamp')

    # Marquer les messages comme lus
    messages.filter(recipient=request.user, is_read=False).update(is_read=True)

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.recipient = recipient
            message.save()
            return redirect('conversation', user_id=recipient.id)
    else:
        form = MessageForm()

    return render(request, 'djassa/djassaman/conversation.html', {'recipient': recipient, 'messages': messages, 'form': form})

@login_required(login_url='/login/')
def parametres_view(request):
    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        password_form = PasswordUpdateForm(user=request.user, data=request.POST)

        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Profil mis à jour avec succès.")
            return redirect('parametres')

        if password_form.is_valid():
            user = password_form.save()
            messages.success(request, "Mot de passe changé avec succès.")
            return redirect('parametres')

    else:
        profile_form = UserProfileForm(instance=request.user)
        password_form = PasswordUpdateForm(user=request.user)



    return render(request, 'djassa/djassaman/parametre.html', {
        'profile_form': profile_form,
        'password_form': password_form
    })

