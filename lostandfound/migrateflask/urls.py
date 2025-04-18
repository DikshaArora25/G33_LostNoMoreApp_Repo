from django.urls import path
from . import views
from django.urls import path
from migrateflask.views import logout_view  # make sure this import is correct





urlpatterns = [
 


    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
   path('report-lost/', views.report_item, {'status': 'lost'}, name='report_lost'),
   path('report-found/', views.report_item, {'status': 'found'}, name='report_found'),

    path('gallery/', views.gallery, name='gallery'),
    path('edit_item/<int:item_id>/', views.edit_item, name='edit_item'),
    path('delete/<int:item_id>/', views.delete_item, name='delete_item'),
    path('contact/', views.contact_view, name='contact'),
    path('profile/', views.profile, name='profile'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('search/', views.search_view, name='search'), 
   
   
      # other paths...
    path('logout/', logout_view, name='logout'),  # this is key
    path('claim/<int:item_id>/', views.claim_item, name='claim_item'),
     
    path('chatbot/', views.chatbot_query, name='chatbot_query'),


]