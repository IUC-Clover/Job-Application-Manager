from django.shortcuts import render
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import UserSerializer, ResumeSerializer
from .models import User, Resume
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser

# Imports for Email Verification
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.urls import reverse

# Create your views here.
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer

    def perform_create(self, serializer):
        user = serializer.save(is_active=False)
        
        # Send verification email
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        verification_link = self.request.build_absolute_uri(
            reverse('verify-email', kwargs={'uidb64': uid, 'token': token})
        )
        
        subject = 'Activate Your JobApp Account'
        message = f'Hi {user.username},\n\nPlease click the link to activate your account:\n{verification_link}'
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

class VerifyEmailView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return Response({'detail': 'Email successfully verified.'}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'Invalid verification link.'}, status=status.HTTP_400_BAD_REQUEST)

class ResumeView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        try:
            return self.request.user.resume
        except Resume.DoesNotExist:
            return None

    def get(self, request, *args, **kwargs):
        resume = self.get_object()
        if not resume:
            return Response({'detail': 'Resume not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ResumeSerializer(resume)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if self.get_object():
             return Response({'detail': 'You already have a resume. Use PUT to update.'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = ResumeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        resume = self.get_object()
        if not resume:
            return Response({'detail': 'Resume not found. Use POST to create one.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ResumeSerializer(resume, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        resume = self.get_object()
        if not resume:
            return Response({'detail': 'Resume not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        resume.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
