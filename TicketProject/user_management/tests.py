from datetime import timedelta
from unittest.mock import patch

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Ticket
from .tasks import change_state
from TicketProject.routing import application


@override_settings(CHANNEL_LAYERS={
    'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'},
})
class AccountAndDashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.super_admin_group = Group.objects.get_or_create(name='super_admin')[0]
        cls.user = get_user_model().objects.create_user(
            username='dashboard_user',
            password='Local-Test-Password-9382',
            email='dashboard@example.invalid',
        )
        cls.user.groups.add(cls.super_admin_group)

    def test_public_pages_render(self):
        self.assertEqual(self.client.get(reverse('base')).status_code, 200)
        self.assertEqual(self.client.get(reverse('register')).status_code, 200)
        self.assertEqual(self.client.get(reverse('login_view')).status_code, 200)

    def test_registration_creates_user_and_redirects_to_project_login(self):
        response = self.client.post(reverse('register'), {
            'username': 'new_test_user',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'new-test@example.invalid',
            'phone': '+15550100123',
            'password': 'Local-Test-Password-9382',
            'password1': 'Local-Test-Password-9382',
            'designation': 'super_admin',
        })

        self.assertRedirects(response, reverse('login_view'), fetch_redirect_response=False)
        user = get_user_model().objects.get(username='new_test_user')
        self.assertTrue(user.groups.filter(name='super_admin').exists())

    def test_login_authenticates_user_and_opens_dashboard(self):
        response = self.client.post(reverse('login_view'), {
            'username': 'dashboard_user',
            'password': 'Local-Test-Password-9382',
        })

        self.assertRedirects(response, reverse('home'), fetch_redirect_response=False)
        with patch('user_management.views.change_state.apply_async'):
            dashboard = self.client.get(reverse('home'))
        self.assertEqual(dashboard.status_code, 200)
        self.assertContains(dashboard, 'Welcome back, dashboard_user.')

    def test_dashboard_requires_login_and_uses_project_login_url(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].startswith('/login/?next='))


@override_settings(CHANNEL_LAYERS={
    'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'},
})
class CeleryTaskTests(TestCase):
    def test_expired_open_tickets_are_cancelled_but_completed_tickets_stay_done(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        open_ticket = Ticket.objects.create(
            start_date=yesterday - timedelta(days=1),
            end_date=yesterday,
            subject='Expired open ticket',
        )
        done_ticket = Ticket.objects.create(
            start_date=yesterday - timedelta(days=1),
            end_date=yesterday,
            subject='Expired completed ticket',
            state=Ticket.DONE,
        )

        result = change_state.apply().get()

        self.assertEqual(result, 1)
        open_ticket.refresh_from_db()
        done_ticket.refresh_from_db()
        self.assertEqual(open_ticket.state, Ticket.CANCEL)
        self.assertEqual(done_ticket.state, Ticket.DONE)


@override_settings(CHANNEL_LAYERS={
    'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'},
})
class WebSocketNotificationTests(TestCase):
    def test_group_event_reaches_notification_consumer(self):
        async def exchange_notification():
            communicator = WebsocketCommunicator(application, '/notifications/')
            connected, _ = await communicator.connect()
            self.assertTrue(connected)
            await get_channel_layer().group_send('gossip', {
                'type': 'user.gossip',
                'event': 'New User',
                'username': 'notification_test_user',
            })
            message = await communicator.receive_json_from(timeout=1)
            await communicator.disconnect()
            return message

        message = async_to_sync(exchange_notification)()
        self.assertEqual(message['event'], 'New User')
        self.assertEqual(message['username'], 'notification_test_user')
