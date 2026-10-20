from django.urls import path
from . import views
from django.views.generic import TemplateView
from .views import *


# The urls which routes to respective view function
urlpatterns = [
    # path('celery/', views.celeryview, name='celery'),
    path('logout/', views.logoutview, name='logout_view'),
    path('addticket/', views.addticket, name='addticket'),
    path('addticketadmin/', views.addticketadmin, name='addticketadmin'),
    path('deleteticket/', views.deleteticket, name='deleteticket'),
    path('home/', views.home, name='home'),
    path('login/', views.login_view, name='login_view'),
    path('', views.base, name='base'),
    path('register/', views.register, name='register'),
    path('listticket/', views.listticket, name='listticket'),
    path('listuser/', views.listuser, name='listuser'),
    path('deleteuser/', views.deleteuser, name='deleteuser'),
    path('edituser/', views.edituser, name='edituser'),
    path('editticket/', views.editticket, name='editticket'),
    path('editticketadmin/', views.editticketadmin, name='editticketadmin'),
    path('view_ticket_system_admin/', views.viewticket, name='viewticket'),
    path('edit_state_ticket_to_done/', views.edit_state_ticket_to_done, name='edit_state_ticket_to_done'),
    path('edit_state_ticket_to_progress/', views.edit_state_ticket_to_progress, name='edit_state_ticket_to_progress'),
]
