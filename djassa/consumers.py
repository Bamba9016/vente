import json

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.urls import resolve, Resolver404

from .models import Like, Publication, Comment
from .models import Message

class LikeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # On récupère l'id de la publication à partir de l'URL
        self.publication_id = self.scope['url_route']['kwargs']['publication_id']
        self.room_group_name = f'like_{self.publication_id}'

        # Joindre le groupe
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Accepter la connexion WebSocket
        await self.accept()

    async def disconnect(self, close_code):
        # Quitter le groupe lorsque la connexion est fermée
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Recevoir les données du WebSocket (dans ce cas, les infos du like)
        data = json.loads(text_data)
        publication = Publication.objects.get(id=self.publication_id)

        # Mettre à jour le nombre de likes (simuler l'ajout de like ici)
        like_exists = Like.objects.filter(publication=publication, user_id=data['user_id']).exists()

        if like_exists:
            Like.objects.filter(publication=publication, user_id=data['user_id']).delete()
            liked = False
        else:
            Like.objects.create(publication=publication, user_id=data['user_id'])
            liked = True

        # Envoyer l'update de likes à tous les clients connectés au même groupe
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'like_update',  # Le type d'événement que nous envoyons
                'liked': liked,
                'likes_count': publication.likes.count()
            }
        )

    # Gérer l'événement pour envoyer le message au WebSocket
    async def like_update(self, event):
        liked = event['liked']
        likes_count = event['likes_count']

        # Envoyer le message au WebSocket
        await self.send(text_data=json.dumps({
            'liked': liked,
            'likes_count': likes_count
        }))


User = get_user_model()

class PrivateChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        # L'utilisateur qui se connecte
        self.user = self.scope['user']
        # L'ID de l'autre utilisateur (destinataire) depuis l'URL
        self.other_user_id = self.scope['url_route']['kwargs']['user_id']

        if not self.user.is_authenticated:
            # Refuser la connexion si l'utilisateur n'est pas authentifié
            await self.close()
            return

        # Vérifier si l'autre utilisateur existe (optionnel mais recommandé)
        self.other_user = await self.get_user_instance(self.other_user_id)
        if not self.other_user:
            print(f"Utilisateur {self.other_user_id} non trouvé.")
            await self.close()
            return

        # Créer un nom de groupe unique et cohérent pour la paire d'utilisateurs
        # En triant les IDs, on s'assure que le nom est le même quel que soit celui qui initie
        user_ids = sorted([self.user.id, self.other_user.id])
        self.room_group_name = f'chat_{user_ids[0]}_{user_ids[1]}'
        print(f"Utilisateur {self.user.username} rejoint le groupe: {self.room_group_name}")

        # Rejoindre le groupe de la conversation
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Accepter la connexion WebSocket
        await self.accept()
        print(f"WebSocket connecté pour {self.user.username} avec {self.other_user.username}")

        # Optionnel: Marquer les messages comme lus lors de la connexion
        # await self.mark_messages_as_read()


    async def disconnect(self, close_code):
        print(f"WebSocket déconnecté pour {self.user.username}, groupe: {self.room_group_name}, code: {close_code}")
        # Quitter le groupe de la conversation
        if hasattr(self, 'room_group_name'): # Vérifier si room_group_name a été défini
             await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data=None, bytes_data=None):
        print(f"Message reçu de {self.user.username}: {text_data}")
        try:
            text_data_json = json.loads(text_data)
            message_content = text_data_json['message']

            if not message_content: # Ignorer les messages vides
                return

        except (json.JSONDecodeError, KeyError):
            print("Erreur: Format de message invalide reçu.")
            # Peut-être envoyer un message d'erreur au client
            await self.send(text_data=json.dumps({'error': 'Format de message invalide.'}))
            return

        # Sauvegarder le message dans la base de données
        new_message = await self.save_message(
            sender=self.user,
            recipient=self.other_user,
            content=message_content
        )

        if not new_message:
             print("Erreur lors de la sauvegarde du message.")
             await self.send(text_data=json.dumps({'error': 'Impossible de sauvegarder le message.'}))
             return

        # Préparer les données à diffuser
        message_data = {
            'type': 'chat.message', # Nom de la méthode handler
            'message_id': new_message.id,
            'sender_id': new_message.sender.id,
            'sender_username': new_message.sender.username,
            'recipient_id': new_message.recipient.id,
            'recipient_username': new_message.recipient.username,
            'content': new_message.content,
            'timestamp': new_message.timestamp.isoformat(), # Format ISO pour JS
        }

        # Diffuser le message au groupe de la conversation
        print(f"Diffusion du message au groupe {self.room_group_name}: {message_data}")
        await self.channel_layer.group_send(
            self.room_group_name,
            message_data
        )

    # --- Méthode appelée par group_send ---
    async def chat_message(self, event):
        # Cette méthode est appelée sur chaque consommateur du groupe
        # quand un message est reçu via group_send.
        print(f"Envoi du message {event['message_id']} au client {self.user.username} via WebSocket")

        # Envoyer le message au client WebSocket individuel
        await self.send(text_data=json.dumps({
            'message_id': event['message_id'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'content': event['content'],
            'timestamp': event['timestamp'],
            # On pourrait ajouter d'autres infos si nécessaire
        }))

    # --- Fonctions d'aide pour interagir avec la DB ---
    @database_sync_to_async
    def get_user_instance(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def save_message(self, sender, recipient, content):
        try:
            return Message.objects.create(
                sender=sender,
                recipient=recipient,
                content=content
                # timestamp est géré par default=timezone.now
            )
        except Exception as e:
            print(f"Erreur DB lors de la sauvegarde: {e}")
            return None

    # @database_sync_to_async
    # def mark_messages_as_read(self):
    #     # Marquer les messages reçus par self.user de self.other_user comme lus
    #     Message.objects.filter(
    #         sender=self.other_user,
    #         recipient=self.user,
    #         is_read=False
    #     ).update(is_read=True)
    #     # Vous pourriez vouloir notifier l'autre utilisateur que les messages ont été lus
    #     # via un autre type de message WebSocket.



class CommentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.publication_id = self.scope['url_route']['kwargs']['publication_id']
        self.room_group_name = f"publication_{self.publication_id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')

        if message_type == 'new_comment':
            comment_content = text_data_json.get('content')
            user_id = self.scope['user'].id

            if user_id and comment_content:
                user = await sync_to_async(User.objects.get)(id=user_id)
                publication = await sync_to_async(Publication.objects.get)(id=self.publication_id)
                comment = await sync_to_async(Comment.objects.create)(
                    user=user,
                    publication=publication,
                    content=comment_content
                )
                comment_data = await self.serialize_comment(comment)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'comment_message',
                        'comment': comment_data
                    }
                )

        elif message_type == 'new_reply':
            reply_content = text_data_json.get('content')
            user_id = self.scope['user'].id
            parent_comment_id = text_data_json.get('parent_id')

            if user_id and reply_content and parent_comment_id:
                user = await sync_to_async(User.objects.get)(id=user_id)
                parent_comment = await sync_to_async(Comment.objects.get)(id=parent_comment_id)
                reply = await sync_to_async(Comment.objects.create)(
                    user=user,
                    publication=parent_comment.publication,
                    content=reply_content,
                    parent_comment=parent_comment
                )
                reply_data = await self.serialize_comment(reply)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'comment_message',
                        'comment': reply_data
                    }
                )

    async def comment_message(self, event):
        comment = event['comment']
        await self.send(text_data=json.dumps({
            'type': 'comment',
            'comment': comment
        }))

    async def serialize_comment(self, comment):
        user = await sync_to_async(lambda u: {
            'id': u.id,
            'username': u.username,
            'profile_picture': u.profile_picture.url if u.profile_picture else 'https://placehold.co/120x120',
            'profile_url': f'/profilepublication/{u.id}/'
        })(comment.user)
        return {
            'id': comment.id,
            'user': user,
            'content': comment.content,
            'created_at': str(comment.created_at),
            'parent_comment': comment.parent_comment.id if comment.parent_comment else None,
            'replies': [] # Replies will be fetched separately on client-side or handled by separate events
        }


class NavigationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def receive(self, text_data):
        import json
        data = json.loads(text_data)
        if data['type'] == 'get_content':
            path = data['url']
            request = HttpRequest()
            request.method = 'GET'
            request.path = path
            request.user = self.scope['user']

            match = resolve(path)
            view_func = match.func
            view_kwargs = match.kwargs

            response = await sync_to_async(view_func)(request, **view_kwargs)

            # suppose que response est un HttpResponse avec du HTML
            html = response.content.decode()
            title = "Mon site"  # ou extraire du HTML

            await self.send(text_data=json.dumps({
                'type': 'content',
                'html': html,
                'title': title
            }))