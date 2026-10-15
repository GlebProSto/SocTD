import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib import messages
from .models import TodoPost, Comment, Profile, Repost, Friendship,Notification,SubTask,TaskList,Chat,Message
from .forms import CustomUserCreationForm, TodoPostForm, CommentForm, ProfileForm, RepostForm, SubTaskForm, TaskListForm, UserSearchForm
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator

def home(request):
    posts = (
        TodoPost.objects
        .select_related('author', 'author__profile')
        .prefetch_related('likes', 'reposts', 'comments')
        .order_by('-created_at')
    )
    page_obj = Paginator(posts, 10).get_page(request.GET.get('page'))
    context = {'posts': page_obj.object_list, 'page_obj': page_obj}
    if request.user.is_authenticated:
        context['form'] = TodoPostForm()
    return render(request, 'home.html', context)

 
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
    
    if section == 'repost':
        reposted_posts = TodoPost.objects.filter(
            repost__user=request.user
        )
        own_posts = TodoPost.objects.filter(author=request.user)
        posts = (reposted_posts | own_posts).distinct().order_by('-created_at')
    else:
        # default (and any unknown section) -> own posts, avoids UnboundLocalError
        posts = TodoPost.objects.filter(author=request.user).order_by('-created_at')
    
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
            Q(from_user=request.user, to_user=user) |
            Q(from_user=user, to_user=request.user),
            accepted=True
        ).exists()
    
    section = request.GET.get('section', 'posts')
    
    if section == 'repost':
        reposted_posts = TodoPost.objects.filter(
            repost__user=user
        )
        own_posts = TodoPost.objects.filter(author=user)
        posts = (reposted_posts | own_posts).distinct().order_by('-created_at')
    else:
        # default (and any unknown section) -> own posts, avoids UnboundLocalError
        posts = TodoPost.objects.filter(author=user).order_by('-created_at')

    context = {
        'user': user,
        'profile': profile,
        'posts': posts,
        'is_friend': is_friend,
        'section': section,
    }
    return render(request, 'profile.html', context)

@login_required
def create_post(request):
    """Handle new post creation from any page.  We only validate content
    because the form no longer includes author etc.
    """
    if request.method == 'POST':
        form = TodoPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, "Пост опубликован")
        else:
            messages.error(request, "Не удалось опубликовать пост. Проверьте текст.")
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
        # Guard against open-redirect: only allow local destinations
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)
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
            messages.success(request, 'Задача создана')
            return redirect('tasks')
        else:
            messages.error(request, 'Исправьте ошибки в форме создания задачи')
    else:
        form = TaskListForm(initial={'date': timezone.now().date()})
    return render(request, 'task_create.html', {'form': form})

@login_required
def tasks(request):
    task_list = TaskList.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'tasks.html', {'task_list': task_list})

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
    tasklist = subtask.tasklist_set.first()
    
    if not tasklist or tasklist.user != request.user:
        return redirect('tasks')
    
    if request.method == 'POST':
        subtask.completed = not subtask.completed
        subtask.save()
    
    return redirect('task_detail', task_id=tasklist.id)

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
@require_POST
def add_comment(request, post_id):
    post = get_object_or_404(TodoPost, id=post_id)

    content = request.POST.get('content', '').strip()
    if content:
        comment = Comment.objects.create(
            post=post,
            author=request.user,
            content=content
        )
        # Notify the post author (but not on their own post)
        if post.author != request.user:
            Notification.objects.get_or_create(
                user=post.author,
                from_user=request.user,
                notification_type='comment',
                post=post,
                comment=comment,
            )

    return redirect('home')


@login_required
@require_POST
def like_post(request, post_id):
    post = get_object_or_404(TodoPost, id=post_id)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
        # clean up the corresponding like notification
        Notification.objects.filter(
            user=post.author, from_user=request.user,
            notification_type='like', post=post
        ).delete()
    else:
        post.likes.add(request.user)
        liked = True
        if post.author != request.user:
            Notification.objects.get_or_create(
                user=post.author, from_user=request.user,
                notification_type='like', post=post,
            )
    return JsonResponse({'liked': liked, 'likes_count': post.likes.count()})

@login_required
@require_POST
def repost_post(request, post_id):
    post = get_object_or_404(TodoPost, id=post_id)
    if Repost.objects.filter(user=request.user, post=post).exists():
        Repost.objects.filter(user=request.user, post=post).delete()
        reposted = False
        Notification.objects.filter(
            user=post.author, from_user=request.user,
            notification_type='repost', post=post
        ).delete()
    else:
        Repost.objects.create(user=request.user, post=post)
        reposted = True
        if post.author != request.user:
            Notification.objects.get_or_create(
                user=post.author, from_user=request.user,
                notification_type='repost', post=post,
            )

    return JsonResponse({
        'reposted': reposted,
        'reposts_count': post.reposts.count()
    })



