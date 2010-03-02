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


class CodeType(models.Model):
    name = models.CharField(max_length=30, unique=True)
    
    def __unicode__(self):
        return self.name
 

class ReportType(models.Model):
    name = models.CharField(max_length=30, unique=True)
    
    def __unicode__(self):
        return self.name   

class ActionCode(models.Model):
    code = models.CharField(max_length=4, unique=True)
    description = models.TextField(blank=True)
    type = models.ForeignKey(CodeType)

    def __unicode__(self):
        return self.code
    
class Patient(models.Model):
    location = models.ForeignKey(Location)
    national_id = models.CharField(max_length=20, unique=True)
    dob = models.DateField(null=True)
    
    def __unicode__(self):
        return self.national_id
    
class Report(models.Model):
    reporter = models.ForeignKey(Reporter)
    action_codes = models.ManyToManyField(ActionCode)
    patient = models.ForeignKey(Patient)
    type = models.ForeignKey(ReportType)
    
    def __unicode__(self):
        return "Report id: %d type: %s patient: %s" % (self.pk, self.type.name, self.patient.national_id) 
