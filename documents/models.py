from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator

class Document(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('pending', 'На подписи'),
        ('signed', 'Подписан'),
    ]

    title = models.CharField(max_length=255, verbose_name="Название документа")
    file = models.FileField(
        upload_to='docs/',
        verbose_name="Файл",
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'docx', 'jpg', 'png', 'txt'])]
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    digital_signature = models.TextField(null=True, blank=True, verbose_name="Цифровая подпись")
    file_hash = models.CharField(max_length=64, null=True, blank=True, verbose_name="Хэш файла")

    def __str__(self):
        return self.title

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    public_key = models.TextField(null=True, blank=True, verbose_name="Открытый ключ")

    def __str__(self):
        return f"Профиль: {self.user.username}"

# --- НОВАЯ МОДЕЛЬ ДЛЯ ЛОГОВ ---
class ActionLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    action = models.CharField(max_length=255, verbose_name="Действие")
    details = models.TextField(blank=True, verbose_name="Детали")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время")

    class Meta:
        verbose_name = "Лог действия"
        verbose_name_plural = "Логи действий"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.action} ({self.created_at.strftime('%d.%m %H:%M')})"