@login_required
def search_users(request):
    """Simple search page that lists users and allows sending/removing
    friendship requests."""
    query = request.GET.get('q', '').strip()
    users_qs = User.objects.exclude(id=request.user.id)
    if query:
        users_qs = users_qs.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )
    users_qs = users_qs.order_by('username')

    # Batch-fetch all friendships involving the current user (avoids N+1)
    friend_map = {}
    for f in Friendship.objects.filter(
        Q(from_user=request.user) | Q(to_user=request.user)
    ):
        other = f.to_user if f.from_user_id == request.user.id else f.from_user
        friend_map[other.id] = f

    results = []
    for u in users_qs:
        existing = friend_map.get(u.id)
        status = 'none'
        if existing:
            if existing.accepted:
                status = 'friends'
            elif existing.from_user_id == request.user.id:
                status = 'requested'
            else:
                status = 'pending'
        results.append({'user': u, 'status': status})

    form = UserSearchForm(request.GET)
    return render(request, 'search_users.html', {'results': results, 'form': form, 'query': query})

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
            # remove any lingering friend-request notifications in both directions
            Notification.objects.filter(
                Q(user=to_user, from_user=request.user) |
                Q(user=request.user, from_user=to_user),
                notification_type='friend_request'
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
        # ensure the friendship record exists and is marked accepted
        try:
            friendship = Friendship.objects.get(
                from_user=notification.from_user,
                to_user=request.user
            )
            friendship.accepted = True
            friendship.save()
        except Friendship.DoesNotExist:
            # something went wrong earlier; create it to maintain consistency
            friendship = Friendship.objects.create(
                from_user=notification.from_user,
                to_user=request.user,
                accepted=True
            )
        
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
        
        # remove the original request so it no longer shows up
        notification.delete()
        
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

@login_required
def friendship_list(request): 
    section = request.GET.get('section', 'subscribers')
    subscribers = None
    subscribed = None
    
    if section == 'subscribers':
        subscribers = Friendship.objects.filter(
            to_user=request.user,
            accepted=True
        ).select_related('from_user').order_by('from_user__username')
    
    elif section == 'subscribed':
        subscribed = Friendship.objects.filter(
            from_user=request.user,
            accepted=True
        ).order_by('to_user__username')
    
    return render(request, 'friendship.html', {
        'subscribers': subscribers,
        'subscribed': subscribed,
        'section': section  
    })
@login_required
def chat(request, username):
    interlocutor = get_object_or_404(User, username=username)
    if interlocutor == request.user:
        return redirect('profile')

    chat = Chat.objects.filter(participants=interlocutor).filter(participants=request.user).first()
    if not chat:
        chat = Chat.objects.create()
        chat.participants.add(request.user)
        chat.participants.add(interlocutor)

    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if text:
            Message.objects.create(chat=chat, sender=request.user, text=text)
            return redirect('chat', username=username)

    messages_list = chat.messages.all().order_by('timestamp')

    # Mark messages addressed to the current user as read when opening the chat
    unread_to_user = messages_list.filter(is_read=False).exclude(sender=request.user)
    if unread_to_user.exists():
        unread_to_user.update(is_read=True)

    # `chat` object is not needed in template; avoid accidentally rendering it
    return render(request, 'chat.html', {'chat_messages': messages_list, 'interlocutor': interlocutor})


@login_required
def api_send_message(request):
    """AJAX endpoint: POST {username, text} -> creates or reuses chat and message"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    data = json.loads(request.body.decode('utf-8')) if request.body else request.POST
    username = data.get('username')
    text = data.get('text', '').strip()
    if not username or not text:
        return JsonResponse({'error': 'username and text required'}, status=400)
    to_user = get_object_or_404(User, username=username)
    if to_user == request.user:
        return JsonResponse({'error': 'cannot send to yourself'}, status=400)
    chat = Chat.objects.filter(participants=to_user).filter(participants=request.user).first()
    if not chat:
        chat = Chat.objects.create()
        chat.participants.add(request.user)
        chat.participants.add(to_user)
    message = Message.objects.create(chat=chat, sender=request.user, text=text)
    return JsonResponse({'id': message.id, 'text': message.text, 'sender': message.sender.username, 'timestamp': message.timestamp.isoformat()})


@login_required
def api_fetch_messages(request):
    """AJAX endpoint: GET ?username=...&after_id=... -> returns list of messages for chat newer than after_id"""
    username = request.GET.get('username')
    after_id = request.GET.get('after_id')
    if not username:
        return JsonResponse({'error': 'username required'}, status=400)
    other = get_object_or_404(User, username=username)
    chat = Chat.objects.filter(participants=other).filter(participants=request.user).first()
    if not chat:
        return JsonResponse({'messages': []})
    qs = chat.messages.order_by('timestamp')
    if after_id:
        try:
            after_id = int(after_id)
            qs = qs.filter(id__gt=after_id)
        except ValueError:
            pass
    messages = []
    last_id = None
    for m in qs:
        messages.append({'id': m.id, 'text': m.text, 'sender': m.sender.username, 'timestamp': m.timestamp.isoformat()})
        last_id = m.id
    # mark fetched messages as read if they were sent to the current user
    qs.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    return JsonResponse({'messages': messages, 'last_id': last_id})


@login_required
def messages_list(request):
    # Prefetch participants and messages to avoid N+1 queries
    chats = (
        Chat.objects
        .filter(participants=request.user)
        .distinct()
        .prefetch_related('participants', 'messages')
    )
    chat_items = []
    for c in chats:
        other = next(
            (p for p in c.participants.all() if p.id != request.user.id), None
        )
        all_msgs = list(c.messages.all())
        last = max(all_msgs, key=lambda m: m.timestamp) if all_msgs else None
        unread = sum(
            1 for m in all_msgs
            if not m.is_read and m.sender_id != request.user.id
        )
        chat_items.append({'chat': c, 'other': other, 'last': last, 'unread': unread})

    # sort by last activity (newest first)
    chat_items.sort(
        key=lambda item: item['last'].timestamp if item['last'] else item['chat'].created_at,
        reverse=True,
    )
    return render(request, 'messages.html', {'chat_items': chat_items})

