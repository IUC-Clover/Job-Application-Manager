from django.shortcuts import render, redirect
from django.views.generic import TemplateView, View, DetailView
from jobs.models import Job, Application
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from accounts.models import User, Notification
from django import forms
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Count
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from jobs.forms import JobForm
from accounts.forms import ProfileForm, ResumeForm, CustomPasswordChangeForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from django.utils.dateparse import parse_datetime

# Registration form
class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'password']

class RegisterView(View):
    def get(self, request):
        form = RegisterForm()
        return render(request, 'register.html', {'form': form})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_active = False  # Email verification required
            user.save()

            # Doğrulama maili gönder
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            verification_link = request.build_absolute_uri(
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

            messages.success(request, 'Registration successful! Please check your email to verify your account.')
            return redirect('login')
        return render(request, 'register.html', {'form': form})

# Login form
class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class LoginView(View):
    def get(self, request):
        form = LoginForm()
        return render(request, 'login.html', {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    # Kullanıcı rolüne göre yönlendirme
                    if user.role == 'job_seeker':
                        return redirect('job-seeker-dashboard')
                    elif user.role == 'employer':
                        return redirect('employer-dashboard')
                    else:
                        return redirect('index')
                else:
                    messages.error(request, 'Please verify your email before logging in.')
            else:
                messages.error(request, 'Invalid username or password.')
        return render(request, 'login.html', {'form': form})

# Create your views here.
class IndexView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        jobs = Job.objects.filter(status='open').order_by('-created_at')
        category = self.request.GET.get('category')
        location = self.request.GET.get('location')
        experience_level = self.request.GET.get('experience_level')
        if category:
            jobs = jobs.filter(category__iexact=category)
        if location:
            jobs = jobs.filter(location__iexact=location)
        if experience_level:
            jobs = jobs.filter(experience_level__iexact=experience_level)
        context['jobs'] = jobs
        # Filtre seçenekleri için unique değerler
        context['categories'] = Job.objects.values_list('category', flat=True).distinct()
        context['locations'] = Job.objects.values_list('location', flat=True).distinct()
        context['experience_levels'] = Job.objects.values_list('experience_level', flat=True).distinct()
        # Seçili filtreler
        context['selected_category'] = category
        context['selected_location'] = location
        context['selected_experience_level'] = experience_level
        return context

class JobDetailView(View):
    def get(self, request, pk):
        job = Job.objects.get(pk=pk)
        application_exists = False
        if request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role == 'job_seeker':
            application_exists = Application.objects.filter(job=job, applicant=request.user).exists()
        return render(request, 'job_detail.html', {
            'job': job,
            'application_exists': application_exists
        })

    def post(self, request, pk):
        job = Job.objects.get(pk=pk)
        if not request.user.is_authenticated or not hasattr(request.user, 'role') or request.user.role != 'job_seeker':
            messages.error(request, 'You must be logged in as a job seeker to apply.')
            return redirect('login')
        # Check if already applied
        if Application.objects.filter(job=job, applicant=request.user).exists():
            messages.warning(request, 'You have already applied for this job.')
        else:
            Application.objects.create(job=job, applicant=request.user)
            # Employer'a notification ekle
            Notification.objects.create(
                user=job.employer,
                message=f'You have received a new application from {request.user.username} for the job "{job.title}".'
            )
            messages.success(request, 'Your application has been submitted!')
        return redirect('job-detail', pk=pk)

class EmployerDashboardView(View):
    def get(self, request):
        if not request.user.is_authenticated or not hasattr(request.user, 'role') or request.user.role != 'employer':
            messages.error(request, 'You must be logged in as an employer to access the dashboard.')
            return redirect('login')
        jobs = Job.objects.filter(employer=request.user)
        # Applications grouped by job
        job_applications = {job.id: job.applications.select_related('applicant').all() for job in jobs}
        # Application stats
        stats = (
            jobs
            .annotate(total_applications=Count('applications'))
            .values('title', 'total_applications')
        )
        # Status distribution for all applications
        status_dist = (
            jobs
            .values('applications__status')
            .annotate(count=Count('applications__status'))
        )
        return render(request, 'employer_dashboard.html', {
            'jobs': jobs,
            'job_applications': job_applications,
            'stats': stats,
            'status_dist': status_dist,
        })

class JobSeekerDashboardView(View):
    def get(self, request):
        if not request.user.is_authenticated or not hasattr(request.user, 'role') or request.user.role != 'job_seeker':
            messages.error(request, 'You must be logged in as a job seeker to access the dashboard.')
            return redirect('login')
        
        # Kullanıcının başvurularını al
        applications = Application.objects.filter(applicant=request.user).select_related('job').order_by('-submitted_at')
        
        # Başvuru durumlarına göre grupla
        application_stats = {
            'pending': applications.filter(status='pending').count(),
            'interview_scheduled': applications.filter(status='interview_scheduled').count(),
            'hired': applications.filter(status='hired').count(),
            'rejected': applications.filter(status='rejected').count(),
        }
        
        return render(request, 'job_seeker_dashboard.html', {
            'applications': applications,
            'application_stats': application_stats,
        })

def logout_view(request):
    logout(request)
    return redirect('index')

class JobCreateView(View):
    @method_decorator(login_required)
    def get(self, request):
        if not hasattr(request.user, 'role') or request.user.role != 'employer':
            messages.error(request, 'Only employers can post jobs.')
            return redirect('index')
        form = JobForm()
        return render(request, 'job_create.html', {'form': form})

    @method_decorator(login_required)
    def post(self, request):
        if not hasattr(request.user, 'role') or request.user.role != 'employer':
            messages.error(request, 'Only employers can post jobs.')
            return redirect('index')
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.employer = request.user
            job.save()
            messages.success(request, 'Job posted successfully!')
            messages.info(request, f'New job posted: {job.title}')
            return redirect('index')
        return render(request, 'job_create.html', {'form': form})

class ProfileView(View):
    @method_decorator(login_required)
    def get(self, request):
        form = ProfileForm(instance=request.user)
        resume_form = None
        if hasattr(request.user, 'resume'):
            resume_form = ResumeForm(instance=request.user.resume)
        else:
            resume_form = ResumeForm()
        password_form = CustomPasswordChangeForm(user=request.user)
        return render(request, 'profile.html', {'form': form, 'resume_form': resume_form, 'password_form': password_form})

    @method_decorator(login_required)
    def post(self, request):
        if 'resume_form_submit' in request.POST:
            resume_form = None
            if hasattr(request.user, 'resume'):
                resume_form = ResumeForm(request.POST, request.FILES, instance=request.user.resume)
            else:
                resume_form = ResumeForm(request.POST, request.FILES)
            form = ProfileForm(instance=request.user)
            password_form = CustomPasswordChangeForm(user=request.user)
            if resume_form.is_valid():
                resume = resume_form.save(commit=False)
                resume.user = request.user
                resume.save()
                messages.success(request, 'Resume uploaded successfully!')
            return render(request, 'profile.html', {'form': form, 'resume_form': resume_form, 'password_form': password_form})
        form = ProfileForm(request.POST, instance=request.user)
        resume_form = None
        password_form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        password_changed = False
        if 'file' in request.FILES:
            if hasattr(request.user, 'resume'):
                resume_form = ResumeForm(request.POST, request.FILES, instance=request.user.resume)
            else:
                resume_form = ResumeForm(request.POST, request.FILES)
            if resume_form.is_valid():
                resume = resume_form.save(commit=False)
                resume.user = request.user
                resume.save()
                messages.success(request, 'Resume uploaded successfully!')
        if form.is_valid():
            user_obj = form.save(commit=False)
            if not form.cleaned_data.get('role'):
                user_obj.role = request.user.role
            user_obj.save()
            messages.success(request, 'Profile updated successfully!')
        if password_form.is_valid() and password_form.cleaned_data.get('new_password1'):
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully!')
            return redirect('profile')
        return render(request, 'profile.html', {'form': form, 'resume_form': resume_form, 'password_form': password_form})

@csrf_exempt
@login_required
def update_application_status(request):
    if request.method == 'POST' and request.user.role == 'employer':
        app_id = request.POST.get('application_id')
        status = request.POST.get('status')
        try:
            application = Application.objects.get(id=app_id, job__employer=request.user)
            application.status = status
            application.save()
            # Bildirim: başvuru sahibine notification ekle
            Notification.objects.create(
                user=application.applicant,
                message=f'Your application for {application.job.title} is now: {application.get_status_display()}'
            )
            return JsonResponse({'success': True, 'message': 'Status updated.'})
        except Application.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Application not found.'})
    return JsonResponse({'success': False, 'message': 'Invalid request.'})

class NotificationsView(View):
    @method_decorator(login_required)
    def get(self, request):
        notifications = Notification.objects.filter(user=request.user).order_by('is_read', '-created_at')
        return render(request, 'notifications.html', {'notifications': notifications})

class SearchCandidatesView(View):
    @method_decorator(login_required)
    def get(self, request):
        if not hasattr(request.user, 'role') or request.user.role != 'employer':
            messages.error(request, 'Only employers can search candidates.')
            return redirect('index')
        experience_level = request.GET.get('experience_level')
        location = request.GET.get('location')
        candidates = User.objects.filter(role='job_seeker')
        if experience_level:
            candidates = candidates.filter(experience_level__iexact=experience_level)
        if location:
            candidates = candidates.filter(location__iexact=location)
        experience_levels = User.objects.filter(role='job_seeker').values_list('experience_level', flat=True).distinct()
        locations = User.objects.filter(role='job_seeker').values_list('location', flat=True).distinct()
        return render(request, 'search_candidates.html', {
            'candidates': candidates,
            'experience_levels': experience_levels,
            'locations': locations,
            'selected_experience_level': experience_level,
            'selected_location': location,
        })

class JobEditView(View):
    @method_decorator(login_required)
    def get(self, request, pk):
        job = Job.objects.get(pk=pk, employer=request.user)
        form = JobForm(instance=job)
        return render(request, 'job_edit.html', {'form': form, 'job': job})

    @method_decorator(login_required)
    def post(self, request, pk):
        job = Job.objects.get(pk=pk, employer=request.user)
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, 'Job updated successfully!')
            return redirect('employer-dashboard')
        return render(request, 'job_edit.html', {'form': form, 'job': job})

class JobDeleteView(View):
    @method_decorator(login_required)
    def post(self, request, pk):
        job = Job.objects.get(pk=pk, employer=request.user)
        job.delete()
        messages.success(request, 'Job deleted successfully!')
        return redirect('employer-dashboard')

class ApplicantProfileView(View):
    @method_decorator(login_required)
    def get(self, request, user_id):
        if not hasattr(request.user, 'role') or request.user.role != 'employer':
            messages.error(request, 'Only employers can view applicant profiles.')
            return redirect('index')
        applicant = User.objects.get(id=user_id, role='job_seeker')
        return render(request, 'applicant_profile.html', {'applicant': applicant})

@require_POST
@login_required
def schedule_interview(request, app_id):
    if not hasattr(request.user, 'role') or request.user.role != 'employer':
        return JsonResponse({'success': False, 'message': 'Permission denied.'})
    from jobs.models import Application
    try:
        app = Application.objects.get(id=app_id, job__employer=request.user)
        data = json.loads(request.body.decode())
        interview_date = data.get('interview_date')
        if interview_date:
            app.interview_date = parse_datetime(interview_date)
        app.status = 'interview_scheduled'
        app.save()
        # Bildirim: başvuru sahibine notification ekle
        Notification.objects.create(
            user=app.applicant,
            message=f'Your interview for {app.job.title} is scheduled for {app.interview_date.strftime('%d %b %Y %H:%M') if app.interview_date else 'TBD'}.'
        )
        return JsonResponse({'success': True, 'message': 'Interview scheduled!'})
    except Application.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Application not found.'})
