from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('search/', views.search, name='search'),
    
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    
    path('projects/', views.project_list, name='project_list'),
    path('projects/create/', views.project_create, name='project_create'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('projects/<int:pk>/settings/', views.project_settings, name='project_settings'),
    path('projects/<int:pk>/add-collaborator/', views.project_add_collaborator, name='project_add_collaborator'),
    path('projects/<int:pk>/remove-collaborator/<int:user_id>/', views.project_remove_collaborator, name='project_remove_collaborator'),
    path('projects/<int:project_pk>/upload/', views.document_upload, name='document_upload'),
    path('projects/<int:project_pk>/work-items/', views.work_item_list, name='project_work_items'),
    path('projects/<int:project_pk>/work-items/create/', views.work_item_create, name='work_item_create'),
    
    path('documents/<int:pk>/', views.document_detail, name='document_detail'),
    path('documents/<int:pk>/upload-version/', views.document_upload_version, name='document_upload_version'),
    path('documents/<int:pk>/compare/', views.document_compare, name='document_compare'),
    path('documents/<int:document_pk>/pull-request/create/', views.pull_request_create, name='pull_request_create'),
    
    path('pull-requests/', views.pull_request_list, name='pull_request_list'),
    path('pull-requests/<int:pk>/', views.pull_request_detail, name='pull_request_detail'),
    path('pull-requests/<int:pk>/review/', views.pull_request_review, name='pull_request_review'),
    path('pull-requests/<int:pk>/merge/', views.pull_request_merge, name='pull_request_merge'),
    
    path('work-items/', views.work_item_list, name='work_item_list'),
    path('work-items/<int:pk>/', views.work_item_detail, name='work_item_detail'),
    path('work-items/<int:pk>/update-status/', views.work_item_update_status, name='work_item_update_status'),
    
    path('teams/', views.team_list, name='team_list'),
    path('teams/create/', views.team_create, name='team_create'),
    path('teams/<int:pk>/', views.team_detail, name='team_detail'),
    
    path('comments/add/', views.add_comment, name='add_comment'),
]
