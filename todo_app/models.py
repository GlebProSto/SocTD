# todo_app/models.py
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class TodoPost(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=280)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    # Добавляем поле для репостов
    reposts = models.ManyToManyField(User, through='Repost', related_name='reposted_posts', blank=True)

    def __str__(self):
        return f'{self.author.username} - {self.content[:50]}'

class Repost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(TodoPost, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'post']  # Один репост на пользователя
    
    def __str__(self):
        return f'{self.user.username} reposted {self.post.author.username}\'s post'

class Comment(models.Model):
    post = models.ForeignKey(TodoPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=280)
    created_at = models.DateTimeField(auto_now_add=True)