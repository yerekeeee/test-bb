from django.contrib.auth.views import LoginView
from .forms import CustomAuthenticationForm, ClientSignUpForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone


@login_required
def profile_view(request):
    user = request.user
    template_name = 'home.html'
    context = {'now': timezone.now()}

    if hasattr(user, 'masterprofile'):
        template_name = 'profile/master_profile.html'
        context['upcoming_appointments'] = user.masterprofile.appointments.filter(
            start_time__gte=context['now']).order_by('start_time')
    else:
        template_name = 'profile/client_profile.html'
        context['appointments'] = user.appointments.order_by('-start_time')

    return render(request, template_name, context)


def signup_view(request):
    if request.method == 'POST':
        form = ClientSignUpForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = ClientSignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

class CustomLoginView(LoginView):
    """
    Это представление для входа клиентов.
    Оно наследует всю логику от стандартного LoginView,
    но использует нашу кастомную форму.
    """
    form_class = CustomAuthenticationForm
    template_name = 'registration/login.html'
