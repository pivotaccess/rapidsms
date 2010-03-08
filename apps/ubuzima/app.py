import rapidsms

from rapidsms.parsers.keyworder import Keyworder
import re
from apps.locations.models import Location
from apps.ubuzima.models import *
from apps.reporters.models import *
from django.utils.translation import ugettext as _
from django.utils.translation import activate
from decimal import *
from exceptions import Exception
import traceback

class App (rapidsms.app.App):
    
    # map of language code to language name
    LANG = { 'en': 'English',
             'fr': 'French',
             'rw': 'Kinyarwanda' }
    
    keyword = Keyworder()
    
    def start (self):
        """Configure your app in the start phase."""
        pass

    def parse (self, message):
        """Parse and annotate messages in the parse phase."""
        pass

    def handle (self, message):
        """Add your main application logic in the handle phase."""
        results = self.keyword.match(self, message.text)
        
        # do we know this reporter?
        if getattr(message, 'reporter', None):
            activate(message.reporter.language)
        else:
            activate('rw')
        
        if results:
            try:
                func, captures = results
                return func(self, message, *captures)
            except Exception as e:
                self.debug("Error: %s %s" % (e, traceback.format_exc()))
                message.respond(_("Unknown Error, please check message format and try again."))
                return True
        else:
            self.debug("NO MATCH FOR %s" % message.text)
            message.respond(_("We don't recogniz this message"))
            return True
    
    def cleanup (self, message):
        """Perform any clean up after all handlers have run in the
           cleanup phase."""
        pass

    def outgoing (self, message):
        """Handle outgoing message notifications."""
        pass

    def stop (self):
        """Perform global app cleanup when the application is stopped."""
        pass


    @keyword("\s*reg(.*)")
    def register(self, message, notice):
        self.debug("REG message: %s" % message.text)
        m = re.search("reg\s+(\d+)\s+(\d+)(.*)", message.text, re.IGNORECASE)
        
        if not m:
            message.respond(_("The correct message format is REG CHWID CLINICID"))
            return True
        received_chw_id = m.group(1)
        received_clinic_id = m.group(2)
        optional_part = m.group(3)
        
        clinics = Location.objects.filter(code=fosa_to_code(received_clinic_id))
        
        if not clinics:
            message.respond(_("Unknown clinic id: %(clinic)s") % \
            { 'clinic': received_clinic_id })
            return True
        
        clinic = clinics[0]
         
        #do we already have a report for our connection?
        #if so, just update it
        if not getattr(message, 'reporter', None):
            rep, created = Reporter.objects.get_or_create(alias=received_chw_id)
            message.reporter = rep
            
        #connect this reporter to the connection
        message.persistant_connection.reporter = message.reporter
        message.persistant_connection.save()
        
        self.debug("saved connection: %s to reporter: %s" % (message.persistant_connection, message.reporter))
        
        #set the location for this reporter
        message.reporter.location = clinic
        
        #set the group for this reporter
        group = ReporterGroup.objects.get(title='CHW')
        message.reporter.groups.add(group)
        
        m2 = re.search("(.*)(fr|en|rw)(.*)", optional_part)    
        
        lang = "rw"
        if m2:
            lang = m2.group(2)
            self.debug("Your prefered language is: %s" % lang) 
                        
            # build our new optional part, which is just the remaining stuff
            optional_part = ("%s %s" % (m2.group(1), m2.group(3))).strip()

        # save away the language
        message.reporter.language = lang

        # if we actually have remaining text, then save that away as our village name
        if optional_part:
            message.reporter.village = optional_part
             
        # save our reporter
        message.reporter.save()
        
        # set our language
        activate(lang)
        
        message.respond(_("Thank you for registering at %(clinic)s") % \
                        { 'clinic':clinics[0].name })
        
        self.debug("chw id: %s  clinic id: %s" % (m.group(1), m.group(2)))
        self.debug("Reg mesage: %s" % clinics)
    
        return True

    
    @keyword("\s*who")
    def who(self, message):
        """Returns what we know about the sender of this message.  This is used primarily for unit
           testing though it may prove usefu in the field"""
           
        if getattr(message, 'reporter', None):
            if not message.reporter.groups.all():
                message.respond(_("You are not in a group, located at %(location)s, you speak %(language)s") % \
                    { 'location': message.reporter.location.name, 'language': App.LANG[message.reporter.language] } )          
            else:
                location = message.reporter.location.name
                if message.reporter.village:
                    location += " (%s)" % message.reporter.village

                message.respond(_("You are a %(group)s, located at %(location)s, you speak %(language)s") % \
                    { 'group': message.reporter.groups.all()[0].title, 'location': location, 'language': App.LANG[message.reporter.language] } )
            
        else:
            message.respond(_("We don't recognize you"))
        return True
    
    @keyword("\s*last")
    def last(self, message):
        if not getattr(message, 'reporter', None):
            message.respond("We dont recognize you, register first.")
            return True
    
        reports = Report.objects.filter(reporter=message.reporter).order_by('-pk')
    
        if not reports:
            message.respond("you have not yet sent any report")
            return True
    
        report = reports[0]
        
        fields = []
        for field in report.fields.all().order_by('type'):
            fields.append(unicode(field))
        
        message.respond("type: %s patient: %s fields: %s" %  \
            (report.type, report.patient, ", ".join(fields)))
        
        return True    
    
        
    
        
    @keyword("\s*sup(.*)")
    def supervisor(self, message, notice):
        self.debug("SUP message: %s" % message.text)
        m = re.search("sup\s+(\d+)\s+(\d+)(.*)", message.text, re.IGNORECASE)
        if not m:
            message.respond(_("The correct format message is  SUP SUPID CLINICID or HOSPITALID"))
            return True
        
        received_sup_id = m.group(1)
        received_clinic_id = m.group(2)
        optional_part = m.group(3)
        
        
            
        clinic = Location.objects.filter(code=fosa_to_code(received_clinic_id))
        
        if not clinic:
            message.respond(_("Unknown Health unit id: %(clinic)s") % \
            { "clinic": received_clinic_id})
            return True
        
        clinic = clinic[0]
        
        #do we already have a report for our connection?
        #if so, just update it
        if not getattr(message, 'reporter', None):
            rep, created = Reporter.objects.get_or_create(alias=received_sup_id)
            message.reporter = rep
            
        #connect this reporter to the connection
        message.persistant_connection.reporter = message.reporter
        message.persistant_connection.save()
        
        self.debug("saved connection: %s to reporter: %s" % (message.persistant_connection, message.reporter))
        
        #set the location for this reporter
        message.reporter.location = clinic
        
        #set the group for this reporter
        group = ReporterGroup.objects.get(title='Supervisor')
        message.reporter.groups.add(group)
        
        m2 = re.search("(fr|en|rw)", optional_part)
        lang = "rw" #the default language
        
        if m2:
            lang = m2.group(1)
            self.debug("Your prefered language is: %s" % lang)
        
        message.reporter.language = lang
        message.reporter.save()

        activate(lang)
        
        message.respond(_("Thank you for registering at %(clinic)s") % \
        { 'clinic': clinic.name } )
        
        self.debug("sup id: %s  clinic id: %s" % (m.group(1), m.group(2)))
        self.debug("sup message: %s" % clinic)
        
        return True



    
    @keyword("\s*pre(.*)")
    def pregnancy(self, message, notice):
        self.debug("PRE message: %s" % message.text)

        if not getattr(message, 'reporter', None):
            message.respond(_("You need to be registered first"))
            return True


        m = re.search("pre\s+(\d+)\s+(\d+)(.*)", message.text, re.IGNORECASE)
        if not m:
            message.respond(_("The correct format message is  PRE PATIENT_ID DATE_BIRTH"))
            return True
        
        received_patient_id = m.group(1)
        date_birth = m.group(2)
        optional_part = m.group(3)

        # get or create the patient
        patient, created = Patient.objects.get_or_create(national_id=received_patient_id,\
        location=message.reporter.location)
                
        # create our report
        report_type = ReportType.objects.get(name='Pregnancy')
        report = Report(patient=patient, reporter=message.reporter, type=report_type)
        
        # add our action codes to the report
        codes = optional_part.split()
        fields = []
        num_mov_codes = 0
        invalid_codes = []
        
        for code in codes:
            try:
                field_type = FieldType.objects.get(key=code.lower())
                fields.append(Field(type=field_type))
                
                # if the action code is a movement code, increment our counter
                if field_type.category.id == 4:
                    num_mov_codes += 1
                   
                                               
            except FieldType.DoesNotExist:
                 invalid_codes.append(code)

        # take care of any error messaging
        error_msg = ""
        if len(invalid_codes) > 0:
            error_msg += _("Unknown action code: %(invalidcode)s.  ") % \
            { 'invalidcode':  ", ".join(invalid_codes)}
            
        if num_mov_codes > 1:
            error_msg += unicode(_("You cannot give more than one movement code"))
        
        if error_msg:
            message.respond(_("Error.  %(error)s") % \
            { 'error': error_msg })
            return True
        
        # save the report
        report.save()
        
        # then associate all the action codes with it
        for field in fields:
            field.save()
            report.fields.add(field)            
            
        message.respond(_("Pregnancy report submitted successfully"))
        
        return True
    
    @keyword("\s*risk(.*)")
    def risk(self, message, notice):
        if not getattr(message, 'reporter', None):
            message.respond(_("Get registered first"))
            return True
            
        m = re.search("risk\s+(\d+)(.*)", message.text, re.IGNORECASE)
        if not m:
            message.respond(_("The correct format message is  RISK PATIENT_ID"))
            return True
        received_patient_id = m.group(1)
        optional_part = m.group(2)
        
        # Create the report and link the particular patient to the report
        # in case patient have never been registered, report Pregnancy first
        try:
            patient = Patient.objects.get(national_id=received_patient_id)
                        
        except Patient.DoesNotExist:
            message.respond(_("Always report Pregnancy before any risk report to a patient"))
            return True

        report_type = ReportType.objects.get(name='Risk')
        report = Report(patient=patient, reporter=message.reporter, type=report_type)
        
        # Line below may be needed in case Risk reports are sent without previous Pregnancy reports
        location = message.reporter.location
        
        
        # add our action codes to the report

        codes = optional_part.split()
        fields = []
        num_mov_codes = 0
        invalid_codes = []
        
        for code in codes:
            try:
                field_type = FieldType.objects.get(key=code.lower())
                fields.append(Field(type=field_type))
                
                # if the action code is a movement code, increment our counter
                if field_type.category.id == 4:
                    num_mov_codes += 1
                   
                                               
            except FieldType.DoesNotExist:
                 invalid_codes.append(code)


        error_msg = ""
        if len(invalid_codes) > 0:
            error_msg += _("Unknown action code: %s.  ") % ", ".join(invalid_codes)
            
        if num_mov_codes > 1:
            error_msg += _("You cannot give more than one movement code")
        
        if error_msg:
            message.respond(_("Error.  %(error)s") % \
            { 'error': error_msg })
            return True
        
        # save the report
        
        report.save()
        
        # then associate all the action codes with it
        for field in fields:
            field.save()
            report.fields.add(field)            
            
        message.respond(_("Thank you! Risk report submitted"))
        
        return True
    
    
    
    #Birth keyword
    @keyword("\s*bir(.*)")
    def birth(self, message, notice):
        
        if not getattr(message, 'reporter', None):
            message.respond(_("Please,Get registered first, unknown Health agent"))
            return True
            
        m = re.search("bir\s+(\d+)(.*)", message.text, re.IGNORECASE)
        if not m:
            message.respond(_("The correct format message is BIR PATIENT_ID"))
            return True
        received_patient_id = m.group(1)
        optional_part = m.group(2)
        
        # Create the report and link the particular patient to the report
        # in case the mother have never been registered, report Pregnancy first
        try:
            patient = Patient.objects.get(national_id=received_patient_id)
                        
        except Patient.DoesNotExist:
            message.respond(_("Always report Pregnancy before any birth report"))
            return True
        
        report_type = ReportType.objects.get(name='Birth')
        report = Report(patient=patient, reporter=message.reporter, type=report_type)
        
        Location = message.reporter.location
        
        # Add field types in our report
        codes = optional_part.split()
        fields = []
        num_mov_codes = 0
        invalid_codes = []
        
        for code in codes:
            try:
                field_type = FieldType.objects.get(key=code.lower())
                fields.append(Field(type=field_type))
                
                # if the action code is a movement code, increment our counter
                if field_type.category.id == 4:
                    num_mov_codes += 1
                
            except FieldType.DoesNotExist:
                m1 = re.search("(\d+\.?\d*)K", code, re.IGNORECASE)
                m2 = re.search("(\d+\.?\d*)cm", code, re.IGNORECASE)
                
                # this is a weight
                if m1:
                    field_type = FieldType.objects.get(key="child_weight")
                    value = Decimal(m1.group(1))
                    field = Field(type=field_type, value=value)
                    fields.append(field)
                    
                # this is a length
                elif m2:
                    field_type = FieldType.objects.get(key="child_length")
                    value = Decimal(m2.group(1))
                    field = Field(type=field_type, value=value)
                    fields.append(field)
                    
                # unknown, add to invalid codes
                else:
                    invalid_codes.append(code)
                    
        error_msg = ""
        if len(invalid_codes) > 0:
            error_msg += _("Unknown action code: %s.  ") % ", ".join(invalid_codes)
            
        if num_mov_codes > 1:
            error_msg += _("You cannot give more than one movement code")
        
        if error_msg:
            message.respond(_("Error.  %(error)s") % \
            { 'error': error_msg })
            return True
        
        # save the report
        
        report.save()
        
        # then associate all the action codes with it
        for field in fields:
            field.save()
            report.fields.add(field)            
            
        message.respond(_("Thank you! Birth report submitted"))
        return True
                
        
        
        
        
        
        
        
        
        
        
        
        
        
        
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    