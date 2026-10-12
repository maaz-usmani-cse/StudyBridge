from django.db import models

class Inquiry(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONTACTED', 'Contacted'),
        ('ENROLLED', 'Enrolled'),
        ('REJECTED', 'Rejected'),
    ]

    # Ye fields Form se aayengi
    student_name = models.CharField(max_length=100)
    parent_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    whatsapp_number = models.CharField(max_length=15)
    grade = models.CharField(max_length=50)
    school_name = models.CharField(max_length=150, blank=True, null=True)
    subjects = models.CharField(max_length=200)
    tuition_type = models.CharField(max_length=100)
    preferred_slot = models.CharField(max_length=50)
    address = models.TextField()
    remarks = models.TextField(blank=True, null=True)

    # Ye internal status tracker hai (Form me user ko nahi dikhega)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_name} - {self.grade} ({self.status})"

    class Meta:
        verbose_name_plural = "Inquiries"
        



        