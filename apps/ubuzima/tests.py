from rapidsms.tests.scripted import TestScript
from app import App
from apps.reporters.app import App as ReporterApp

class TestApp (TestScript):
    apps = (App, ReporterApp)

    fixtures = ("fosa_location_types", "fosa_test_locations", "groups")

    testRegister = """
        2 > reg 10 05
        2 < Unknown clinic id: 05
	    1 > reg asdf
        1 < The correct message format is REG CHWID CLINICID
	    1 > reg 01 01
        1 < Unknown clinic id: 01
	1 > reg 01 01001
	1 < Thank you for registering at Biryogo
        3 > REG 01 01001 
        3 < Thank you for registering at Biryogo

	#testing the default language
	3 > WHO
	3 < You are a CHW, located at Biryogo, you speak rw
	
        4 > WHO
	4 < We don't recognize you
        5 > REG 08 01001 en
        5 < Thank you for registering at Biryogo
        5 > WHO
	5 < You are a CHW, located at Biryogo, you speak en
        
    """
    
    testSupervisor = """
        1 > sup 23 05094 en    
        1 < Thank you for registering at Gashora 
	4 > WHO
        4 < We don't recognize you
	1 > who   
	1 < You are a Supervisor, located at Gashora, you speak en

        2 > sup 34 048547 fr
        2 < Unknown Health unit id: 048547
        3 > SUP 23 048547 fr
        3 < Unknown Health unit id: 048547 
    """

    # define your test scripts here.
    # e.g.:
    #
    # testRegister = """
    #   8005551212 > register as someuser
    #   8005551212 < Registered new user 'someuser' for 8005551212!
    #   8005551212 > tell anotheruser what's up??
    #   8005550000 < someuser said "what's up??"
    # """
    #
    # You can also do normal unittest.TestCase methods:
    #
    # def testMyModel (self):
    #   self.assertEquals(...)
