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

    def test_user_can_message_using_user_case_number(self):
        # Create user 1's case (PK id=1, user_case_number=1)
        self.auth_client(self.user)
        res1 = self.client.post('/api/cases/', {'title': 'User 1 Case', 'description': 'Help'}, format='json')
        case1_id = res1.data['id']

        # Create user 2
        user2 = User.objects.create_user(username='user2', password='password123', role='user')
        self.auth_client(user2)
        res2 = self.client.post('/api/cases/', {'title': 'User 2 Case', 'description': 'Help'}, format='json')
        case2_id = res2.data['id']
        case2_user_case_num = res2.data['user_case_number']
        self.assertEqual(case2_user_case_num, 1)  # Per-user case number is 1

        # User 2 sends message using 'case': 1 (which equals case1_id, but is user2's user_case_number)
        msg_res = self.client.post(
            '/api/messages/',
            {'case': case2_user_case_num, 'content': 'Hello from user2'},
            format='json'
        )
        self.assertEqual(msg_res.status_code, 201)
        # Verify the message was attached to user 2's case (case2_id), not case 1
        msg = Message.objects.get(id=msg_res.data['id'])
        self.assertEqual(msg.case.id, case2_id)
        self.assertEqual(msg.sender, user2)

    def test_single_active_case_enforcement(self):
        self.auth_client(self.user)
        # Create first case (open)
        res1 = self.client.post('/api/cases/', {'title': 'First Case', 'description': 'Need help'}, format='json')
        self.assertEqual(res1.status_code, 201)
        case1_id = res1.data['id']

        # Attempt to create second case while first is active -> must fail with 403
        res2 = self.client.post('/api/cases/', {'title': 'Second Case', 'description': 'Another help'}, format='json')
        self.assertEqual(res2.status_code, 403)

        # Close the first case
        close_res = self.client.post(f'/api/cases/{case1_id}/close/')
        self.assertEqual(close_res.status_code, 200)

        # Now creating a second case must succeed
        res3 = self.client.post('/api/cases/', {'title': 'Second Case', 'description': 'Another help'}, format='json')
        self.assertEqual(res3.status_code, 201)
        case2_id = res3.data['id']

        # Attempt to reopen first case while second case is active -> must fail with 400
        reopen_res = self.client.post(f'/api/cases/{case1_id}/reopen/')
        self.assertEqual(reopen_res.status_code, 400)
        self.assertIn('already have an active case', reopen_res.data['error'])


