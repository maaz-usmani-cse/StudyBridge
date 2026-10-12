from django.shortcuts import render, redirect
from app.models import UserProfile
from core.models import Inquiry
from .models import Batch, StudyMaterial, FeeRecord
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password

def get_logged_user(request):
    user_id=request.session.get('user_id')
    if not user_id:
        return None
    return UserProfile.objects.filter(id=user_id).first()





def dashboard_view(request):
    user_profile=get_logged_user(request)
    if not user_profile:
        return redirect('login')
    

    if user_profile.role=='TEACHER':
        return redirect('teacher_dashboard')


    elif user_profile.role=='OWNER':
        return redirect('owner_dashboard')
    

    elif user_profile.role=='STUDENT':
        return redirect('student_dashboard')


    elif user_profile.role=='PARENT':
        return redirect('parent_dashboard')





def teacher_dashboard_view(request):
    user_profile=get_logged_user(request)
    if not user_profile or user_profile.role!='TEACHER':
        return redirect ('login')


    if request.method == 'POST' and 'upload_note' in request.POST:
        title = request.POST.get('title')
        batch_id = request.POST.get('batch')
        pdf_file = request.FILES.get('pdf_file')

        if title and batch_id and pdf_file:
            batch_obj = Batch.objects.filter(id=batch_id).first()
            if batch_obj:
                StudyMaterial.objects.create(
                    title=title,
                    batch=batch_obj,
                    pdf_file=pdf_file,
                    uploaded_by=user_profile
                )
                return redirect('teacher_dashboard')

  
    if request.method == 'POST' and 'delete_note_id' in request.POST:
        note_id = request.POST.get('delete_note_id')
        note = StudyMaterial.objects.filter(id=note_id, uploaded_by=user_profile).first()
        if note:
            note.pdf_file.delete()  
            note.delete()         
            return redirect('teacher_dashboard')

    
    my_batches = Batch.objects.filter(teacher=user_profile)
    my_notes = StudyMaterial.objects.filter(uploaded_by=user_profile).order_by('-created_at')

    context = {
        'user_profile': user_profile,
        'my_batches': my_batches,
        'my_notes': my_notes,
        'total_batches': my_batches.count(),
        'total_notes': my_notes.count(),
    }
    return render(request, 'dashboard/teacher_dashboard.html', context)
    



 







def student_dashboard_view(request):
    user_profile=get_logged_user(request)
    if not user_profile or user_profile.role!='STUDENT':
        return redirect('login')

   
    my_batches = user_profile.enrolled_batches.all().select_related('teacher')

    
    if my_batches.exists():
        notes = StudyMaterial.objects.filter(batch__in=my_batches).select_related('batch', 'uploaded_by').order_by('-created_at')
    else:
        notes = StudyMaterial.objects.none()

    context = {
        'user_profile': user_profile,
        'my_batches': my_batches,
        'notes': notes,
        'total_batches': my_batches.count(),
        'total_notes': notes.count(),
    }
    return render(request, 'dashboard/student_dashboard.html', context)
  






def parent_dashboard_view(request):
    user_profile = get_logged_user(request)
    if not user_profile or user_profile.role != 'PARENT':
        return redirect('login')

    child = user_profile.child
    child_batches = []
    fee_records = []
    total_fee_due = 0

    if child:
        
        child_batches = child.enrolled_batches.all().select_related('teacher')
       
        fee_records = FeeRecord.objects.filter(student=child).order_by('-id')
        
    
        pending_records = fee_records.filter(is_paid=False)
        total_fee_due = sum(item.amount for item in pending_records)

    context = {
        'user_profile': user_profile,
        'child': child,
        'child_batches': child_batches,
        'fee_records': fee_records,
        'total_fee_due': total_fee_due,
        'total_batches': len(child_batches) if child else 0,
    }
    return render(request, 'dashboard/parent_dashboard.html', context)








