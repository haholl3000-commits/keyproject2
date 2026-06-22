from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
# Убрали register_view из импорта ниже
from documents.views import dashboard, generate_keys, sign_document, verify_document

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard, name='dashboard'),

    # Только вход и выход
    path('login/', auth_views.LoginView.as_view(template_name='documents/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='dashboard'), name='logout'),

    # Функции ЭЦП
    path('generate-keys/', generate_keys, name='generate_keys'),
    path('sign/<int:doc_id>/', sign_document, name='sign_document'),
    path('verify/<int:doc_id>/', verify_document, name='verify_document'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)