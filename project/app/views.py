import random
from django.contrib import messages  
from django.shortcuts import render, redirect
from django.utils import timezone
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Q  
from .models import UserProfile
from dashboard.models import Batch
import resend
import os


def is_password_strong(password):
    digit = any(i.isdigit() for i in password)
    symbol = any(not i.isalnum() for i in password)
    alphabet = any(i.isalpha() for i in password)
    
    if not (digit and symbol and alphabet):
        return False, "Password mein kam se kam ek digit, ek symbol, aur ek alphabet hona chahiye!"
    return True, ""

def signup_view(request):
    batches = Batch.objects.all()

    if request.method == "POST":
        full_name = request.POST.get('full_name', '').strip().title()
        username = request.POST.get('username', '').strip().lower()
        email = request.POST.get('email', '').strip().lower()
        mobile = request.POST.get('mobile', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        profile_pic = request.FILES.get('profile_pic')
        role = request.POST.get('role', 'STUDENT')
        batch_ids = request.POST.getlist('batch_ids')
        child_identifier = request.POST.get('child_identifier', '').strip()
        terms_accepted = request.POST.get('terms')

        # Helper context builder to preserve form inputs
        def get_err_ctx(msg):
            return {
                'error': msg,
                'batches': batches,
                'form_data': request.POST,
                'selected_batch_ids': batch_ids
            }

        if not all([full_name, username, email, mobile, password, confirm_password, role]):
            return render(request, 'signup.html', get_err_ctx('Bhai, saare fields bharna zaroori hai!'))

        if not terms_accepted:
            return render(request, 'signup.html', get_err_ctx('Bhai, aage badhne ke liye Terms & Service agree karna zaroori hai!'))

        if len(mobile) < 10 or not mobile.replace('+', '').replace(' ', '').isdigit():
            return render(request, 'signup.html', get_err_ctx('Bhai, valid mobile number enter karo!'))

        matched_child = None
        if role == 'PARENT':
            if not child_identifier:
                return render(request, 'signup.html', get_err_ctx('Parent registration ke liye bache ka Registered Mobile No ya Username daalna zaroori hai!'))

            matched_child = UserProfile.objects.filter(
                Q(username=child_identifier.lower()) | Q(mobile=child_identifier),
                role='STUDENT'
            ).first()

            if not matched_child:
                return render(request, 'signup.html', get_err_ctx(f'"{child_identifier}" se koi registered student nahi mila! Kripya sahi Mobile Number ya Username dalein.'))

        # Junk cleanup for unverified data on re-attempts
        UserProfile.objects.filter(email=email, is_verified=False).delete()
        UserProfile.objects.filter(username=username, is_verified=False).delete()
        UserProfile.objects.filter(mobile=mobile, is_verified=False).delete()

        if UserProfile.objects.filter(username=username, is_verified=True).exists():
            return render(request, 'signup.html', get_err_ctx('Bhai, ye username pehle se kisi ne le rakha hai!'))

        if UserProfile.objects.filter(email=email, is_verified=True).exists():
            return render(request, 'signup.html', get_err_ctx('Ye email pehle se register hai!'))

        if UserProfile.objects.filter(mobile=mobile, is_verified=True).exists():
            return render(request, 'signup.html', get_err_ctx('Bhai, ye mobile number pehle se use ho raha hai!'))

        if password != confirm_password:
            return render(request, 'signup.html', get_err_ctx('Dono password match nahi kar rahe!'))
            
        is_strong, msg = is_password_strong(password)
        if not is_strong:   
            return render(request, 'signup.html', get_err_ctx(msg))

        otp_code = str(random.randint(100000, 999999))
        
        try:
            with transaction.atomic():
                hashed_pw = make_password(password)
                new_user = UserProfile.objects.create(
                    full_name=full_name,
                    username=username,
                    role=role,
                    email=email,
                    mobile=mobile,
                    profile_pic=profile_pic,
                    password=hashed_pw,
                    otp=otp_code,
                    otp_created_at=timezone.now(),
                    is_verified=False,
                    child=matched_child if role == 'PARENT' else None
                )

                # Student hone par selected batch me add karo
                if role == 'STUDENT' and batch_ids:
                    selected_batches = Batch.objects.filter(id__in=batch_ids)
                    for batch_obj in selected_batches:
                        batch_obj.students.add(new_user)

                resend.api_key = os.environ.get('RESEND_API_KEY')

                resend.Emails.send({
                    "from": "Semester Registration <onboarding@resend.dev>",
                    "to": [email],
                    "subject": "Verify Your Account",
                    "text": "Bhai, aapka OTP hai: " + str(otp_code) + ". Ye sirf 5 minute tak valid hai.",
                })
                
                request.session['pre_verified_username'] = username
                return redirect('verify_otp')
                
        except Exception as e:
            return render(request, 'signup.html', get_err_ctx(f'Technical error! Data save ya email bhejne me dikkat aayi: {e}'))

    return render(request, 'signup.html', {'batches': batches})
# ==========================================
# 2. VERIFY OTP VIEW (Flow: Verify -> Redirect to Login)
# ==========================================
def verify_otp_view(request):
    username = request.session.get('pre_verified_username')
    
    # 1. EARLY RETURN: Session check layer
    if not username:
        return redirect('signup')

    if request.method == "POST":
        submitted_otp = request.POST.get('otp_code', '').strip()

        # 2. EARLY RETURN: Mandatory field check
        if not submitted_otp:
            return render(request, 'verify.html', {'error': 'Bhai, OTP daalna zaroori hai!'})

        profiles = UserProfile.objects.filter(username=username, is_verified=False)
        
        # 3. EARLY RETURN: Account existence check
        if not profiles.exists():
            return redirect('signup')

        profile = profiles.first()

        # 4. EARLY RETURN: 5-Minute Time validity check
        if not profile.is_otp_valid():
            return render(request, 'verify.html', {
                'error': 'Bhai, OTP ka 5-minute ka time khatam ho gaya! "Resend OTP" par click karo.'
            })

        # 5. EARLY RETURN: OTP Character matching check
        if profile.otp != submitted_otp:
            return render(request, 'verify.html', {'error': 'Galat OTP code daala hai bhai, sahi se check karo!'})

        # SUCCESS BLOCK: Agar saare checks pass ho gaye
        profile.is_verified = True
        profile.otp = None  
        profile.save()

        # Session data flush execution
        del request.session['pre_verified_username']
        
        return redirect('login')

    return render(request, 'verify.html')


# ==========================================
# 3. RESEND OTP VIEW (SIGNUP SYSTEM)
# ==========================================


def resend_otp_view(request):
    username = request.session.get('pre_verified_username')
    
    # 1. EARLY RETURN: Session check layer
    if not username:
        return redirect('signup')

    # 🚀 NEW LOOPHOLE PROTECTION: Agar koi direct URL access kare (GET request), 
    # toh use bina OTP generate kiye seedhe verify page par wapas bhaga do!
    if request.method != "POST":
        return redirect('verify_otp')

    profiles = UserProfile.objects.filter(username=username, is_verified=False)
    
    # 2. EARLY RETURN: Account existence layer
    if not profiles.exists():
        return redirect('signup')

    profile = profiles.first()
    
    # Core system execution block (Sirf POST request par hi trigger hoga)
    new_otp = str(random.randint(100000, 999999))
    profile.otp = new_otp
    profile.otp_created_at = timezone.now()
    profile.save()
    
    try:
        
                resend.api_key = os.environ.get('RESEND_API_KEY')

                resend.Emails.send({
                    "from": "Semester Registration <onboarding@resend.dev>",
                    "to": [profile.email],
                    "subject": "Verify Your Account",
                    "text": "Bhai, aapka OTP hai: " + str(new_otp) + ". Ye sirf 5 minute tak valid hai.",
                })
                
                request.session['pre_verified_username'] = username
                return redirect('verify_otp')
        
    except Exception:
        messages.error(request, 'Mail server error! Naya OTP nahi bhej paye.')
        return redirect('verify_otp')

# ==========================================
# 4. LOGIN VIEW (Flow: Login -> Redirect to Dashboard)
# ==========================================
def login_view(request):
    if request.method == 'POST':
        login_input = request.POST.get('login_input', '').strip().lower() 
        password_input = request.POST.get('password', '').strip()
        remember_me=request.POST.get('remember_me')

        # 1. Mandatory Input Gate
        if not all([login_input, password_input]):
            return render(request, 'login.html', {'error': 'Bhai, fields khali mat chodo!'})

        # Dual Matching Engine: Username ya Email dono se check karega
        profiles = UserProfile.objects.filter(Q(username=login_input) | Q(email=login_input))
        
        # 2. EARLY RETURN LAYER: Agar account exist nahi karta, toh turant bhaga do!
        if not profiles.exists():
            return render(request, 'login.html', {'error': 'Bhai, ye credentials registered nahi hain!'})
        
        # Agar yahan tak code aaya hai, iska matlab profile guaranteed exist karti hai
        profile = profiles.first()
        
        # 3. Cryptography Password Validation Check
        if not check_password(password_input, profile.password):
            return render(request, 'login.html', {'error': 'Password galat hai bhai!'})
            
        # 4. OTP Verification Gate
        if not profile.is_verified:
            request.session['pre_verified_username'] = profile.username
            # Redirect logic update standard ko manage karega (Verification state path rendering)
            return redirect('resend_otp', {'error': 'Bhai, account verified nahi hai! Pehle OTP verify karo.'})
            
        # 5. Successful Session Authentication Architecture Flow
        request.session['user_id'] = profile.id

        if remember_me:
            # Checkbox Checked -> Settings me configured lifetime expiry (Unlimited/Persistent)
            request.session.set_expiry(None)
        else:
            # Checkbox Unchecked -> Browser Band (`X`) Hote Hi Instantly Logout!
            request.session.set_expiry(0)
        return redirect('dashboard')

    return render(request, 'login.html')




# ==========================================
# 6. LOGOUT VIEW (Flow: Logout -> Redirect to Login)
# ==========================================
def logout_view(request):
    if 'user_id' in request.session:
        del request.session['user_id']
    return redirect('login')




# ==========================================
# 7. FORGOT PASSWORD VIEW (Flow: Forgot -> Redirect to Reset)
# ==========================================
# 1. FORGOT PASSWORD VIEW
def forgot_password_view(request):
    if request.method == "POST":
        email_input = request.POST.get('email', '').strip().lower()
        if not email_input:
            return render(request, 'forgot_password.html', {'error': 'Email bharna zaroori hai!'})
            
        profiles = UserProfile.objects.filter(email=email_input, is_verified=True)
        if not profiles.exists():
            return render(request, 'forgot_password.html', {'error': 'Email verified nahi hai!'})
            
        profile = profiles.first()
        reset_otp = str(random.randint(100000, 999999))
        profile.otp = reset_otp
        profile.otp_created_at = timezone.now()
        profile.save()
        
        try:
                resend.api_key = os.environ.get('RESEND_API_KEY')

                resend.Emails.send({
                    "from": "Semester Registration <onboarding@resend.dev>",
                    "to": [email_input],
                    "subject": "Verify Your Account",
                    "text": "Bhai, aapka OTP hai: " + str(reset_otp) + ". Ye sirf 5 minute tak valid hai.",
                })
                
                request.session['reset_email'] = email_input
                return redirect('reset')
        except Exception:
            return render(request, 'forgot_password.html', {'error': 'Mail send error.'})

    # GET Request par direct template render
    return render(request, 'forgot_password.html')







# 2. RESET PASSWORD VIEW
def reset_password_view(request):
    email = request.session.get('reset_email')
    if not email:
        return redirect('forgot')

    if request.method == "POST":
        submitted_otp = request.POST.get('otp_code', '').strip()
        new_password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if not all([submitted_otp, new_password, confirm_password]):
            return render(request, 'reset_password.html', {'error': 'Saare fields fill karo!'})

        if new_password != confirm_password:
            return render(request, 'reset_password.html', {'error': 'Passwords match nahi ho rahe!'})

        is_strong, msg = is_password_strong(new_password)
        if not is_strong:
            return render(request, 'reset_password.html', {'error': msg})

        profiles = UserProfile.objects.filter(email=email)
        if not profiles.exists():
            return redirect('forgot')

        profile = profiles.first()
        if not profile.is_otp_valid():
            return render(request, 'reset_password.html', {'error': 'OTP expire ho gaya hai!'})

        if profile.otp != submitted_otp:
            return render(request, 'reset_password.html', {'error': 'Galat OTP code hai.'})

        # Success Action
        profile.password = make_password(new_password)
        profile.otp = None
        profile.save()

        if 'reset_email' in request.session:
            del request.session['reset_email']

        messages.success(request, 'Password reset ho gaya! Ab login karein.')
        return redirect('login')

    # GET Request par direct template render
    return render(request, 'reset_password.html')





# ==========================================
# 8. RESEND FORGOT OTP VIEW (Flow: Resend -> Refresh Reset Page)
# ==========================================
# 3. RESEND FORGOT OTP VIEW (Pure Action - No HTML Page)
def resend_forgot_password_otp_view(request):
    email = request.session.get('reset_email')
    if not email:
        return redirect('forgot')

    # Action Guard: Direct GET walo ko wapas redirect karo
    if request.method != "POST":
        return redirect('reset')

    profiles = UserProfile.objects.filter(email=email, is_verified=True)
    if not profiles.exists():
        return redirect('forgot')

    profile = profiles.first()
    new_otp = str(random.randint(100000, 999999))
    profile.otp = new_otp
    profile.otp_created_at = timezone.now()
    profile.save()

    try:
                resend.api_key = os.environ.get('RESEND_API_KEY')

                resend.Emails.send({
                    "from": "Semester Registration <onboarding@resend.dev>",
                    "to": [email],
                    "subject": "Verify Your Account",
                    "text": "Bhai, aapka OTP hai: " + str(new_otp) + ". Ye sirf 5 minute tak valid hai.",
                })
                
                return redirect('reset')
    except Exception:
        messages.error(request, 'Mail server issue! OTP nahi gaya.')

    return redirect('reset')








def legal_policy_view(req):
    return render(req,'legal.html')



