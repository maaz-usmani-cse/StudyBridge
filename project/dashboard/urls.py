from django.urls import path
from . import views

urlpatterns=[
    path('dashboard/',views.dashboard_view,name='dashboard'),
    path('teacher_dashboard/',views.teacher_dashboard_view,name='teacher_dashboard'),
    path('owner_dashboard/',views.owner_dashboard_view,name='owner_dashboard'),
    path('student_dashboard/',views.student_dashboard_view,name='student_dashboard'),
    path('parent_dashboard/',views.parent_dashboard_view,name='parent_dashboard')



]