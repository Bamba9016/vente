import json
import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, update_session_auth_hash, logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from . import models
from .forms import InscriptionForm, LoginForm, UserProfileForm, PasswordUpdateForm, PublicationForm, DemandeForm, \
    MessageForm
from .models import Publication, Comment, Share, Like, Follow, CustomUser, Demande, Friend, Message, Notification

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


@csrf_exempt
def marquer_publications_vues(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        seen_ids = data.get('seen_ids', [])

        if not isinstance(seen_ids, list):
            return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)

        publications_vues = Publication.objects.filter(id__in=seen_ids)

        if request.user.is_authenticated:
            request.user.publications_vues.add(*publications_vues)

        return JsonResponse({'status': 'success', 'seen_ids': seen_ids})

    return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=405)

@login_required(login_url='/login/')
def accueil_view(request):
    user = request.user

    # Récupérer les ID des publications déjà vues
    publications_vues_ids = user.publications_vues.values_list('id', flat=True)

    # Exclure les publications vues et celles de l'utilisateur lui-même
    publications = Publication.objects.exclude(author=user).exclude(id__in=publications_vues_ids).order_by('created_at')

    follow_status = {}
    comments = {}

    for publication in publications:
        is_following = Follow.objects.filter(follower=user, following=publication.author).exists()
        follow_status[publication.id] = is_following
        comments[publication.id] = list(Comment.objects.filter(publication=publication))

    context = {
        'publications': publications,
        'follow_status': follow_status,
        'comments': comments,
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
def profile_view(request ):
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
    publications = Publication.objects.all().order_by('-created_at')[:10]  # Trier par date de création décroissante
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
def publication_detail(request, publication_id):
    publication = get_object_or_404(Publication, id=publication_id)
    return render(request, 'djassa/djassaman/publication_detail.html', {'publication': publication})
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
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'likes_count': publication.likes.count()
            })
        return redirect(request.POST.get('next', 'accueil'))


    # Redirection pour les requêtes classiques
    next_url = request.GET.get('next', 'accueil')
    return redirect(next_url)


@login_required
def comment_publication(request, publication_id):
    if request.method == 'POST':
        content = request.POST.get('comment')
        publication = Publication.objects.get(id=publication_id)

        comment = Comment.objects.create(
            user=request.user,
            publication=publication,
            content=content
        )

        return JsonResponse({
            'status': 'success',
            'comment': {
                'username': comment.user.username,
                'content': comment.content,
                'user_avatar': comment.user.profile_picture.url if comment.user.profile_picture else 'https://placehold.co/120x120',
                'user_profile_url': f'/profilepublication/{comment.user.id}/'
            }
        })
    return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'}, status=405)

def page_commentaire(request, publication_id):
    publication = get_object_or_404(Publication, id=publication_id)
    comments = Comment.objects.filter(publication=publication).select_related('user').prefetch_related('replies').order_by('-created_at')
    return render(request, 'djassa/djassaman/commentaire.html', {
        'publication': publication,
        'comments': comments
    })

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

    users_data = {}
    for msg in conversations:
        # L'autre utilisateur dans la conversation
        other = msg.recipient if msg.sender == request.user else msg.sender

        # On ignore l'utilisateur connecté
        if other != request.user:
            if other not in users_data:
                last_message = msg
                unread_count = Message.objects.filter(sender=other, recipient=request.user, is_read=False).count()
                users_data[other] = {
                    'user': other,
                    'last_message': last_message,
                    'unread_count': unread_count
                }

    # Récupérer les utilisateurs sans l'utilisateur connecté
    return render(request, 'djassa/djassaman/inbox.html', {'users': users_data.values()})

@login_required
def conversation(request, user_id):
    """Afficher une conversation entre deux utilisateurs"""
    recipient = get_object_or_404(CustomUser, id=user_id)

    # Récupérer les messages entre l'utilisateur connecté et le destinataire
    messages = Message.objects.filter(
        (Q(sender=request.user, recipient=recipient) |
         Q(sender=recipient, recipient=request.user))
    ).order_by('timestamp')

    # Marquer les messages comme lus
    messages.filter(recipient=request.user, is_read=False).update(is_read=True)

    # Si le formulaire est soumis (pour envoyer un message)
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





@login_required
def reply_to_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if request.method == "POST":
        reply_content = request.POST.get("reply")
        # Créer une réponse au commentaire
        Comment.objects.create(
            user=request.user,
            content=reply_content,
            parent_comment=comment,  # Lier la réponse au commentaire parent
            publication=comment.publication  # Si vous souhaitez lier la réponse à la même publication
        )
        return redirect('page_commentaire', publication_id=comment.publication.id)  # Ou redirigez vers la page appropriée

    return render(request, 'votre_template.html', {'comment': comment})

def recherche_ajax(request):
    query = request.GET.get('q', '')
    if query:
        publications = Publication.objects.filter(
            Q(nom_du_produit__icontains=query) |
            Q(content__icontains=query)
        )[:5]

        users = CustomUser.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )[:5]

        demandes = Demande.objects.filter(
            Q(nom_du_produit__icontains=query) |
            Q(description__icontains=query)
        )[:5]

        data = {
            'publications': [
                {'nom': p.nom_du_produit, 'id': p.id, 'type': 'publication'}
                for p in publications
            ],
            'users': [
                {'nom': u.username, 'id': u.id, 'type': 'user'}
                for u in users
            ],
            'demandes': [
                {'nom': d.nom_du_produit, 'id': d.id, 'type': 'demande'}
                for d in demandes
            ],
        }

        return JsonResponse(data)
    return JsonResponse({'publications': [], 'users': [], 'demandes': []})

def recherche_resultats(request):
    query = request.GET.get('q', '')
    publications = []
    users = []
    demandes = []

    if query:
        publications = Publication.objects.filter(
            Q(nom_du_produit__icontains=query) |
            Q(content__icontains=query)
        )

        users = CustomUser.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )

        demandes = Demande.objects.filter(
            Q(nom_du_produit__icontains=query) |
            Q(description__icontains=query)
        )

    return render(request, 'djassa/djassaman/recherche_resultats.html', {
        'query': query,
        'publications': publications,
        'users': users,
        'demandes': demandes,
    })



def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()  # Compter les notifications non lues
    return render(request, 'djassa/djassaman/notifications_list.html', {
        'notifications': notifications,
        'unread_count': unread_count
    })