def owner_dashboard_view(request):
    user_profile = get_logged_user(request)
    if not user_profile or user_profile.role != 'OWNER':
        return redirect('login')

    # ACTION 1: Existing Student/User ko Teacher Banana (Role Switch)
    if request.method == 'POST' and 'promote_to_teacher' in request.POST:
        target_user_id = request.POST.get('target_user_id')
        target_user = UserProfile.objects.filter(id=target_user_id).first()
        if target_user:
            target_user.role = 'TEACHER'
            target_user.save()
            return redirect('owner_dashboard')

    # ACTION 2: Naya Faculty Teacher Direct Create Karna
    if request.method == 'POST' and 'create_teacher' in request.POST:
        t_name = request.POST.get('teacher_name', '').strip().title()
        t_username = request.POST.get('teacher_username', '').strip().lower()
        t_email = request.POST.get('teacher_email', '').strip().lower()
        t_mobile = request.POST.get('teacher_mobile', '').strip()
        t_password = request.POST.get('teacher_password', '').strip()

        if t_name and t_username and t_password and t_mobile:
            if not UserProfile.objects.filter(username=t_username).exists():
                UserProfile.objects.create(
                    full_name=t_name,
                    username=t_username,
                    email=t_email if t_email else f"{t_username}@studybridge.internal",
                    mobile=t_mobile,
                    password=make_password(t_password),
                    role='TEACHER',
                    is_verified=True
                )
                return redirect('owner_dashboard')

    # ACTION 3: Naya Batch Create Karna
    if request.method == 'POST' and 'create_batch' in request.POST:
        batch_name = request.POST.get('batch_name', '').strip()
        subject = request.POST.get('subject', '').strip()
        timing = request.POST.get('timing', '').strip()
        teacher_id = request.POST.get('teacher')

        if batch_name and subject and timing:
            teacher_obj = UserProfile.objects.filter(id=teacher_id, role='TEACHER').first() if teacher_id else None
            Batch.objects.create(
                batch_name=batch_name,
                subject=subject,
                timing=timing,
                teacher=teacher_obj
            )
            return redirect('owner_dashboard')

    # ACTION 4: Quick Fee Record Add Karna
    if request.method == 'POST' and 'add_fee_record' in request.POST:
        student_id = request.POST.get('student_id')
        month = request.POST.get('month', '').strip()
        amount = request.POST.get('amount', '').strip()
        is_paid = request.POST.get('is_paid') == 'on'

        if student_id and amount:
            student_obj = UserProfile.objects.filter(id=student_id, role='STUDENT').first()
            if student_obj:
                FeeRecord.objects.create(
                    student=student_obj,
                    month=month if month else 'Current Month',
                    amount=amount,
                    is_paid=is_paid,
                    paid_date=timezone.now().date() if is_paid else None
                )
                return redirect('owner_dashboard')

    # --- NEW ACTION 5: Direct Inquiry se Student Banana & Batch Assign Karna ---
    if request.method == 'POST' and 'enroll_inquiry' in request.POST:
        inquiry_id = request.POST.get('inquiry_id')
        selected_batch_id = request.POST.get('batch_id')
        inquiry_obj = Inquiry.objects.filter(id=inquiry_id).first()

        if inquiry_obj and selected_batch_id:
            batch_obj = Batch.objects.filter(id=selected_batch_id).first()
            if batch_obj:
                # Check agar student pehle se exists karta hai (by mobile number)
                student_user = UserProfile.objects.filter(mobile=inquiry_obj.phone_number, role='STUDENT').first()

                if not student_user:
                    # Naya username auto generate (e.g. rahul1234)
                    base_username = inquiry_obj.student_name.lower().replace(" ", "")
                    unique_username = f"{base_username}_{inquiry_obj.phone_number[-4:]}"
                    # Default password set to mobile number (User baad me change kar sakta hai)
                    default_pw = make_password(inquiry_obj.phone_number)

                    student_user = UserProfile.objects.create(
                        full_name=inquiry_obj.student_name,
                        username=unique_username,
                        mobile=inquiry_obj.phone_number,
                        email=f"{unique_username}@studybridge.internal",
                        password=default_pw,
                        role='STUDENT',
                        is_verified=True
                    )

                # Batch me student add karo
                batch_obj.students.add(student_user)

                # Inquiry status ENROLLED mark karo
                inquiry_obj.status = 'ENROLLED'
                inquiry_obj.save()

                return redirect('owner_dashboard')

    # --- NEW ACTION 6: Quick Inquiry Status Change (Pending / Contacted / Rejected) ---
    if request.method == 'POST' and 'update_inquiry_status' in request.POST:
        inquiry_id = request.POST.get('inquiry_id')
        new_status = request.POST.get('status')
        if inquiry_id and new_status:
            Inquiry.objects.filter(id=inquiry_id).update(status=new_status)
            return redirect('owner_dashboard')

    # Data Fetching
    total_students = UserProfile.objects.filter(role='STUDENT', is_verified=True).count()
    total_teachers = UserProfile.objects.filter(role='TEACHER', is_verified=True).count()
    all_batches = Batch.objects.all().select_related('teacher').prefetch_related('students')
    all_teachers = UserProfile.objects.filter(role='TEACHER', is_verified=True).order_by('-id')
    all_students = UserProfile.objects.filter(role='STUDENT', is_verified=True).order_by('-id')
    
    try:
        recent_inquiries = Inquiry.objects.all().order_by('-created_at')[:12]
    except Exception:
        recent_inquiries = []

    recent_fee_records = FeeRecord.objects.all().select_related('student').order_by('-id')[:8]

    context = {
        'user_profile': user_profile,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_batches': all_batches.count(),
        'all_batches': all_batches,
        'all_teachers': all_teachers,
        'all_students': all_students,
        'recent_inquiries': recent_inquiries,
        'recent_fee_records': recent_fee_records,
    }
    return render(request, 'dashboard/owner_dashboard.html', context)