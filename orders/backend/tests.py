from django.test import TestCase

from rest_framework import status

from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

from .models import User, ConfirmEmailToken
from .serializers import UserSerializer


class RegistrationTestCase(APITestCase):

    def test_registration(self):
        data = {'first_name': 'test_name', 'last_name': 'test_last_name',
                'email': 'test@email.test', 'password': 'test_passw',
                'company': 'test_company', 'position': 'test_position'}

        response = self.client.post('/user/register', data)
        self.assertEqual(response.json()['Status'], True)

        self.assertTrue(User.objects.filter(email='test@email.test'))

    def test_registration_bad_params(self):
        response = self.client.post('/user/register', {})
        self.assertEqual(response.json()['Status'], False)
        self.assertFalse(User.objects.all())


class EmailConfirmationTestCase(APITestCase):

    def setUp(self) -> None:
        data = {'first_name': 'test_name', 'last_name': 'test_last_name',
                'email': 'test@email.test', 'password': 'test_passw',
                'company': 'test_company', 'position': 'test_position'}
        user_serializer = UserSerializer(data=data)
        if user_serializer.is_valid():
            self.user = user_serializer.save()
            self.user.set_password(data['password'])
            self.user.save()
            self.token, _ = ConfirmEmailToken.objects.get_or_create(user_id=self.user.id)

    def test_account_confirm(self):
        data = {'email': self.user.email, 'token': self.token.key}
        response = self.client.post('/user/register/confirm', data)
        self.assertEqual(response.json()['Status'], True)
        self.assertTrue(User.objects.filter(id=self.user.id).first().is_active)

    def test_account_confirm_without_token(self):
        data = {'email': self.user.email}
        response = self.client.post('/user/register/confirm', data)
        self.assertEqual(response.json()['Status'], False)
        self.assertFalse(User.objects.filter(id=self.user.id).first().is_active)


class AccountDetailsTestCase(APITestCase):

    def setUp(self) -> None:
        data = {'first_name': 'test_name', 'last_name': 'test_last_name',
                'email': 'test@email.test', 'password': 'test_passw',
                'company': 'test_company', 'position': 'test_position'}
        user_serializer = UserSerializer(data=data)
        if user_serializer.is_valid():
            self.user = user_serializer.save()
            self.user.set_password(data['password'])
            self.user.is_active = True
            self.user.save()
            response = self.client.post('/user/login', {'email': self.user.email, 'password': data['password']})
            self.token = response.json()['Token']

    def test_get_account_details(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token}')
        response = self.client.get('/user/details')
        serializer = UserSerializer(self.user)
        self.assertEqual(response.json(), serializer.data)

    def test_get_account_details_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token 12345')
        response = self.client.get('/user/details')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_account_details(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token}')
        data = {'first_name': 'edited_test_name', 'last_name': 'edited_test_last_name',
                'email': 'edited_test@email.test', 'password': 'edited_test_passw',
                'company': 'edited_test_company', 'position': 'edited_test_position',
                'type': 'shop',
                }
        response = self.client.post('/user/details', data=data)

        edited_user = User.objects.filter(id=self.user.id).first()

        self.assertEqual(response.json()['Status'], True)
        self.assertEqual(edited_user.first_name, 'edited_test_name')
        self.assertEqual(edited_user.last_name, 'edited_test_last_name')
        self.assertEqual(edited_user.email, 'edited_test@email.test')
        self.assertTrue(edited_user.check_password('edited_test_passw'))
        self.assertEqual(edited_user.company, 'edited_test_company')
        self.assertEqual(edited_user.position, 'edited_test_position')
        self.assertEqual(edited_user.type, 'shop')

        if 'email' in data:
            self.assertFalse(edited_user.is_active)


class AccountLoginTestCase(APITestCase):

    def setUp(self) -> None:
        self.data = {'first_name': 'test_name', 'last_name': 'test_last_name',
                     'email': 'test@email.test', 'password': 'test_passw',
                     'company': 'test_company', 'position': 'test_position'}
        user_serializer = UserSerializer(data=self.data)
        if user_serializer.is_valid():
            self.user = user_serializer.save()
            self.user.set_password(self.data['password'])
            self.user.is_active = True
            self.user.save()

    def test_user_login(self):
        response = self.client.post('/user/login', {'email': self.user.email, 'password': self.data['password']})
        self.assertEqual(response.json()['Token'], Token.objects.filter(user=self.user).first().key)

    def test_user_login_bad_credentials(self):
        response = self.client.post('/user/login', {'email': 'kek', 'password': 'pass'})
        self.assertEqual(response.json()['Status'], False)
