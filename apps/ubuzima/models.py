from django.db import models
from apps.logger.models import IncomingMessage
from apps.reporters.models import Reporter
from apps.locations.models import Location


# Create your Django models here, if you need them.

def fosa_to_code(fosa_id):
    """Given a fosa id, returns a location code"""
    return "F" + fosa_id

def code_to_fosa(code):
    """Given a location code, returns the fosa id"""
    return code[1:]


class FieldCategory(models.Model):
    name = models.CharField(max_length=30, unique=True)
    
    def __unicode__(self):
        return self.name
 

class ReportType(models.Model):
    name = models.CharField(max_length=30, unique=True)
    
    def __unicode__(self):
        return self.name   

class FieldType(models.Model):
    key = models.CharField(max_length=32, unique=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(FieldCategory)
    has_value = models.BooleanField(default=False)

    def __unicode__(self):
        return self.key
    
class Patient(models.Model):
    location = models.ForeignKey(Location)
    national_id = models.CharField(max_length=20, unique=True)
    
    def __unicode__(self):
        return "%s" % self.national_id
    
    
class Field(models.Model):
    type = models.ForeignKey(FieldType)
    value = models.DecimalField(max_digits=10, decimal_places=5, null=True)
    
    def __unicode__(self):
        if self.value:
            return "%s=%.2f" % (self.type.key, self.value)
        else:
            return "%s" % self.type.key
    
class Report(models.Model):
    reporter = models.ForeignKey(Reporter)
    location = models.ForeignKey(Location)
    village = models.CharField(max_length=255, null=True)
    fields = models.ManyToManyField(Field)
    patient = models.ForeignKey(Patient)
    type = models.ForeignKey(ReportType)
    
    # meaning of this depends on report type.. arr, should really do this as a field, perhaps as a munged int?
    date = models.CharField(max_length=10, null=True)
    
    created = models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return "Report id: %d type: %s patient: %s date: %s" % (self.pk, self.type.name, self.patient.national_id, self.date)
    
    def summary(self):
        return ", ".join(map(lambda f: unicode(f), self.fields.all()))
    
RECIPIENT_CHOICES = ( ('SUP', 'Supervisor'),
                      ('CHW', 'Community Health Worker'),
                      ('ALL', 'Community Health Worker and Supervisor') )    

class AlertAction(models.Model):
    recipient = models.CharField(max_length=3, choices=RECIPIENT_CHOICES)
    message = models.CharField(max_length=160)
    
    def __unicode__(self):
        return "'%s' => %s" % (self.message, self.recipient)
    
class Alert(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField()
    actions = models.ManyToManyField(AlertAction)
    triggers = models.ManyToManyField(FieldType)
    active = models.BooleanField(default=True)
    
    def trigger_summary(self):
        return ", ".join(map(lambda t: t.description, self.triggers.all()))
    
    def recipients(self):
        return ", ".join(map(lambda a: a.recipient, self.actions.all()))
    
    def __unicode__(self):
        return self.name