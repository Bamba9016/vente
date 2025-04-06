from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, User
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('L\'adresse e-mail doit être définie')
        user = self.model(username=username, email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)

class CustomUser(AbstractBaseUser):
    username = models.CharField(max_length=50, unique=True)  # Réduit la longueur
    email = models.EmailField(max_length=50, unique=True)  # Réduit la longueur
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=[('H', 'Homme'), ('F', 'Femme'), ('A', 'Autre')], blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    account_created_at = models.DateTimeField(default=timezone.now)

    # Champs supplémentaires pour les fonctionnalités inspirées de TikTok
    followers_count = models.PositiveIntegerField(default=0)  # Nombre d'abonnés
    following_count = models.PositiveIntegerField(default=0)  # Nombre de personnes suivies
    friends_count = models.PositiveIntegerField(default=0)  # Nombre d'amis
    bio = models.TextField(max_length=500, blank=True)  # Biographie de l'utilisateur
    website = models.URLField(max_length=200, blank=True)  # URL du site web de l'utilisateur

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']



    @property
    def following_count(self):
        return Follow.objects.filter(follower=self).count()

    @property
    def followers_count(self):
        return Follow.objects.filter(following=self).count()

    @property
    def friends_count(self):
        friends = CustomUser.objects.filter(
            follows__follower=self,
            followers__following=self
        )
        return friends.count()


def __str__(self):
        return self.username


def get_followers(self):
    return self.followers.all()

def get_friends(self):
    return self.friends_with.all()





class Friend(models.Model):
    user = models.ForeignKey(CustomUser, related_name='friends_with', on_delete=models.CASCADE)  # Utilisateur
    friend = models.ForeignKey(CustomUser, related_name='friends', on_delete=models.CASCADE, )  # Ami
    created_at = models.DateTimeField(auto_now_add=True)  # Date d'ajout d'ami

    class Meta:
        unique_together = ('user', 'friend')  # Assurer l'unicité de la relation

    def __str__(self):
        return f"{self.user} est ami avec {self.friend}"

class Publication(models.Model):
    CATEGORIES_CHOICES = [
        ('Mode', 'Mode et Accessoires'),
        ('Electronique', 'Électronique et Informatique'),
        ('Maison', 'Maison et Jardin'),
        # Ajoutez toutes les autres catégories ici...
    ]

    FONCTION_CHOICES = [
        ('quasie_neuf', 'Quasi Neuf'),
        ('deuxieme_main', 'Deuxième Main'),
        ('nouveau', 'Nouveau'),
    ]

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    fichier = models.FileField(upload_to='publications/', blank=True,null=True)  # Un seul champ pour l'image ou la vidéo
    categorie = models.CharField(max_length=50, choices=CATEGORIES_CHOICES, default='Mode')
    nom_du_produit = models.CharField(max_length=100, blank=True, null=True)
    fonction = models.CharField(max_length=20, choices=FONCTION_CHOICES, default='nouveau')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.nom_du_produit} - {self.content[:50]}"

    def is_image(self):
        return self.fichier.name.endswith(('.png', '.jpg', '.jpeg', '.gif'))

    def is_video(self):
        return self.fichier.name.endswith(('.mp4', '.mov', '.avi'))

class Like(models.Model):
    publication = models.ForeignKey(Publication, related_name='likes', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='likes', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('publication', 'user')

    def __str__(self):
        return f"{self.user} aime {self.publication}"

class Comment(models.Model):
    publication = models.ForeignKey(Publication, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='comments', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent_comment = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')


    def __str__(self):
        return f"Commentaire de {self.user} sur {self.publication}"

class Share(models.Model):
    publication = models.ForeignKey(Publication, related_name='shares', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='shares', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('publication', 'user')

    def __str__(self):
        return f"{self.user} a partagé {self.publication}"

class Follow(models.Model):
    follower = models.ForeignKey(CustomUser, related_name='follows', on_delete=models.CASCADE)
    following = models.ForeignKey(CustomUser, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f"{self.follower} suit {self.following}"

class Demande(models.Model):
    CATEGORIES_CHOICES = [
        ('Mode', 'Mode et Accessoires'),
        ('Electronique', 'Électronique et Informatique'),
        ('Maison', 'Maison et Jardin'),
        # Ajoutez d'autres catégories ici...
    ]

    ETAT_PRODUIT_CHOICES = [
        ('dans_carton', 'Dans Carton'),
        ('quasi_neuf', 'Quasi Neuf'),
        ('deuxieme_main', 'Deuxième Main'),
    ]

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    description = models.TextField()
    categorie = models.CharField(max_length=50, choices=CATEGORIES_CHOICES,blank=True, null=True
)
    nom_du_produit = models.CharField(max_length=100)
    prix_achat = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    etat_du_produit = models.CharField(max_length=20, choices=ETAT_PRODUIT_CHOICES, blank=True, null=True)
    numero_telephone = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Produit: {self.nom_du_produit} - Catégorie: {self.categorie} - Téléphone: {self.numero_telephone}"


class Message(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='sent_messages',
        on_delete=models.CASCADE
    )  # L'utilisateur qui envoie le message
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='received_messages',
        on_delete=models.CASCADE
    )  # L'utilisateur qui reçoit le message
    content = models.TextField()  # Contenu du message
    timestamp = models.DateTimeField(default=timezone.now)  # Date et heure de l'envoi
    is_read = models.BooleanField(default=False)  # Statut du message (lu/non lu)

    class Meta:
        ordering = ['-timestamp']  # Trier les messages du plus récent au plus ancien

    def __str__(self):
        return f"Message de {self.sender} à {self.recipient} : {self.content[:30]}"

