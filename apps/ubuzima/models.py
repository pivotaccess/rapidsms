from django.db import models
from apps.logger.models import IncomingMessage
from apps.reporters.models import Reporter
from apps.locations.models import Location
from django.utils.translation import ugettext as _
import datetime


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
            return "%s=%.2f" % (_(self.type.description), self.value)
        else:
            return "%s" % _(self.type.description)
    
class Report(models.Model):
    # Constants for our reminders.  Each reminder will be triggered this many days 
    # before the mother's EDD
    DAYS_ANC2 = 150
    DAYS_ANC3 = 60
    DAYS_ANC4 = 14
    DAYS_SUP_EDD = 14
    DAYS_EDD = 7

    reporter = models.ForeignKey(Reporter)
    location = models.ForeignKey(Location)
    village = models.CharField(max_length=255, null=True)
    fields = models.ManyToManyField(Field)
    patient = models.ForeignKey(Patient)
    type = models.ForeignKey(ReportType)
    
    # meaning of this depends on report type.. arr, should really do this as a field, perhaps as a munged int?
    date_string = models.CharField(max_length=10, null=True)

    # our real date if we have one complete with a date and time
    date = models.DateField(null=True)
    
    created = models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return "Report id: %d type: %s patient: %s date: %s" % (self.pk, self.type.name, self.patient.national_id, self.date_string)
    
    def summary(self):
        summary = ""
        if self.date_string:
            summary += "Date=" + self.date_string

        if self.fields.all():
            if self.date_string: summary += ", "
            summary += ", ".join(map(lambda f: unicode(f), self.fields.all()))

        return summary

    def as_verbose_string(self):
        verbose = _("%s Report: ") % self.type.name
        verbose += _("Patient=%s, ") % self.patient
        verbose += _("Location=%s") % self.location
        if self.village:
            verbose += _(" (%s)") % self.village

        summary = self.summary()
        if summary:
            verbose += ", " + self.summary()
        return verbose

    def set_date_string(self, date_string):
        """
        Trap anybody setting the date_string and try to set the date from it.
        """
        self.date_string = date_string

        # try to parse the date.. dd/mm/yyyy
        try:
            self.date = datetime.datetime.strptime(date_string, "%d.%m.%Y").date()
        except ValueError as e:
            # no-op, just keep the date_string value
            pass


    @classmethod
    def get_reports_with_edd_in(cls, date, days, reminder_type):
        """
        Returns all the reports which have an EDD within ``days`` of ``date``.  The results
        will be filtered to not include items which have at least one reminder of the passed
        in type.
        """
        (start, end) = cls.calculate_reminder_range(date, days)

        # only check pregnancy reports
        # TODO: should we check others as well?  not sure what the date means in RISK reports
        # For now we assume everybody needs to register with a pregnancy report first
        preg_type = ReportType.objects.get(pk=4)

        # we only allow one report per patient
        reports = {}

        # filter our reports based on which have not received a reminder yet.
        # TODO: this is simple, but could get slow, at some point it may be worth
        # replacing it with some fancy SQL
        for report in Report.objects.filter(date__gte=start, date__lte=end, type=preg_type):
            if not report.reminders.filter(type=reminder_type):
                reports[report.patient.national_id] = report

        return reports.values()
    
    @classmethod
    def calculate_edd(cls, last_menses):
        """
        Given the date of the last menses, figures out the expected delivery date
        """
            
        # first add seven days
        edd = last_menses + datetime.timedelta(7)

        # figure out if your year needs to be modified, anything later than march will
        # be the next year
        if edd.month > 3:
            edd = edd.replace(year=edd.year+1, month=edd.month+9-12)
        else:
            edd = edd.replace(month=edd.month+9)
        
        return edd

    @classmethod
    def calculate_last_menses(cls, edd):
        """
        Given an EDD, figures out the last menses date.  This is basically the opposite
        function to calculate_edd
        """
        # figure out if your year needs to be modified, anything earlier than october
        # will be in the previous year
        if edd.month <= 9:
            last_menses = edd.replace(year=edd.year-1, month=edd.month-9+12)
        else:
            last_menses = edd.replace(month=edd.month-9)

        # now subtract 7 days
        last_menses = last_menses - datetime.timedelta(7)
        
        return last_menses

    @classmethod
    def calculate_reminder_range(cls, date, days):
        """
        Passed in a day (of today), figures out the range for the menses dates for
        our reminder.  The ``days`` variable is the number of days before delivery
        we want to figure out the date for.  (bracketed by 2 days each way)
        
        """
        # figure out the expected delivery date
        edd = date + datetime.timedelta(days)

        # calculate the last menses
        last_menses = cls.calculate_last_menses(edd)

        # bracket in either direction
        start = last_menses - datetime.timedelta(2)
        end = last_menses + datetime.timedelta(2)
    
        return (start, end)
    
