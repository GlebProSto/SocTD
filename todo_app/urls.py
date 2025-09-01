from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
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
    path('tasks/', views.tasks, name='tasks'),
    path('tasks/create', views.create_tasks, name='create_tasks'),
    path('tasks/<int:task_id>', views.task_detail, name='task_detail'),
    path('tasks/<int:task_id>/add_subtask/', views.add_subtask, name='add_subtask'),
]