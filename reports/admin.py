from django.contrib import admin
from .models import ReportTemplate, ReportExecution, SavedReport


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'report_type', 'chart_type', 'created_by', 'is_public', 'created_at')
    list_filter = ('report_type', 'chart_type', 'is_public', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)


@admin.register(ReportExecution)
class ReportExecutionAdmin(admin.ModelAdmin):
    list_display = ('template', 'executed_by', 'executed_at', 'date_from', 'date_to', 'row_count')
    list_filter = ('executed_at', 'template')
    search_fields = ('template__name', 'executed_by__username')
    ordering = ('-executed_at',)
    readonly_fields = ('executed_at',)


@admin.register(SavedReport)
class SavedReportAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'template', 'created_at')
    list_filter = ('created_at', 'template')
    search_fields = ('name', 'user__username', 'template__name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)