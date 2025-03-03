import secrets
import string
from functools import partial

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.urls import reverse

User: AbstractBaseUser = get_user_model()


PASSWORD_LENGTH = 10


def generate_random_password(length: int) -> str:
    charset = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(charset) for i in range(length))


def create_new_user(username: str, password: str = None):
    if not password or len(password) < PASSWORD_LENGTH:
        password = get_random_password()
    user = User.objects.create(username=username)
    user.set_password(password)
    user.save()
    return user


get_random_password = partial(generate_random_password, PASSWORD_LENGTH)


class RegisterUserViewTest(TestCase):
    REQUEST_PATH = reverse('users:register')

    @classmethod
    def setUpTestData(cls):
        cls.existing_user_pswd = get_random_password()
        cls.existing_user = create_new_user('ImUser', cls.existing_user_pswd)

    def setUp(self) -> None:
        self.client = Client()

    def test_userRegistrationSuccessful(self):
        pswd = get_random_password()
        resp = self.client.post(
            self.REQUEST_PATH, {'username': 'JohnDoe', 'password1': pswd, 'password2': pswd}
        )

        self.assertRedirects(resp, reverse('index'))
        self.assertIsNotNone(User.objects.get(username='JohnDoe'))

    def test_userRegistrationUnsuccessfulWhenUsernameExists(self):
        pswd = get_random_password()
        for username in (self.existing_user.get_username(), self.existing_user.get_username().lower()):
            with self.subTest(username=username):
                resp = self.client.post(
                    self.REQUEST_PATH, {'username': username, 'password1': pswd, 'password2': pswd}
                )

                self.assertEqual(resp.status_code, 200)
                self.assertEqual(User.objects.filter(username=self.existing_user.get_username()).count(), 1)

    def test_userRegistrationUnsuccessfulWhenPasswordsDontMatch(self):
        pswd1 = get_random_password()
        pswd2 = pswd1[-1::-1]

        resp = self.client.post(
            self.REQUEST_PATH, {'username': 'JohnDoe', 'password1': pswd1, 'password2': pswd2}
        )

        self.assertEqual(resp.status_code, 200)
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(username='JohnDoe')

    def test_userRegistrationUnsuccessfulWhenPasswordIsTooShort(self):
        pswd = generate_random_password(1)

        resp = self.client.post(
            self.REQUEST_PATH, {'username': 'JohnDoe', 'password1': pswd, 'password2': pswd}
        )

        self.assertEqual(resp.status_code, 200)
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(username='JohnDoe')

    def test_redirectIsSendWhenAuthorizedUserRequestsForRegister(self):
        self.client.login(username=self.existing_user.get_username(), password=self.existing_user_pswd)
        resp = self.client.get(self.REQUEST_PATH)

        self.assertRedirects(resp, '/')


class LoginUserViewTest(TestCase):
    REQUEST_PATH = reverse('users:login')

    @classmethod
    def setUpTestData(cls):
        cls.users_password = get_random_password()
        cls.user_to_log_in = create_new_user(username='JohnDoe', password=cls.users_password)

    def setUp(self) -> None:
        self.client = Client()

    def test_loginSuccessful(self):
        resp = self.client.post(
            self.REQUEST_PATH, {'username': self.user_to_log_in.get_username(), 'password': self.users_password}
        )

        self.assertRedirects(resp, '/')
        self.assertEqual(self.client.session.get('_auth_user_id'), str(self.user_to_log_in.id))

    def test_loginUnsuccessful(self):
        resp = self.client.post(
            self.REQUEST_PATH, {'username': self.user_to_log_in.get_username(), 'password': self.users_password[-1::-1]}
        )

        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(self.client.session.get('_auth_user_id'))


class LogoutUserViewTest(TestCase):
    REQUEST_PATH = reverse('users:logout')

    @classmethod
    def setUpTestData(cls):
        cls.users_password = get_random_password()
        cls.user_to_log_out = create_new_user(username='JohnDoe', password=cls.users_password)

    def setUp(self) -> None:
        self.client = Client()

    def test_logoutSuccessful(self):
        self.client.login(username=self.user_to_log_out.get_username(), password=self.users_password)

        self.client.post(self.REQUEST_PATH)
