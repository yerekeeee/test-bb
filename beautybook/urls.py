from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from booking.views import admin_dashboard
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth import views as auth_views
from users.views import CustomLoginView

urlpatterns = [
    path(
        'accounts/login/staff/',
        auth_views.LoginView.as_view(template_name='registration/staff_login.html'),
        name='staff_login'  # <--- Вот имя, которое ищет Django
    ),
    path('accounts/login/', CustomLoginView.as_view(), name='login'),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/', include('users.urls')),
    path('booking/', include('booking.urls')),
    path('dashboard/', admin_dashboard, name='admin_dashboard'),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += staticfiles_urlpatterns()
