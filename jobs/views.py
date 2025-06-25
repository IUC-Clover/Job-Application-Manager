from django.shortcuts import render
from rest_framework import viewsets
from .models import Job, Application
from .serializers import JobSerializer, ApplicationSerializer
from .permissions import IsEmployerOrReadOnly, IsOwnerOrReadOnly, IsJobSeeker
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework import serializers

# Imports for Stats and Email
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count
from django.core.mail import send_mail
from django.conf import settings
from accounts.models import Notification

# Create your views here.
class JobViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows jobs to be viewed or edited.
    """
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsEmployerOrReadOnly, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(employer=self.request.user)

class ApplicationViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows applications to be viewed or edited.
    """
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'employer':
            return Application.objects.filter(job__employer=user)
        elif user.role == 'job_seeker':
            return Application.objects.filter(applicant=user)
        return Application.objects.none()

    def perform_create(self, serializer):
        job = serializer.validated_data.get('job')
        if Application.objects.filter(job=job, applicant=self.request.user).exists():
            raise serializers.ValidationError("You have already applied for this job.")
        
        application = serializer.save(applicant=self.request.user)
        
        # Send email notification to employer
        employer = application.job.employer
        subject = f'New Application for {application.job.title}'
        message = f'Hi {employer.username},\n\nYou have received a new application from {self.request.user.username} for the job "{application.job.title}".'
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [employer.email],
            fail_silently=True, # Do not crash if email fails
        )
        # Employer'a notification ekle
        Notification.objects.create(
            user=employer,
            message=f'You have received a new application from {self.request.user.username} for the job "{application.job.title}".'
        )

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [IsJobSeeker]
        return super().get_permissions()

class ApplicationStatsView(APIView):
    """
    Provides statistics on job applications for employers.
    """
    permission_classes = [IsAuthenticated] # We will add IsEmployer permission here later

    def get(self, request, *args, **kwargs):
        user = self.request.user
        if user.role != 'employer':
            return Response({"detail": "You do not have permission to perform this action."}, status=403)

        # Get stats for jobs posted by the current employer
        application_stats = Application.objects.filter(job__employer=user) \
            .values('status') \
            .annotate(count=Count('status')) \
            .order_by('status')
            
        return Response(list(application_stats))
