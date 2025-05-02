from django.urls import path
from .views import *

app_name = "accounts"

urlpatterns = [
    path('login/', login_view, name='login'),
    path('admin-dashboard/', admin_dashboard, name="admin_dashboard"),
    path('password-reset', forgot_password, name="password_reset"),
        path('password-reset/sent/', password_reset_sent, name='password_reset_sent'),
    path('password-reset/<str:token>/', password_reset_confirm, name='password_reset_confirm'),
    path('password-reset/complete/', password_reset_complete, name='password_reset_complete'),
]