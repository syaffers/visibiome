from django.contrib import admin
from app.models import BiomSample, BiomSearchJob, EcosystemChoice, Guest


class BiomSearchJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'status')


class BiomSampleAdmin(admin.ModelAdmin):
    list_display = ('name', 'job')


class GuestAdmin(admin.ModelAdmin):
    list_display = ('user', 'status_display')

    def status_display(self, obj):
        return obj.status

    status_display.short_description = "Guest"
    status_display.boolean = True


admin.site.register(Guest, GuestAdmin)
admin.site.register(BiomSample, BiomSampleAdmin)
admin.site.register(BiomSearchJob, BiomSearchJobAdmin)
admin.site.register(EcosystemChoice)
