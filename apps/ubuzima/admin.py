from django.contrib import admin
from apps.ubuzima.models import *

admin.site.register(Report)
admin.site.register(ReportType)
admin.site.register(Field)
admin.site.register(FieldType)
admin.site.register(Patient)

class TriggerAdmin(admin.ModelAdmin):
    pass

admin.site.register(TriggeredText, TriggerAdmin)



