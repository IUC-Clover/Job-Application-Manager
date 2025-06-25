from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from accounts.models import User
from jobs.models import Job, Application

# Create your tests here.

class JobApplicationE2ETest(APITestCase):
    def setUp(self):
        self.employer = User.objects.create_user(username='employer', password='Testpass123!', role='employer')
        self.job_seeker = User.objects.create_user(username='seeker', password='Testpass123!', role='job_seeker')
        self.job = Job.objects.create(
            employer=self.employer,
            title='Test Job',
            description='Test Desc',
            category='IT',
            location='Remote',
            experience_level='Junior',
        )
    def test_job_application_flow(self):
        # Giriş yap
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {'username': 'seeker', 'password': 'Testpass123!'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        # İşe başvur
        url = reverse('application-list')
        response = self.client.post(url, {'job': self.job.id})
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK])

class JobViewSetE2ETest(APITestCase):
    def setUp(self):
        self.employer = User.objects.create_user(username='employer2', password='Testpass123!', role='employer', is_active=True)
        self.client = APIClient()
        self.client.force_authenticate(user=self.employer)

    def test_job_crud(self):
        # Create
        data = {'title': 'API Job', 'description': 'desc', 'category': 'IT', 'location': 'Remote', 'experience_level': 'Junior'}
        response = self.client.post('/api/jobs/', data)
        self.assertEqual(response.status_code, 201)
        job_id = response.data['id']
        # List
        response = self.client.get('/api/jobs/')
        self.assertEqual(response.status_code, 200)
        # Retrieve
        response = self.client.get(f'/api/jobs/{job_id}/')
        self.assertEqual(response.status_code, 200)
        # Update
        response = self.client.patch(f'/api/jobs/{job_id}/', {'title': 'Updated'}, format='json')
        self.assertEqual(response.status_code, 200)
        # Delete
        response = self.client.delete(f'/api/jobs/{job_id}/')
        self.assertEqual(response.status_code, 204)

class ApplicationViewSetE2ETest(APITestCase):
    def setUp(self):
        self.employer = User.objects.create_user(username='employer3', password='Testpass123!', role='employer', is_active=True)
        self.seeker = User.objects.create_user(username='seeker3', password='Testpass123!', role='job_seeker', is_active=True)
        self.job = Job.objects.create(employer=self.employer, title='JobX', description='desc', category='IT', location='Remote', experience_level='Junior')
        self.client = APIClient()
        self.client.force_authenticate(user=self.seeker)

    def test_application_create_and_list(self):
        # Başvuru oluştur
        response = self.client.post('/api/applications/', {'job': self.job.id})
        self.assertIn(response.status_code, [201, 200])
        # Listele (job_seeker)
        response = self.client.get('/api/applications/')
        self.assertEqual(response.status_code, 200)
        # Employer olarak listele
        self.client.force_authenticate(user=self.employer)
        response = self.client.get('/api/applications/')
        self.assertEqual(response.status_code, 200)

class ApplicationStatsViewTest(APITestCase):
    def setUp(self):
        self.employer = User.objects.create_user(username='employer4', password='Testpass123!', role='employer', is_active=True)
        self.seeker = User.objects.create_user(username='seeker4', password='Testpass123!', role='job_seeker', is_active=True)
        self.job = Job.objects.create(employer=self.employer, title='JobY', description='desc', category='IT', location='Remote', experience_level='Junior')
        Application.objects.create(job=self.job, applicant=self.seeker, status='pending')
        self.client = APIClient()
        self.client.force_authenticate(user=self.employer)

    def test_application_stats(self):
        response = self.client.get('/api/stats/')
        self.assertEqual(response.status_code, 200)
        # Beklenen anahtarlar: status ve count
        if isinstance(response.data, list) and response.data:
            self.assertIn('status', response.data[0])
            self.assertIn('count', response.data[0])
        elif isinstance(response.data, list):
            self.assertEqual(response.data, [])
        else:
            self.fail('Beklenmeyen response tipi: %s' % type(response.data))
