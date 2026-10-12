from django.contrib import admin
from .models import Batch, StudyMaterial, FeeRecord

admin.site.register(Batch)
admin.site.register(StudyMaterial)
admin.site.register(FeeRecord)