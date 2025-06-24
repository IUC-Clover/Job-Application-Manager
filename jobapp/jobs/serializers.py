from rest_framework import serializers
from .models import Job, Application
from accounts.serializers import UserSerializer

class JobSerializer(serializers.ModelSerializer):
    employer = serializers.ReadOnlyField(source='employer.username')

    class Meta:
        model = Job
        fields = [
            'id', 'employer', 'title', 'company', 'description', 'category', 
            'location', 'salary', 'experience_level', 'status', 
            'created_at', 'updated_at'
        ]

class ApplicationSerializer(serializers.ModelSerializer):
    applicant = serializers.ReadOnlyField(source='applicant.username')

    class Meta:
        model = Application
        fields = '__all__' 