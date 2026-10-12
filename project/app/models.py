
from django.db import models
from django.utils import timezone
from datetime import timedelta

class UserProfile(models.Model):

    ROLE_CHOICES = [
        ('OWNER', 'Owner / Center Head (Di)'),
        ('TEACHER', 'Faculty Teacher'),
        ('STUDENT', 'Student'),
        ('PARENT', 'Parent'),
    ]
   
    full_name = models.CharField(max_length=100)
    username = models.CharField(max_length=50, unique=True, default='') 
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15, default='') 
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    
   
    password = models.CharField(max_length=255) 
    
   
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    is_verified = models.BooleanField(default=False) 

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT')

    child = models.ForeignKey(
    'self', 
    on_delete=models.SET_NULL, 
    null=True, 
    blank=True, 
    related_name='parents', 
    limit_choices_to={'role': 'STUDENT'}
)


    
    def is_otp_valid(self):
        if self.otp_created_at:
            return timezone.now() < self.otp_created_at + timedelta(minutes=5)
        return False

    def __str__(self):
        return f"{self.full_name} (@{self.username} - {self.role})"

    class Meta:
        verbose_name_plural = "User Profiles"