from django.shortcuts import render, redirect
from django.contrib import messages
from core.models import Inquiry
from dashboard.models import Batch 


def landing_view(req):
   
    batches = Batch.objects.all().select_related('teacher')

    if req.method == "POST":
        student_name = req.POST.get('student_name', '').strip()
        parent_name = req.POST.get('parent_name', '').strip()
        phone_number = req.POST.get('phone_number', '').strip()
        whatsapp_number = req.POST.get('whatsapp_number', '').strip()
        grade = req.POST.get('grade', '').strip()
        school_name = req.POST.get('school_name', '').strip()
        subjects = req.POST.get('subjects', '').strip()
        tuition_type = req.POST.get('tuition_type', '').strip()
        preferred_slot = req.POST.get('preferred_slot', '').strip()
        address = req.POST.get('address', '').strip()
        remarks = req.POST.get('remarks', '').strip()

        if student_name and phone_number:
            Inquiry.objects.create(
                student_name=student_name,
                parent_name=parent_name,
                phone_number=phone_number,
                whatsapp_number=whatsapp_number,
                grade=grade,
                school_name=school_name,
                subjects=subjects,
                tuition_type=tuition_type,
                preferred_slot=preferred_slot,
                address=address,
                remarks=remarks
            )
            messages.success(req, 'Inquiry Successfully Ho chuki h! Hamari team aapse jald hi call karegi.')
            return redirect('landing')

    return render(req, 'core/landing.html', {'batches': batches})