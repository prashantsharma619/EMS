from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import authenticate, login
from .models import User
from django.contrib import messages
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from .forms import PasswordResetRequestForm, PasswordResetConfirmForm
from .models import PasswordResetToken

# Create your views here.
def login_view(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        device_id = request.POST.get('device_id')
        device_type = request.POST.get('device_type')
        app_info = request.POST.get('app_info')

        user = authenticate(request, email=email, password=password)
        if user is not None:
            # Ensure the user is an instance of your User model
            if isinstance(user, User):
                if user.is_superuser:
                    login(request, user)
                    return redirect('/admin-dashboard/')
                elif user.role == User.Role.INSTITUTE_OWNER.value:
                    login(request, user)
                    return redirect('/employee-dashboard/')
                else:
                    messages.info(
                        request,
                        'You do not have permission to access the admin dashboard.'
                    )
            else:
                messages.info(request, 'Invalid user type.')

        else:
            messages.info(request, 'Invalid email or password. Please try again.')

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    return render(request, 'authentication/admin_login.html')

def admin_dashboard(request):
    return render(request, "authentication/employee_dashboard.html")


def forgot_password(request):
    if request.method == "POST":
        form =PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                token_obj = PasswordResetToken.create_token(user)

                reset_url = request.build_absolute_uri(
                    reverse('accounts:password_reset_confirm',
                          kwargs={'token': token_obj.token})
                )
                send_mail(
                    subject='Password Reset Request',
                    message=f'Click this link to reset your password: {reset_url}\n\n',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                return redirect('accounts:password_reset_sent')
            except User.DoesNotExist:
                # Still show success to prevent email enumeration
                messages.error(request, "please enter correct email")
                return redirect('accounts:password_reset')
    else:
        form = PasswordResetRequestForm()

    return render(request, 'authentication/forgot_password/password_reset_form.html', {'form': form})


def password_reset_confirm(request, token):
    try:
        token_obj = PasswordResetToken.objects.get(token=token)
        if not token_obj.is_valid():
            print("token obj not valid")
            return render(request, 'authentication/forgot_password/password_reset_invalid.html')

        user = token_obj.user  # get user from token

        if request.method == 'POST':
            form = PasswordResetConfirmForm(user, request.POST)
            if form.is_valid():
                user.set_password(form.cleaned_data['new_password1'])
                user.save()

                token_obj.is_used = True
                token_obj.save()
                return redirect('accounts:password_reset_complete')
        else:
            form = PasswordResetConfirmForm(user)

        return render(request, 'authentication/forgot_password/password_reset_confirm.html', {
            'form': form,
            'token': token,
            'validlink':True
        })

    except PasswordResetToken.DoesNotExist:
        return render(request, 'authentication/forgot_password/password_reset_invalid.html')


def password_reset_sent(request):
    return render(request, 'authentication/forgot_password/password_reset_done.html')


def password_reset_complete(request):
    return render(request, 'authentication/forgot_password/password_reset_complete.html')
