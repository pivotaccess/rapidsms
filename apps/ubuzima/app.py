import rapidsms

from rapidsms.parsers.keyworder import Keyworder
import re
from apps.locations.models import Location
from apps.ubuzima.models import *
from apps.reporters.models import Reporter


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
        
        m2 = re.search("(fr|eng|rw)", optional_part)    
        
        lang = "kw"
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
            message.respond("You are located at %s, you speak %s" % (message.reporter.location.name, message.reporter.language))
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
        
        optional_part = m.group(3)
        received_clinic_id = m.group(2)
        
        m2 = re.search("(fr|eng|rw)", optional_part)
        
        if m2:
            lang = m2.group(1)
            self.debug("Your prefered language is: %s" % lang)
            
        healthUnit = Location.objects.filter(code=fosa_to_code(received_clinic_id))
        
        if not healthUnit:
            message.respond("Unknown Health unit id: %s" % (received_clinic_id))
            return True
        
        clinic = healthUnit[0]

    
        message.respond("Thank you for registering at %s" % (healthUnit[0].name))
        
        self.debug("sup id: %s  clinic id: %s" % (m.group(1), m.group(2)))
        self.debug("sup message: %s" % healthUnit)
        
        return True



    
    @keyword("pre (whatever)")
    def pregnancy(self, message, notice):
        self.debug("PRE message: %s" % message.text)
        return True
        
