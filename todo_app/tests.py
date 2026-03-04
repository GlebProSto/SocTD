from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Profile, TodoPost, Chat, Message, TaskList, Comment, Repost, Friendship, Notification
from django.utils import timezone
import json

User = get_user_model()

class BasicModelTests(TestCase):
    def test_profile_created(self):
        user = User.objects.create_user(username='u', password='p')
        profile = Profile.objects.get(user=user)
        self.assertIsNotNone(profile)

    def test_create_post(self):
        user = User.objects.create_user(username='u2', password='p')
        post = TodoPost.objects.create(author=user, content='hello')
        self.assertEqual(str(post).split(' - ')[0], 'u2')


class MessageTests(TestCase):
    def setUp(self):
        self.u1 = User.objects.create_user(username='alice', password='p')
        self.u2 = User.objects.create_user(username='bob', password='p')
        self.chat = Chat.objects.create()
        self.chat.participants.add(self.u1, self.u2)

    def test_unread_and_mark_read_on_open(self):
        m = Message.objects.create(chat=self.chat, sender=self.u2, text='hello')
        self.assertFalse(m.is_read)
        # alice opens the chat
        self.client.force_login(self.u1)
        resp = self.client.get('/chat/bob')
        m.refresh_from_db()
        self.assertTrue(m.is_read)

    def test_api_send_and_fetch(self):
        self.client.force_login(self.u1)
        # send message to bob
        resp = self.client.post('/api/messages/send/', data=json.dumps({'username': 'bob', 'text': 'hey'}), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIn('id', data)
        msg_id = data['id']
        # bob fetches new messages
        self.client.logout()
        self.client.force_login(self.u2)
        resp2 = self.client.get(f'/api/messages/updates/?username=alice&after_id={msg_id-1}')
        self.assertEqual(resp2.status_code, 200)
        d2 = json.loads(resp2.content)
        self.assertTrue(any(m['id']==msg_id for m in d2.get('messages', [])))
class FeatureTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u3', password='p')
        self.other = User.objects.create_user(username='other', password='p')

    def test_task_creation_date_default(self):
        self.client.force_login(self.user)
        resp = self.client.get('/tasks/create')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('type="date"', resp.content.decode())

    def test_search_and_friend_request(self):
        self.client.force_login(self.user)
        resp = self.client.get('/search/')
        self.assertContains(resp, 'other')
        resp2 = self.client.post(f'/add_friend/{self.other.username}/', follow=True)
        self.assertEqual(resp2.status_code, 200)
        self.assertTrue(self.other.notifications.filter(notification_type='friend_request').exists())

    def test_profile_editing(self):
        self.client.force_login(self.user)
        resp = self.client.post('/profile/', {'bio': 'hi'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.profile.bio, 'hi')

    def test_create_post_redirects_back(self):
        self.client.force_login(self.user)
        resp = self.client.post('/create_post/', {'content': 'xyz', 'next': '/messages/'}, follow=True)
        self.assertEqual(resp.redirect_chain[-1][0], '/messages/')
        self.assertEqual(TodoPost.objects.filter(author=self.user, content='xyz').count(), 1)
    def test_post_form_works(self):
        self.client.force_login(self.user)
        resp = self.client.post('/create_post/', {'content': 'hello world', 'next': '/'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(TodoPost.objects.filter(author=self.user, content='hello world').exists())

    def test_profile_message_form_redirects(self):
        # send message directly from profile page
        self.client.force_login(self.user)
        resp = self.client.post(f'/chat/{self.other.username}', {'text': 'hi there'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        # after posting, chat page should exist with message
        self.assertTrue(Message.objects.filter(sender=self.user, text='hi there').exists())

    def test_profile_statistics_display(self):
        # create posts with likes and comments to check stats on profile
        self.client.force_login(self.user)
        p = TodoPost.objects.create(author=self.user, content='stat post')
        p.likes.add(self.other)
        Comment.objects.create(post=p, author=self.other, content='nice')
        Repost.objects.create(user=self.other, post=p)
        resp = self.client.get(f'/profile/{self.user.username}/')
        # numbers are bolded in template; match markup accordingly
        self.assertContains(resp, '<strong>1</strong> лайков')
        self.assertContains(resp, '<strong>1</strong> репостов')
        self.assertContains(resp, '<strong>1</strong> комментов')

    def test_no_left_message_form_on_other_profile(self):
        self.client.force_login(self.user)
        resp = self.client.get(f'/profile/{self.other.username}/')
        # left textarea should be gone
        self.assertNotContains(resp, 'Написать сообщение...')
        # right-hand write link still present
        self.assertContains(resp, '<a href="/chat/other"')

    def test_accept_friend_notification_removed(self):
        # sender sends request, recipient accepts and notification should disappear
        u1 = self.user
        u2 = self.other
        Friendship.objects.create(from_user=u1, to_user=u2, accepted=False)
        notif = Notification.objects.create(user=u2, from_user=u1, notification_type='friend_request')
        self.client.force_login(u2)
        resp = self.client.post(f'/accept_friend/{notif.id}/', follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Notification.objects.filter(id=notif.id).exists())
        self.assertTrue(Notification.objects.filter(user=u1, notification_type='friend_accept').exists())

    def test_accept_friend_with_missing_record(self):
        # simulate the error case where the friendship row was deleted before acceptance
        u1 = self.user
        u2 = self.other
        notif = Notification.objects.create(user=u2, from_user=u1, notification_type='friend_request')
        self.client.force_login(u2)
        resp = self.client.post(f'/accept_friend/{notif.id}/', follow=True)
        self.assertEqual(resp.status_code, 200)
        # friendship should have been created and marked accepted
        self.assertTrue(Friendship.objects.filter(from_user=u1, to_user=u2, accepted=True).exists())
        self.assertFalse(Notification.objects.filter(id=notif.id).exists())

    def test_notification_badge_updates(self):
        # badge on nav should reflect unread notifications
        u1 = self.user
        u2 = self.other
        # send friend request to u2
        Notification.objects.create(user=u2, from_user=u1, notification_type='friend_request')
        self.client.force_login(u2)
        resp = self.client.get('/')
        # should see badge count 1
        self.assertContains(resp, '<span class="badge">1</span>')
        # accept the request
        notif = Notification.objects.get(user=u2, from_user=u1, notification_type='friend_request')
        self.client.post(f'/accept_friend/{notif.id}/', follow=True)
        resp2 = self.client.get('/')
        self.assertNotContains(resp2, '<span class="badge">1</span>')

    def test_friend_list_links_to_profile(self):
        self.client.force_login(self.user)
        Friendship.objects.create(from_user=self.other, to_user=self.user, accepted=True)
        resp = self.client.get('/friendship/')
        self.assertContains(resp, f'href="/profile/{self.other.username}/"')

    def test_chat_page_no_system_messages(self):
        self.client.force_login(self.user)
        # make a chat so view has messages
        Friendship.objects.create(from_user=self.other, to_user=self.user, accepted=True)
        # create chat and message
        chat = Chat.objects.create()
        chat.participants.add(self.user, self.other)
        Message.objects.create(chat=chat, sender=self.other, text='hi')
        resp = self.client.get(f'/chat/{self.other.username}')
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, 'Message<')

    def test_profile_edit_button_shows_form(self):
        self.client.force_login(self.user)
        resp = self.client.get(f'/profile/{self.user.username}/')
        self.assertContains(resp, 'id="toggle-edit"')
        self.assertContains(resp, 'id="edit-profile-form"')

    def test_add_subtask(self):
        # user creates a task and adds a subtask
        self.client.force_login(self.user)
        task = TaskList.objects.create(user=self.user, title='Test', date=timezone.now().date())
        resp = self.client.post(f'/tasks/{task.id}/add_subtask/', {'text': 'sub1'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.subtasks.count(), 1)
        self.assertEqual(task.subtasks.first().text, 'sub1')
