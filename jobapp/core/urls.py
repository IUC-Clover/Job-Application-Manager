from django.urls import path
from .views import IndexView, RegisterView, LoginView, JobDetailView, EmployerDashboardView, logout_view, JobSeekerDashboardView, JobCreateView, ProfileView, update_application_status, NotificationsView, SearchCandidatesView, JobEditView, JobDeleteView, ApplicantProfileView, schedule_interview

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('jobs/<int:pk>/', JobDetailView.as_view(), name='job-detail'),
    path('employer/dashboard/', EmployerDashboardView.as_view(), name='employer-dashboard'),
    path('job-seeker/dashboard/', JobSeekerDashboardView.as_view(), name='job-seeker-dashboard'),
    path('jobs/create/', JobCreateView.as_view(), name='job-create'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('applications/update-status/', update_application_status, name='update-application-status'),
    path('notifications/', NotificationsView.as_view(), name='notifications'),
    path('candidates/search/', SearchCandidatesView.as_view(), name='search-candidates'),
    path('logout/', logout_view, name='logout'),
    path('jobs/<int:pk>/edit/', JobEditView.as_view(), name='job-edit'),
    path('jobs/<int:pk>/delete/', JobDeleteView.as_view(), name='job-delete'),
    path('applicant/<int:user_id>/profile/', ApplicantProfileView.as_view(), name='applicant-profile'),
    path('applications/<int:app_id>/schedule-interview/', schedule_interview, name='schedule-interview'),
] 