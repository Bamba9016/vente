from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget
from .models import CustomUser
from django.core.exceptions import ValidationError

from djassa.models import Publication, Demande, Message
import phonenumbers

User = get_user_model()

class InscriptionForm(forms.ModelForm):
    mot_de_passe = forms.CharField(widget=forms.PasswordInput(), label="Mot de passe")
    confirmation_mot_de_passe = forms.CharField(widget=forms.PasswordInput(), label="Confirmez le mot de passe")

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'date_of_birth',
            'gender',
            'phone_number',
            'country',
            'city',
            'profile_picture',
            'mot_de_passe',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'country': CountrySelectWidget(),  # widget pour liste déroulante des pays
        }
        labels = {
            'username': 'Nom d’utilisateur',
            'email': 'Adresse e-mail',
            'first_name': 'Prénom',
            'last_name': 'Nom',
            'date_of_birth': 'Date de naissance',
            'gender': 'Genre',
            'phone_number': 'Numéro de téléphone',
            'country': 'Pays',
            'city': 'Ville',
            'profile_picture': 'Photo de profil',
        }



    def save(self, commit=True):
        utilisateur = super().save(commit=False)
        utilisateur.set_password(self.cleaned_data['mot_de_passe'])
        if commit:
            utilisateur.save()
        return utilisateur

class LoginForm(forms.Form):
    username = forms.CharField(
        label="Nom d’utilisateur",
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    mot_de_passe = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'date_of_birth', 'gender', 'profile_picture']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'username': 'Nom d’utilisateur',
            'email': 'Adresse e-mail',
            'first_name': 'Prénom',
            'last_name': 'Nom',
            'date_of_birth': 'Date de naissance',
            'gender': 'Genre',
        }

class PasswordUpdateForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Mot de passe actuel",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password1 = forms.CharField(
        label="Nouveau mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password2 = forms.CharField(
        label="Confirmez le nouveau mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['old_password', 'new_password1', 'new_password2']


class PublicationForm(forms.ModelForm):
    class Meta:
        model = Publication
        fields = ['content', 'fichier', 'categorie', 'nom_du_produit', 'fonction']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Exprimez-vous...'}),
            'categorie': forms.Select(attrs={'class': 'form-control'}),
            'fonction': forms.Select(attrs={'class': 'form-control'}),
            'nom_du_produit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du produit'}),

        }
        labels = {
            'content': 'Contenu',
            'fichier': 'fichier',

            'categorie': 'Catégorie',
            'nom_du_produit': 'Nom du produit',
            'fonction': 'État du produit',
        }

    def clean_fichier(self):
        fichier = self.cleaned_data.get('fichier')
        if fichier:
            if not fichier.name.endswith(('.png', '.jpg', '.jpeg', '.gif', '.mp4', '.mov', '.avi')):
                raise forms.ValidationError(
                    "Veuillez télécharger une image (png, jpg, jpeg, gif) ou une vidéo (mp4, mov, avi).")
        return fichier
class DemandeForm(forms.ModelForm):
    class Meta:
        model = Demande
        fields = ['nom_du_produit', 'description', 'categorie', 'prix_achat', 'etat_du_produit', 'numero_telephone']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Décrivez votre demande ici...'}),
            'prix_achat': forms.NumberInput(attrs={'placeholder': 'Ex: 100.00'}),
            'numero_telephone': forms.TextInput(attrs={'placeholder': 'Ex: +123456789'}),
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Écrire un message...'}),
        }