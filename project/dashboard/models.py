from django.db import models
from app.models import UserProfile


class Batch(models.Model):
    batch_name = models.CharField(max_length=100)
    subject = models.CharField(max_length=100)   
    timing = models.CharField(max_length=100)     
    
   
    teacher = models.ForeignKey(
        UserProfile, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_batches', 
        limit_choices_to={'role': 'TEACHER'}
    )
    
   
    students = models.ManyToManyField(
        UserProfile, 
        blank=True, 
        related_name='enrolled_batches', 
        limit_choices_to={'role': 'STUDENT'}
    )

    def __str__(self):
        return f"{self.batch_name} ({self.timing})"



class StudyMaterial(models.Model):
    title = models.CharField(max_length=200)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='materials')
    pdf_file = models.FileField(upload_to='notes_pdfs/')
    uploaded_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, limit_choices_to={'role': 'TEACHER'})
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.batch.batch_name}"



class FeeRecord(models.Model):
    student = models.ForeignKey(
        UserProfile, 
        on_delete=models.CASCADE, 
        related_name='student_fees', 
        limit_choices_to={'role': 'STUDENT'}
    )
    amount = models.IntegerField()
    month = models.CharField(max_length=20) 
    is_paid = models.BooleanField(default=False)
    paid_date = models.DateField(null=True, blank=True)

    def __str__(self):
        status = "Paid" if self.is_paid else "Pending"
        return f"{self.student.full_name} - {self.month} ({status})"