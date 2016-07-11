from django.contrib import admin
from app.models import BiomSearchJob, EcosystemChoice, Guest, Job


class BiomSearchJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'completed')


class GuestAdmin(admin.ModelAdmin):
    list_display = ('user', 'status_display')

    def status_display(self, obj):
        return obj.status

    status_display.short_description = "Guest"
    status_display.boolean = True


admin.site.register(Job)
admin.site.register(Guest, GuestAdmin)
admin.site.register(BiomSearchJob, BiomSearchJobAdmin)
admin.site.register(EcosystemChoice)
