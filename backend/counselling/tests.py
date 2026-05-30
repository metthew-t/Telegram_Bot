from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, Case, Message

class CounsellingAPITestCase(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='ownerpass',
            role='owner',
        )
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass',
            role='admin',
        )
        self.user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='userpass',
            role='user',
        )
        self.client = APIClient()

    def auth_client(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_user_registration(self):
        response = self.client.post(
            '/api/users/',
            {
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password': 'strongpass123',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['username'], 'newuser')
        self.assertEqual(response.data['role'], 'admin')

    def test_login_returns_jwt(self):
        response = self.client.post(
            '/api/login/',
            {'username': 'user', 'password': 'userpass'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_owner_can_list_users(self):
        self.auth_client(self.owner)
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data) >= 3)

    def test_admin_cannot_list_users(self):
        self.auth_client(self.admin)
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, 403)

    def test_case_creation_and_assignment(self):
        self.auth_client(self.user)
        create_response = self.client.post(
            '/api/cases/',
            {'title': 'Need help', 'description': 'I need support.'},
            format='json',
        )
        self.assertEqual(create_response.status_code, 201)
        case_id = create_response.data['id']

        self.auth_client(self.admin)
        assign_response = self.client.post(
            f'/api/cases/{case_id}/assign/',
            {'admin_id': self.admin.id},
            format='json',
        )
        self.assertEqual(assign_response.status_code, 200)
        self.assertEqual(assign_response.data['status'], 'assigned')

    def test_message_create_permissions(self):
        self.auth_client(self.user)
        case = Case.objects.create(title='Test Case', description='Message test', user=self.user)
        response = self.client.post(
            '/api/messages/',
            {'case': case.id, 'content': 'Hello there.'},
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['content'], 'Hello there.')
        self.assertEqual(response.data['sender']['label'], 'You')

    def test_telegram_login_registers_user(self):
        response = self.client.post(
            '/api/telegram-login/',
            {'telegram_id': '1234567890', 'username': 'telegram_user'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertEqual(response.data['user']['username'], 'telegram_user')
        # telegram_id is hidden for non-owner users in the serializer
        self.assertNotIn('telegram_id', response.data['user'])

    def test_profile_endpoint(self):
        self.auth_client(self.user)
        response = self.client.get('/api/profile/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'user')

    def test_staff_notification_on_case_creation(self):
        from unittest.mock import patch
        # Set telegram_id for owner to receive notification
        self.owner.telegram_id = '999999999'
        self.owner.save()
        
        self.auth_client(self.user)
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            response = self.client.post(
                '/api/cases/',
                {'title': 'Help me', 'description': 'Need urgent support'},
                format='json'
            )
            self.assertEqual(response.status_code, 201)
            # Verify that requests.post was called to send Telegram notification
            self.assertTrue(mock_post.called)
            # Check if it was called with owner's telegram_id
            args, kwargs = mock_post.call_args
            self.assertEqual(kwargs['json']['chat_id'], '999999999')
            self.assertIn('New Case Created', kwargs['json']['text'])
