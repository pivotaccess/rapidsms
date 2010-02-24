import rapidsms

from rapidsms.parsers.keyworder import Keyworder

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
        return True
        
    @keyword("sup (whatever)")
    def supervisor(self, message, notice):
        self.debug("SUP message: %s" % message.text)
        return True
    
    @keyword("pre (whatever)")
    def pregnancy(self, message, notice):
        self.debug("PRE message: %s" % message.text)
        return True
        