class TriggeredText(models.Model):
    """ Represents an automated text response that is returned to the CHW, SUP or district SUP based 
        on a set of matching action codes. """

    DESTINATION_CHW = 'CHW'
    DESTINATION_SUP = 'SUP'
    DESTINATION_DIS = 'DIS'

    DESTINATION_CHOICES = ( (DESTINATION_CHW, "Community Health Worker"),
                            (DESTINATION_SUP, "Clinic Supervisor"),
                            (DESTINATION_DIS, "District Supervisor") )
    
    name = models.CharField(max_length=128)
    destination = models.CharField(max_length=3, choices=DESTINATION_CHOICES,
                                   help_text="Where this text will be sent to when reports match all triggers.")

    description = models.TextField()
    
    message_kw = models.CharField(max_length=160)
    message_fr = models.CharField(max_length=160)
    message_en = models.CharField(max_length=160)

    triggers = models.ManyToManyField(FieldType,
                                      help_text="This trigger will take effect when ALL triggers match the report.")

    active = models.BooleanField(default=True)


    def trigger_summary(self):
        return ", ".join(map(lambda t: t.description, self.triggers.all()))
    
    def recipients(self):
        return ", ".join(map(lambda a: a.recipient, self.actions.all()))
    
    def __unicode__(self):
        return self.name

    @classmethod
    def get_triggers_for_report(cls, report):
        """
        Returns which trigger texts match this report.
        It is up to the caller to actually send the messages based on the triggers returned.
        """
        types = []
        for field in report.fields.all():
            types.append(field.type.pk)
               
        # these are the texts which may get activated
        texts = TriggeredText.objects.filter(triggers__in=types).distinct().order_by('id')

        # triggers that should be sent back, one per destination
        matching_texts = []
            
        # for each trigger text, see whether we should be triggered by it
        for text in texts:
            matching = True
            
            for trigger in text.triggers.all():
                found = False

                for field in report.fields.all():
                    if trigger.pk == field.type.pk:
                        found = True
                        break
                    
                # not found?  this won't trigger
                if not found:
                    matching = False
            
            if matching:
                matching_texts.append(text)

        # sort the texts, first by number of triggers (more specific texts should be triggered
        # before vague ones) then by id (earliest triggers should take precedence)
        matching_texts.sort(key=lambda tt: "%04d_%06d" % (len(tt.triggers.all()), 100000 - tt.pk))
        matching_texts.reverse()

        # now build a map containing only one trigger per destination
        per_destination = {}
        for tt in matching_texts:
            if not tt.destination in per_destination:
                per_destination[tt.destination] = tt
                
        # return our trigger texts
        matching_list = per_destination.values()
        matching_list.sort(key=lambda tt: tt.pk)
        return matching_list

class ReminderType(models.Model):
    """
    Simple models to keep track of the differen kinds of reminders.
    """

    name = models.CharField(max_length=255)

    message_kw = models.CharField(max_length=160)
    message_fr = models.CharField(max_length=160)
    message_en = models.CharField(max_length=160)

    def __unicode__(self):
        return self.name


class Reminder(models.Model):
    """
    Logs reminders that have been sent.  We use this both for tracking and so that we do
    not send more than one reminder at a time.
    """
    reporter = models.ForeignKey(Reporter)
    report = models.ForeignKey(Report, related_name="reminders", null=True)
    type = models.ForeignKey(ReminderType)
    date = models.DateTimeField()

    @classmethod
    def get_expired_reporters(cls, today):
        # we'll check anybody who hasn't been seen in between 30 and 45 days
        expired_start = today - datetime.timedelta(45)
        expired_end = today - datetime.timedelta(30)

        # reporter reminder type
        expired_type = ReminderType.objects.get(pk=6)

        reporters = set()

        for reporter in Reporter.objects.filter(connections__last_seen__gt = expired_start,
                                                connections__last_seen__lt = expired_end):
            # get our most recent reminder
            reminders = Reminder.objects.filter(reporter=reporter, type=expired_type).order_by('-date')

            # we've had a previous reminder
            if reminders:
                last_reminder = reminders[0]
                # if we were last seen before the reminder, we've already been reminded, skip over
                if reporter.last_seen() < last_reminder.date:
                    continue

            # otherwise, pop this reporter on
            reporters.add(reporter)

        return reporters
                    
    


    
