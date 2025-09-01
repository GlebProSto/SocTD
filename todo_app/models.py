# todo_app/models.py
import datetime
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def get_friends_count(self):
        return self.user.friendship_requests_sent.filter(accepted=True).count()
    
    def get_followers_count(self):
        return self.user.friendship_requests_received.filter(accepted=True).count()
    
    def get_following_count(self):
        return self.user.friendship_requests_sent.filter(accepted=True).count()

class Friendship(models.Model):
    from_user = models.ForeignKey(User, related_name='friendship_requests_sent', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='friendship_requests_received', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('from_user', 'to_user')

class TodoPost(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=280)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    reposts = models.ManyToManyField(User, through='Repost', related_name='reposted_posts', blank=True)

    def __str__(self):
        return f'{self.author.username} - {self.content[:50]}'

class Repost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(TodoPost, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'post']
    
    def __str__(self):
        return f'{self.user.username} reposted {self.post.author.username}\'s post'

class Comment(models.Model):
    post = models.ForeignKey(TodoPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=280)
    created_at = models.DateTimeField(auto_now_add=True)

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('friend_request', 'Заявка в друзья'),
        ('friend_accept', 'Принятие заявки'),
        ('like', 'Лайк'),
        ('comment', 'Комментарий'),
        ('repost', 'Репост'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    post = models.ForeignKey(TodoPost, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.from_user.username} → {self.user.username}: {self.notification_type}"
    
class SubTask(models.Model):
    text = models.CharField(max_length=280) 
    completed = models.BooleanField(default=False)  
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.text
    
class TaskList(models.Model): 
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200) 
    date = models.DateField() 
    subtasks = models.ManyToManyField(SubTask)
    created_at = models.DateTimeField(default=datetime.datetime.now)
    @property
    def completion_percentage(self):
        total = self.subtasks.count()
        if total == 0:
            return 0
        completed = self.subtasks.filter(completed=True).count()
        return (completed / total) * 100




