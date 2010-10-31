
Migration
=========

Some new features require database changes.  This document details how to apply them.

Backup the DB
-------------

Make sure to do a backup of the current database before starting.  Just shut down the router and server and run::

   % mysqldump -u ubuzima -p ubuzima > backup.sql

SQL Migration
-------------

Some of the SQL tables were changed to deal with new models.  First make sure to shut down rapidsms and the route process.   Then run the migration script::

   % mysql -u ubuzima -p ubuzima < migrate.sql

This will modify a bunch of tables, adding some, renaming others.

Finally, add the new tables that are needed by running syncdb::

   % python rapidsms syncdb

This will probably ask you about deleting unused content types, go ahead and do that.

Date Migration
--------------

One of the things changed was to add a real date field to the Report object.  We need to backfill dates for all reports based on the previous string field.  The migratedates management command does this::

   % python rapidsms migratedates

Reminder Tables
---------------

We added some other new fields for reminders that need to be loaded via fixtures::

   % python rapidsms loaddata reminder_types.json

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

Design
=======

Reminders
---------

Two new models are introduced, ReminderTypes, and Reminders.  ReminderTypes represents the different types of reminders, such as the ANC visits, EDD reminders and inactivity reminders for Reporters.  Within ReminderTypes is the actual english/kinyarwanda/french message that will be sent.  The Reminder object is our record of an actual reminder being sent.

We trigger daily reminders via a simple Django management command that is run daily via crontab.  That command 'checkreminders', simply does a query against all pregnancy reports, then finds those that are within the ranges needed for reminders.  The ranges for each reminder type (ANC2, ANC3, ANC4, EDD) can be found as constants in the Reminder object in models.py.  Reminder messages are sent using an HTTP bridge to the router process, note that the route process must be running (and sending) or reminders will not be sent.  Reminders have a couple day grace period, so if for some reason the router is down one day then they should be sent the next. (the grace period is five days)

Reporter inactivity reminders are done in the same script.  We simply do a query against the last_seen attribute in our Connections table and trigger reminders to supervisors for all reporters which have not had activity in between 30 and 45 days.  Note that a reminder will ONLY be sent after the first inactivity period.

Alerts / Triggers
------------------

Alerting and Advice Texts have been merged into one model and feature, Triggers.  Triggers are simply responses that can be triggered by certain fields being present in a report.  Trigger define what the response is as well as who will be receiving it, which can be the supervisor of the CHW's health clinic, or the supervisor of the hospital if there is one.

Note that Triggers follow some rules to determine which trigger will be sent if more than one matches.  Specifically, triggers that are more specific, matching more than one field, will be prioritized over others.  So if there are two triggers, one for only 'he' and one which matches both 'he' and 'ma', then the latter will be picked over the former.  This allows more specific instructions to be sent as needed.

Message Forwarding
------------------

The message forwarding has been enhanced to include the full text of the fields instead of just the two letter abbreviations.  One drawback to this is that the messages would likely be over the 160 character limit in Kinyarwanda, so the fields are sent in English as per their name field in FieldType.  If desired, a new field could easily be added to FieldType which contains abbreviated (but not two letter) versions of the field names in Kinyarwanda.  You woud simply have to modify the 'summary' method in Report to change this.

Random Improvements
--------------------

Some random improvements made in the user interface:

     1. The message log pane was fixed, it was trying to display all messages, it now display the most recent 200
     2. The patient pane now display reminders which have been sent
     3. The report pane shows the date included in the report as well as the message submission date
     4. The view of triggers is improved

Unit Tests
----------

All new features are extensively unit tested in /ubuzima/tests.py.  Before thinking there is a problem, try to reproduce it by writing a unit test that matches the behavior you are seeing.  Your first step after making any modifications should be running the full test suite.






