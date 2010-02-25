from rapidsms.tests.scripted import TestScript
from app import App

class TestApp (TestScript):
    apps = (App,)

    fixtures = ("fosa_location_types", "fosa_test_locations")

    testRegister = """
        2 > reg 10 05
        2 < Invalid Clinic id: 05
	1 > reg asdf
        1 < The correct message format is REG CHWID CLINICID
	1 > reg 01 01
        1 < Unknown clinic id: 01
	1 > reg 01 01001
	1 < Thank you for registering at Biryogo
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
