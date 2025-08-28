from django.contrib import admin
from .models import Profile, TodoPost, Comment, Repost, Friendship, Notification


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'bio', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username']

@admin.register(TodoPost)
class TodoPostAdmin(admin.ModelAdmin):
    list_display = ['author', 'content', 'completed', 'created_at']
    list_filter = ['completed', 'created_at']
    search_fields = ['author__username', 'content']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'post', 'content', 'created_at']
    list_filter = ['created_at']
    search_fields = ['author__username', 'content']

@admin.register(Repost)
class RepostAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'post__content']

@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'to_user', 'accepted', 'created_at']
    list_filter = ['accepted', 'created_at']
    search_fields = ['from_user__username', 'to_user__username']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'from_user', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'from_user__username']