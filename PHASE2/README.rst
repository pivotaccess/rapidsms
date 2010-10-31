
Migration
=========

Some new features require database changes.  This document details how to apply them.

SQL Migration
-------------

Some of the SQL tables were changed to deal with new models.  First make sure to shut down rapidsms and the route process.   Then run the migration script::

   % mysql -u ubuzima -p ubuzima < migrate.sql

This will modify a bunch of tables, adding some, renaming others.

Finally, add the new tables that are needed by running syncdb::

   % python rapidsms syncdb

Date Migration
--------------

One of the things changed was to add a real date field to the Report object.  We need to backfill dates for all reports based on the previous string field.  The migratedates management command does this::

   % python rapidsms migratedates

Reminder Tables
---------------

Finally, we added some other new fields for reminders that need to be loaded via fixtures.

   % python loaddata reminder_types.json

Unit Tests
----------

You should run the unit tests to make sure everything looks sane::

   % python rapidsms test

Crontab
-------

To trigger reminders, we now have to run a management script every day.  You can test this out by running::

   % python rapidsms checkreminders --dry

This will show all the reminders that would be sent without actually sending them.  If you get an error it will need fixing.  You now need to schedule that script to be run every day via a crontab, to do so, just install the rapidsms.crontab::

   % crontab rapidsms.crontab
