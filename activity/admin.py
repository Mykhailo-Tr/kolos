from django.contrib import admin
from .models import ActivityLog

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    # 1. Відображення всіх полів у списку
    list_display = ('id', 'created_at', 'user', 'action', 'description_full')
    
    # 2. Додаємо можливість клікнути на користувача або дату для переходу в деталі
    list_display_links = ('id', 'created_at')
    
    # 3. Фільтрація (справа)
    list_filter = ('action', 'created_at', 'user')
    
    # 4. Пошук по всіх ключових полях
    search_fields = ('user__username', 'description', 'action')
    
    # 5. Робимо поля доступними тільки для читання (щоб не можна було змінити історію)
    readonly_fields = ('user', 'action', 'description', 'created_at')

    # 6. Сортування (найновіші зверху)
    ordering = ('-created_at',)

    def description_full(self, obj):
        """Відображає повний опис, щоб він не обрізався в таблиці"""
        return obj.description
    description_full.short_description = "Деталі дії"

    # Щоб бачити більше деталей при натисканні на запис:
    fieldsets = (
        ('Основна інформація', {
            'fields': ('created_at', 'user', 'action')
        }),
        ('Контент', {
            'fields': ('description',),
        }),
    )

    # Заборона редагування
    def has_add_permission(self, request):
        return False