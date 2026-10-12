from django.contrib import admin
from .models import Inquiry

@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'grade', 'phone_number', 'tuition_type', 'status', 'created_at')
    list_filter = ('status', 'grade', 'tuition_type')
    search_fields = ('student_name', 'parent_name', 'phone_number')