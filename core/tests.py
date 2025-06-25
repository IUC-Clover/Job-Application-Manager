from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from jobs.models import Job

# Create your tests here.

class CoreViewsSmokeTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.employer = User.objects.create_user(username='employer', password='Testpass123!', role='employer', is_active=True)
        self.seeker = User.objects.create_user(username='seeker', password='Testpass123!', role='job_seeker', is_active=True)
        self.job = Job.objects.create(employer=self.employer, title='Test Job', description='desc', category='IT', location='Remote', experience_level='Junior')

    def test_index_view(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

    def test_job_detail_view(self):
        response = self.client.get(reverse('job-detail', args=[self.job.id]))
        self.assertEqual(response.status_code, 200)

    def test_register_view_get(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_login_view_get(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_employer_dashboard_view(self):
        self.client.login(username='employer', password='Testpass123!')
        response = self.client.get(reverse('employer-dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_job_seeker_dashboard_view(self):
        self.client.login(username='seeker', password='Testpass123!')
        response = self.client.get(reverse('job-seeker-dashboard'))
        self.assertEqual(response.status_code, 200)
