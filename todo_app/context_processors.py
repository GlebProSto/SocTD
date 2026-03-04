from .models import Message


def unread_counts(request):
    if not request.user.is_authenticated:
        return {}
    total_unread = Message.objects.filter(chat__participants=request.user, is_read=False).exclude(sender=request.user).count()
    notif_unread = request.user.notifications.filter(is_read=False).count()
    return {'unread_messages_total': total_unread, 'unread_notifications_total': notif_unread}
