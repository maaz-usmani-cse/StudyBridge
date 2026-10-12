from django.urls import path
from . import views

urlpatterns=[
    path('signup/',views.signup_view,name='signup'),
    path('legal_policy/',views.legal_policy_view,name='legal_policy'),
    path('verify_otp/',views.verify_otp_view,name='verify_otp'),
    path('resend_otp/',views.resend_otp_view,name='resend_otp'),
    path('login/',views.login_view,name='login'),
    path('logout/',views.logout_view,name='logout'),
    path('forgot/',views.forgot_password_view,name='forgot'),
    path('reset',views.reset_password_view,name='reset'),
    path('resend_forgot_otp/',views. resend_forgot_password_otp_view,name='resend_forgot_otp')

]