import rapidsms

from rapidsms.parsers.keyworder import Keyworder
import re
from apps.locations.models import Location
from apps.ubuzima.models import *
from apps.reporters.models import *


class App (rapidsms.app.App):
    
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
        
        if results:
            func, captures = results
            return func(self, message, *captures)
        else:
            self.debug("NO MATCH FOR %s" % message.text)
            message.respond("We don't recogniz this messge")
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


    @keyword("reg (whatever)")
    def register(self, message, notice):
        self.debug("REG message: %s" % message.text)
        m = re.search("reg\s+(\d+)\s+(\d+)(.*)", message.text, re.IGNORECASE)
             
        
        if not m:
            message.respond("The correct message format is REG CHWID CLINICID")
            return True
        received_chw_id = m.group(1)
        received_clinic_id = m.group(2)
        optional_part = m.group(3)
        
        
        
        
        clinics = Location.objects.filter(code=fosa_to_code(received_clinic_id))
        
        if not clinics:
            message.respond("Unknown clinic id: %s" % (received_clinic_id))
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
        
        m2 = re.search("(fr|en|rw)", optional_part)    
        
        lang = "rw"
        if m2:
            lang = m2.group(1)
            self.debug("Your prefered language is: %s" % lang) 
 
            
        message.reporter.language = lang
        message.reporter.save()
        
        message.respond("Thank you for registering at %s" % (clinics[0].name))
        
        self.debug("chw id: %s  clinic id: %s" % (m.group(1), m.group(2)))
        self.debug("Reg mesage: %s" % clinics)
    
        return True

    
    @keyword("who")
    def who(self, message):
        if (getattr(message, 'reporter', None)):
            if not message.reporter.groups.all():
                message.respond("You are not in a group, located at %s, you speak %s" % (message.reporter.location.name, message.reporter.language))          
            else:
                message.respond("You are a %s, located at %s, you speak %s" % (message.reporter.groups.all()[0].title, message.reporter.location.name, message.reporter.language))
            
        else:
            message.respond("We don't recognize you")
        return True
        
        
    @keyword("sup (whatever)")
    def supervisor(self, message, notice):
        self.debug("SUP message: %s" % message.text)
        m = re.search("sup\s+(\d+)\s+(\d+)(.*)", message.text, re.IGNORECASE)
        if not m:
            message.respond("The correct format message is  SUP SUPID CLINICID or HOSPITALID")
            return True
        
        received_sup_id = m.group(1)
        received_clinic_id = m.group(2)
        optional_part = m.group(3)
        
        
            
        healthUnit = Location.objects.filter(code=fosa_to_code(received_clinic_id))
        
        if not healthUnit:
            message.respond("Unknown Health unit id: %s" % (received_clinic_id))
            return True
        
        clinic = healthUnit[0]
        
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
        message.respond("Thank you for registering at %s" % (healthUnit[0].name))
        
        self.debug("sup id: %s  clinic id: %s" % (m.group(1), m.group(2)))
        self.debug("sup message: %s" % healthUnit)
        
        return True



    
    @keyword("pre (whatever)")
    def pregnancy(self, message, notice):
        self.debug("PRE message: %s" % message.text)

        if not getattr(message, 'reporter', None):
            message.respond("You need to be registered first")
            return True


        m = re.search("pre\s+(\d+)\s+(\d+)(.*)", message.text, re.IGNORECASE)
        if not m:
            message.respond("The correct format message is  PRE PATIENT_ID DATE_BIRTH")
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
        action_codes = []
        num_mov_codes = 0
        invalid_codes = []
        
        for code in codes:
            print "code: %s" % code
            try:
                action_code = ActionCode.objects.get(code=code)
                action_codes.append(action_code)
                
                # if the action code is a movement code, increment our counter
                if action_code.type.id == 4:
                    num_mov_codes += 1
                   
                                               
            except ActionCode.DoesNotExist:
                 invalid_codes.append(code)

#        #in case an unknown action code is received  and more than one movement code     
#        if len(invalid_codes)>0 and num_mov_codes>1:
#            message.respond("Error.  More than one movement code and Unknown action code: %s" % ", ".join(invalid_codes))   
#            return True
#               
#        #in case an unknown action code is received       
#        if len(invalid_codes) > 0:
#            message.respond("Error.  Unknown action code: %s" % ", ".join(invalid_codes))   
#            return True
#        
#        # error out if there is more than one movement code    
#        if num_mov_codes > 1:
#            message.respond("Error.  You cannot give more than one movement code")
#            return True
        
        
        error_msg = ""
        if len(invalid_codes) > 0:
            error_msg += "Error.  Unknown action code: %s.  " % ", ".join(invalid_codes)
            
        if num_mov_codes > 1:
            error_msg += "Error.  You cannot give more than one movement code"
        
        if error_msg:
            message.respond("Error.  %s" % error_msg)
            return True
        
        # save the report
        report.save()
        
        # then associate all the action codes with it
        for action_code in action_codes:
            report.action_codes.add(action_code)            
            
        message.respond("Pregnancy report submitted successfully")
        
        return True
            











        
