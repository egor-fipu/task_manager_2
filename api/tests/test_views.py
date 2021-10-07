from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from task.models import User, Task


class AuthTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.data = {
            'username': 'test_user',
            'password': 'test_password',
            'full_name': 'Test Testov'
        }
        cls.create_user_url = '/api/v1/auth/'
        cls.get_token_url = '/api/v1/auth/token/'

    def test_create_account(self):
        response = self.client.post(
            self.create_user_url,
            self.data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertTrue(
            User.objects.filter(
                username=self.data['username'],
                full_name=self.data['full_name']
            ).exists()
        )
        self.assertEqual(response.data.get('username'), self.data['username'])
        self.assertEqual(
            response.data.get('full_name'), self.data['full_name']
        )

        response = self.client.post(
            self.create_user_url,
            self.data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(
            response.data.get('username'),
            ['A user with that username already exists.']
        )

        empty_data = {
            'username': '',
            'password': '',
            'full_name': ''
        }
        response = self.client.post(
            self.create_user_url,
            empty_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        json = response.json()
        for field, message in json.items():
            with self.subTest(field):
                self.assertEqual(message, ['This field may not be blank.'])

        empty_data = {}
        response = self.client.post(
            self.create_user_url, empty_data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        json = response.json()
        for field, message in json.items():
            with self.subTest(field):
                self.assertEqual(message, ['This field is required.'])

    def test_get_token(self):
        self.client.post(self.create_user_url, self.data, format='json')
        response = self.client.post(
            self.get_token_url,
            {
                'username': self.data['username'],
                'password': self.data['password'],
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('token' in response.json())

        invalid_data = {
            'username': 'invalid_username',
            'password': 'test_password'
        }
        response = self.client.post(
            self.get_token_url, invalid_data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data.get('detail'), 'Not found.')

        invalid_data = {
            'username': self.data['username'],
            'password': 'invalid_password'
        }
        response = self.client.post(
            self.get_token_url, invalid_data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('password'), 'Неверный пароль')


class TasksTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tasks_url = '/api/v1/tasks/'
        cls.my_tasks_url = '/api/v1/tasks/my/'
        cls.user_1 = User.objects.create(
            username='test_user_1',
        )
        cls.user_2 = User.objects.create(
            username='test_user_2'
        )
        cls.task_1 = Task.objects.create(
            author=cls.user_1,
            title='Название задачи 1-го юзера',
            description='Описание задачи 1-го юзера',
            finished='2022-09-13',
        )
        cls.task_1.performers.set([cls.user_2])
        cls.task_2 = Task.objects.create(
            author=cls.user_2,
            title='Название задачи 2-го юзера',
            description='Описание задачи 2-го юзера',
            finished='2023-10-05',
        )
        cls.task_2.performers.set([cls.user_1, cls.user_2])

    def setUp(self):
        refresh = RefreshToken.for_user(self.user_1)
        token = str(refresh.access_token)
        self.authorized_client = APIClient()
        self.authorized_client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )

    def test_get_tasks_my_list_retrieve(self):
        subtests_tuple = (
            (self.tasks_url, 'get all tasks list'),
            (f'{self.tasks_url}my/', 'get my tasks list'),
        )
        for address, subtest_description in subtests_tuple:
            with self.subTest(subtest_description):
                response = self.authorized_client.get(address)
                json = response.json()
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertTrue('count' in json)
                self.assertEqual(json.get('next'), None)
                self.assertEqual(json.get('previous'), None)
                results = json.get('results')
                self.assertEqual(type(results), list)

        response = self.authorized_client.get(self.tasks_url)
        json = response.json()
        task_1 = json.get('results')[1]
        response = self.authorized_client.get(f'{self.my_tasks_url}')
        json = response.json()
        task_2 = json.get('results')[0]
        response = self.authorized_client.get(
            f'{self.tasks_url}{self.task_1.id}/'
        )
        task_3 = response.json()

        subtests_tuple = (
            (task_1, 'task in results all tasks list'),
            (task_2, 'task in results my tasks list'),
            (task_3, 'task in get task by id'),
        )
        for task, subtest_description in subtests_tuple:
            with self.subTest(subtest_description):
                self.assertEqual(task['id'], self.task_1.id)
                self.assertEqual(task['author'], self.task_1.author.username)
                self.assertEqual(task['title'], self.task_1.title)
                self.assertEqual(task['description'], self.task_1.description)
                self.assertEqual(task['finished'], self.task_1.finished)
                self.assertEqual(task['file'], self.task_1.file)
                self.assertEqual(
                    task['performers'],
                    [self.user_2.username]
                )

    def test_post_task(self):
        task_count = Task.objects.count()
        data = {
            'title': 'Тестовая задача',
            'performers': [self.user_2.username],
            'description': 'Описание тестовой задачи',
            'finished': '2022-08-05'
        }
        response = self.authorized_client.post(self.tasks_url, data)
        task = response.json()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), task_count + 1)
        self.assertTrue(
            Task.objects.filter(
                id=task['id'],
                author=self.user_1,
                title=data['title'],
                description=data['description'],
                finished=data['finished'],
            ).exists()
        )
        self.assertEqual(task['author'], self.user_1.username)
        self.assertEqual(task['title'], data['title'])
        self.assertEqual(task['description'], data['description'])
        self.assertEqual(task['finished'], data['finished'])
        self.assertEqual(task['performers'], data['performers'])

        empty_data = {}
        response = self.authorized_client.post(self.tasks_url, empty_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        json = response.json()
        for field, message in json.items():
            with self.subTest(field):
                self.assertEqual(message, ['This field is required.'])

        invalid_data = {
            'title': '',
            'performers': ['invalid_username'],
            'description': '',
            'finished': ''
        }
        response = self.authorized_client.post(self.tasks_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        json = response.json()
        self.assertEqual(
            json['performers'],
            [f'Object with username={invalid_data["performers"][0]} '
             f'does not exist.']
        )
        self.assertEqual(json['title'], ['This field may not be blank.'])
        self.assertEqual(json['description'], ['This field may not be blank.'])
        self.assertEqual(
            json['finished'],
            ['Date has wrong format. Use one of '
             'these formats instead: YYYY-MM-DD.']
        )

    def test_patch_task(self):
        data = {
            'title': 'Измененная задача',
            'performers': [self.user_1.username],
            'description': 'Описание измененной задачи',
            'finished': '2023-09-06'
        }
        response = self.authorized_client.patch(
            f'{self.tasks_url}{self.task_1.id}/', data
        )
        task = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(task['id'], self.task_1.id)
        self.assertEqual(task['author'], self.task_1.author.username)
        self.assertEqual(task['title'], data['title'])
        self.assertEqual(task['description'], data['description'])
        self.assertEqual(task['finished'], data['finished'])
        self.assertEqual(task['performers'], data['performers'])

    def test_delete_task(self):
        response = self.authorized_client.delete(
            path=f'{self.tasks_url}{self.task_1.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Task.objects.filter(id=self.task_1.id).exists()
        )

    def test_permissions(self):
        subtests_tuple = (
            (self.tasks_url, 'unauthorized get tasks list'),
            (self.my_tasks_url, 'unauthorized get my tasks list'),
            (
                f'{self.tasks_url}{self.task_1.id}/',
                'unauthorized get task by id'
            ),
        )
        for address, subtest_description in subtests_tuple:
            with self.subTest(subtest_description):
                response = self.client.get(address)
                self.assertEqual(
                    response.status_code, status.HTTP_401_UNAUTHORIZED
                )

        response = self.authorized_client.delete(
            f'{self.tasks_url}{self.task_2.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.authorized_client.patch(
            f'{self.tasks_url}{self.task_2.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
