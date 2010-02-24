#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


import os, csv, decimal
from django.core.management.base import NoArgsCommand
from locations.models import * #we are importing model classes from locations app

IMPORT_DIR = os.path.abspath("apps/ubuzima/import")

class Command(NoArgsCommand):
    
    def _csv(self, filename):
        """Returns a CSV reader for _filename_
           relative to the sources directory."""
        path = os.path.join(IMPORT_DIR, filename)
        return csv.reader(file(path))
    
    
    def _hospital_name(self, original):
        return original.replace(" HD", "").capitalize()
    
    
    def _loc_type (self, name):
        return LocationType.objects.get(name__iexact=name)
    
    
    def __init__(self):
        self.provinces = {}
        self.districts = {}
        self.hospitals = {}
        self.healthcentres = {}
    
    def handle_noargs(self, **options):
        #delete all locations before insertion, 
        #we might change his during production
        Location.objects.all().delete()
        
        rows = list(self._csv("FosaListTable.csv"))
        for row in rows:
            # ensure that the province exists
            province, p_created = \
                self._loc_type("province").locations.get_or_create(
                    name=row[6].capitalize(),
                    code=row[4])

            if p_created:
                print ". Created Province: %s" % (province)

            # ensure that the district exists, and is
            # linked to the province named on this row
            district, d_created = \
                    self._loc_type("district").locations.get_or_create(
                        parent=province,
                        name=row[8].capitalize(),
                        code=row[7])
            
            if d_created:
                    print ". Created District: %s" % (district)
                    self.districts[district.code] = district
        
        # second iteration: create all of the hospitals. we must do
        # this before the health centres, since many health centres
        # link (by name) to the hospitals before they are listed
        for row in rows:
            if row[3] == "HD":
                try:
                    # wooo geo co-ords!
                    lat = decimal.Decimal(row[11])
                    lon = decimal.Decimal(row[12])
                
                # django doesn't accept invalid decimals, so
                # leave both fields null if they can't be cast
                except decimal.InvalidOperation:
                    lat = lon = None

                hospital, created = \
                    self._loc_type("hospital").locations.get_or_create(
                        parent=self.districts[row[7]],
                        name=self._hospital_name(row[2]),
                        code=row[1],
                        latitude=lat,
                        longitude=lon)

                if created:
                    print ". Created Hospital: %s" %\
                        (hospital)
                    self.hospitals[hospital.name] = hospital


        # third iteration: create all of the remaining health
        # centres, and link them back to the hospitals. this is
        # very similar to above, and should probably be refactored
        for row in rows:
            if row[3] == "CS":

                # some locations are missing their
                # government FOSA CODE. this just
                # won't do, so skip it
                if not row[1]:
                    print "! Health Centre missing FOSA code: %s" % (row[2])
                    continue


                try:
                    # wooo geo co-ords!
                    lat = decimal.Decimal(row[11])
                    lon = decimal.Decimal(row[12])
                
                # django doesn't accept invalid decimals, so
                # leave both fields null if they can't be cast
                except decimal.InvalidOperation:
                    lat = lon = None


                # resolve the hospital name into an object.
                # if the parent was invalid, skip this location
                try:
                    parent = self.hospitals[self._hospital_name(row[18])]

                except KeyError:
                    continue

                healthcentre, created = \
                    self._loc_type("health centre").locations.get_or_create(
                        parent=parent,
                        name=row[2],
                        code=row[1],
                        latitude=lat,
                        longitude=lon)

                if created:
                    print ". Created Health Centre: %s" %\
                        (healthcentre)
                