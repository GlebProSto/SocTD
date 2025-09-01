import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib import messages
from .models import TodoPost, Comment, Profile, Repost, Friendship,Notification,SubTask,TaskList
from .forms import CustomUserCreationForm, TodoPostForm, CommentForm, ProfileForm, RepostForm,SubTaskForm,TaskListForm
from django.db.models import Q

def home(request):
    posts = TodoPost.objects.all().order_by('-created_at')
    if request.user.is_authenticated:
        form = TodoPostForm()
        return render(request, 'home.html', {
            'form': form,
            'posts': posts
        })
    else:
        return render(request, 'home.html',{
            'posts' : posts
        }) 
 
    
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def profile(request):
    section = request.GET.get('section', 'posts')
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if section == 'posts':  
        posts = TodoPost.objects.filter(author=request.user).order_by('-created_at')
    elif section == 'repost':
        reposted_posts = TodoPost.objects.filter(
            repost__user=request.user
        ).order_by('-repost__created_at')
        
        own_posts = TodoPost.objects.filter(author=request.user)
        
        posts = (reposted_posts | own_posts).distinct().order_by('-created_at')
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile) 
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)
    
    return render(request, 'profile.html', {
        'user' : request.user,
        'form': form, 
        'profile': profile,
        'posts': posts,
        'section': section,
    })

def user_profile(request, username):
    user = get_object_or_404(User, username=username)
    profile, created = Profile.objects.get_or_create(user=user)
    
    is_friend = False
    if request.user.is_authenticated and request.user != user:
        is_friend = Friendship.objects.filter(
            from_user=request.user, 
            to_user=user, 
            accepted=True
        ).exists()
    
    section = request.GET.get('section', 'posts')
    
    if section == 'posts':
        posts = TodoPost.objects.filter(author=user).order_by('-created_at')
        reposts = []
    elif section == 'repost':
        reposts = Repost.objects.filter(user=user).order_by('-created_at')
        posts = []
    else:
        posts = TodoPost.objects.filter(author=user).order_by('-created_at')
    
    context = {
        'user': user,
        'profile': profile,
        'posts': posts,
        'is_friend': is_friend,
        'section': section,
        'reposts': reposts
    }
    return render(request, 'profile.html', context)

@login_required
def create_post(request):
    if request.method == 'POST':
        form = TodoPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('home')
    return redirect('home')

    
@login_required
def create_tasks(request):
    if request.method == 'POST':
        form = TaskListForm(request.POST)
        if form.is_valid():
            tasklist = form.save(commit=False)
            tasklist.user = request.user    
            tasklist.save()
            return redirect('tasks')
    else:
        form = TaskListForm()
    
    return render(request, 'task_create.html', {'form': form})

@login_required
def tasks(request):
    task_list = TaskList.objects.filter(user=request.user).order_by('-created_at')
    if request.user:
        return render(request,'tasks.html',{'task_list':task_list})

@login_required
def task_detail(request, task_id):
    task = get_object_or_404(TaskList, id=task_id, user=request.user)
    subtask_list = task.subtasks.all().order_by('completed', '-created_at')
    subtask_form = SubTaskForm()
    return render(request, 'task_detail.html', {
        'task': task, 
        'subtask_form': subtask_form, 
        'subtask_list': subtask_list
    })

@login_required
def subtask_toggle(request, subtask_id):
    subtask = get_object_or_404(SubTask, id=subtask_id)
    
    # Получаем TaskList, к которому привязана подзадача (через M2M связь)
    # Берем первый попавшийся, обычно подзадача принадлежит только одному списку
    tasklist = subtask.tasklist_set.first()
    
    # Проверяем права доступа
    if not tasklist or tasklist.user != request.user:
        return redirect('tasks')  # или на страницу задачи, если есть task_id
    
    if request.method == 'POST':
        subtask.completed = not subtask.completed
        subtask.save()
    
    return redirect('task_detail', task_id=tasklist.id)
@login_required
def like_post(request, post_id):
    post = get_object_or_404(TodoPost, id=post_id)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
    return JsonResponse({'liked': liked, 'likes_count': post.likes.count()})
    
@login_required
def add_subtask(request,task_id):
    task = get_object_or_404(TaskList, id=task_id,user=request.user)
    if request.method == 'POST':
        form = SubTaskForm(request.POST)
        if form.is_valid():
            new_subtask = form.save()
            task.subtasks.add(new_subtask)
            return redirect('task_detail', task_id=task_id)

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(TodoPost, id=post_id)
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Comment.objects.create(
                post=post,
                author=request.user,
                content=content
            )
    
    return redirect('home')


@login_required
def like_post(request, post_id):
    post = get_object_or_404(TodoPost, id=post_id)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
    return JsonResponse({'liked': liked, 'likes_count': post.likes.count()})

@login_required
def repost_post(request, post_id):
    post = get_object_or_404(TodoPost, id=post_id)
    if Repost.objects.filter(user=request.user, post=post).exists():
        Repost.objects.filter(user=request.user, post=post).delete()
        reposted = False
    else:
        Repost.objects.create(user=request.user, post=post)
        reposted = True
    
    return JsonResponse({
        'reposted': reposted, 
        'reposts_count': post.reposts.count()
    })



@login_required
def add_friend(request, username):
    to_user = get_object_or_404(User, username=username)
    
    if request.user == to_user:
        messages.error(request, "Нельзя добавить себя в друзья")
        return redirect('user_profile', username=username) 
    
    existing_friendship = Friendship.objects.filter(
        (Q(from_user=request.user, to_user=to_user) |
         Q(from_user=to_user, to_user=request.user))
    ).first()
    
    if existing_friendship:
        if existing_friendship.accepted:
            Friendship.objects.filter(
                Q(from_user=request.user, to_user=to_user) |
                Q(from_user=to_user, to_user=request.user)
            ).delete()
            messages.success(request, f"{to_user.username} удален из друзей")
        else:
            messages.info(request, "Заявка уже отправлена")
    else:
        friendship = Friendship.objects.create(
            from_user=request.user,
            to_user=to_user,
            accepted=False
        )
        
        Notification.objects.create(
            user=to_user,
            from_user=request.user,
            notification_type='friend_request'
        )
        messages.success(request, f"Заявка в друзья отправлена {to_user.username}")
    
    return redirect('user_profile', username=username)

@login_required
def accept_friend(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    
    if notification.notification_type == 'friend_request':
        friendship = Friendship.objects.get(
            from_user=notification.from_user,
            to_user=request.user
        )
        friendship.accepted = True
        friendship.save()
        
        
        reverse_friendship, created = Friendship.objects.get_or_create(
            from_user=request.user,
            to_user=notification.from_user,
            defaults={'accepted': True}
        )

        if not created and not reverse_friendship.accepted:
            reverse_friendship.accepted = True
            reverse_friendship.save()
        
        Notification.objects.create(
            user=notification.from_user,
            from_user=request.user,
            notification_type='friend_accept'
        )
        
        notification.is_read = True
        notification.save()
        
        messages.success(request, f"Вы приняли заявку в друзья от {notification.from_user.username}")
    
    return redirect('notifications')

@login_required
def notifications(request):
    user_notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')
    
    unread_notifications = user_notifications.filter(is_read=False)
    unread_notifications.update(is_read=True)
    
    return render(request, 'notifications.html', {
        'notifications': user_notifications
    })



