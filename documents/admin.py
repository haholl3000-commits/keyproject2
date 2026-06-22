from django.contrib import admin
from .models import Document, UserProfile, ActionLog


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'status', 'created_at')
    list_filter = ('status', 'owner')
    search_fields = ('title',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'public_key_status')

    def public_key_status(self, obj):
        return "Ключ выпущен" if obj.public_key else "Ключ отсутствует"

    public_key_status.short_description = "Статус ключа"


@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    # Теперь в админке будет видно: кто, что и когда сделал
    list_display = ('user', 'action', 'details', 'created_at')
    list_filter = ('user', 'action', 'created_at')
    search_fields = ('action', 'details', 'user__username')
    readonly_fields = ('created_at',)  # Логи нельзя менять, только смотреть