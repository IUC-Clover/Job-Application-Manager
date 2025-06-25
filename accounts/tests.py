from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from accounts.models import User
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from accounts.forms import ProfileForm, ResumeForm
from accounts.models import Notification, Resume

# Create your tests here.

class UserRegistrationLoginE2ETest(APITestCase):
    def test_user_registration_and_login(self):
        # Kullanıcı kaydı
        url = reverse('register')
        data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'Testpass123!',
            'role': 'job_seeker'
        }
        response = self.client.post(url, data)
        if response.status_code == 302:
            print('Yönlendirme:', response['Location'])
            print('Yönlendirme response:', response.content)
        else:
            print('Kayıt response:', getattr(response, 'data', response.content))
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED, 302])

        # Kullanıcıyı aktif et (eğer değilse)
        user = User.objects.get(username='testuser')
        if not user.is_active:
            user.is_active = True
            user.save()

        # Kullanıcı giriş (JWT Token alma)
        url = reverse('token_obtain_pair')
        data = {
            'username': 'testuser',
            'password': 'Testpass123!'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

class ResumeViewE2ETest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='resumeuser', password='Testpass123!', role='job_seeker', is_active=True)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_resume_crud(self):
        # Başlangıçta GET 404
        response = self.client.get('/api/accounts/resume/')
        self.assertEqual(response.status_code, 404)
        # POST ile yükle
        import io
        from django.core.files.uploadedfile import SimpleUploadedFile
        file = SimpleUploadedFile('cv.pdf', b'PDFDATA', content_type='application/pdf')
        response = self.client.post('/api/accounts/resume/', {'file': file}, format='multipart')
        self.assertEqual(response.status_code, 201)
        # GET ile kontrol
        response = self.client.get('/api/accounts/resume/')
        self.assertEqual(response.status_code, 200)
        # PUT ile güncelle
        file2 = SimpleUploadedFile('cv2.pdf', b'PDFDATA2', content_type='application/pdf')
        response = self.client.put('/api/accounts/resume/', {'file': file2}, format='multipart')
        self.assertEqual(response.status_code, 200)
        # DELETE ile sil
        response = self.client.delete('/api/accounts/resume/')
        self.assertEqual(response.status_code, 204)

class VerifyEmailViewTest(APITestCase):
    def test_verify_email(self):
        user = User.objects.create_user(username='verifyuser', password='Testpass123!', email='verify@example.com', is_active=False)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        url = f'/api/accounts/verify-email/{uid}/{token}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.is_active)

class ProfileFormTest(TestCase):
    def test_valid_profile_form(self):
        data = {
            'username': 'formuser',
            'email': 'form@example.com',
            'first_name': 'Form',
            'last_name': 'User',
            'role': 'job_seeker',
            'location': '',
            'experience_level': '',
        }
        form = ProfileForm(data=data)
        self.assertTrue(form.is_valid())

class ResumeFormTest(TestCase):
    def test_resume_form(self):
        form = ResumeForm(data={})
        self.assertFalse(form.is_valid())

class UserModelTest(TestCase):
    def test_user_str(self):
        user = User(username='struser')
        self.assertEqual(str(user), 'struser')

class NotificationModelTest(TestCase):
    def test_notification_str(self):
        user = User.objects.create(username='notifuser')
        notif = Notification.objects.create(user=user, message='Test notification')
        self.assertIn('notifuser', str(notif))

class ResumeModelTest(TestCase):
    def test_resume_str(self):
        user = User.objects.create(username='resumeuser2')
        resume = Resume.objects.create(user=user, file='resumes/test.pdf')
        self.assertIn('resumeuser2', str(resume))
