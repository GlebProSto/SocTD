from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('messages/', views.messages_list, name='messages'),
    path('api/messages/send/', views.api_send_message, name='api_send_message'),
    path('api/messages/updates/', views.api_fetch_messages, name='api_fetch_messages'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('add_friend/<str:username>/', views.add_friend, name='add_friend'),
    path('notifications/', views.notifications, name='notifications'),
    path('accept_friend/<int:notification_id>/', views.accept_friend, name='accept_friend'),
    path('create_post/', views.create_post, name='create_post'),
    path('like_post/<int:post_id>/', views.like_post, name='like_post'),
    path('repost_post/<int:post_id>/', views.repost_post, name='repost_post'),
    path('add_comment/<int:post_id>/', views.add_comment, name='add_comment'),
    path('profile/<str:username>/', views.user_profile, name='user_profile'),
    path('search/', views.search_users, name='search_users'),
    path('tasks/', views.tasks, name='tasks'),
    path('tasks/create', views.create_tasks, name='create_tasks'),
    path('tasks/<int:task_id>', views.task_detail, name='task_detail'),
    path('tasks/<int:task_id>/add_subtask/', views.add_subtask, name='add_subtask'),
    path('tasks/subtask/<int:subtask_id>/toggle/', views.subtask_toggle, name='subtask_toggle'),
    path('friendship/', views.friendship_list, name='friendship_list'),
    path('chat/<str:username>', views.chat, name='chat'),
]