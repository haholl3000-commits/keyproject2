import os
import django
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Автоматический прогон миграций при старте контейнера
from django.core.management import call_command
try:
    call_command('migrate', interactive=False)
    
    # Автосоздание суперпользователя
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', '12345678')
        print("Суперпользователь admin создан успешно!")
except Exception as e:
    print(f"Ошибка миграций при старте: {e}")

application = get_wsgi_application()