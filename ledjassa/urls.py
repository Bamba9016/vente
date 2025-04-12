from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from djassa import views
from djassa.views import inbox, conversation

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.inscription_view, name='inscription'),
    path('login/', views.login_view, name='login'),

    path('accueil/', views.accueil_view, name='accueil'),
    path('accueil/profile/', views.profile_view, name='profile'),
    path('accueil/profilepublication/<int:user_id>/', views.profilepublication_view, name='profilepublication'),

    path('accueil/modifier_profile/', views.modifier_profile_view, name='modifier_profile'),
    path('accueil/change_password/', views.change_password, name='change_password'),
    path('accueil/logout/', views.logout_view, name='logout'),
    path('accueil/publication/', views.publication_view, name='publication'),
    path('publications/', views.publication_list, name='publication_list'),

    path('accueil/like<int:publication_id>/', views.like_publication, name='like_publication'),
    path('accueil/comment/<int:publication_id>/', views.comment_publication, name='comment_publication'),
    path('accueil/share/<int:publication_id>/', views.share_publication, name='share_publication'),

path('subscribe/<int:user_id>/', views.subscribe_view, name='subscribe'),

path('accueil/unsubscribe/<int:user_id>/', views.unsubscribe_view, name='unsubscribe'),
path('accueil/vente/', views.page_de_vente, name='page_de_vente'),
    path('enregistrer-demande/', views.enregistrer_demande, name='enregistrer_demande'),
    path('categories/', views.choisir_categorie, name='choisir_categorie'),
    path('demandes/<str:categorie>/', views.voir_demandes, name='voir_demandes'),

    path('user/<int:user_id>/abonnements/', views.abonnements_view, name='abonnements'),
    path('user/<int:viewuser_id>/viewabonnements/', views.viewabonnements_view, name='viewabonnements'),

    path('user/<int:user_id>/abonnes/', views.abonnes_view, name='abonnes'),
    path('user/<int:viewuser_id>/viewabonnes/', views.viewabonnes_view, name='viewabonnes'),

    path('user/<int:user_id>/amis/', views.amis_view, name='amis'),
    path('user/<int:user_id>/subscribe/', views.subscribe_view, name='subscribe_view'),
    path('user/<int:user_id>/unsubscribe/', views.unsubscribe_view, name='unsubscribe_view'),

    path('profile/<int:user_id>/', views.profile_view, name='profile'),
    path('messagerie/', views.inbox, name='inbox'),
    path('messagerie/<int:user_id>/', views.conversation, name='conversation'),
    path('parametres/', views.parametres_view, name='parametres'),
    path('comment/<int:comment_id>/reply/', views.reply_to_comment, name='reply_to_comment'),
    path('ajax/recherche/', views.recherche_ajax, name='recherche_ajax'),
    path('recherche/', views.recherche_resultats, name='recherche_resultats'),
path('publication/<int:publication_id>/', views.publication_detail, name='publication_detail'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('commentaire/<int:publication_id>/', views.page_commentaire, name='page_commentaire'),
path('api/marquer-vues/', views.marquer_publications_vues, name='marquer_vues'),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
