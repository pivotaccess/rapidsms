
# switch to ubuzima
use ubuzima;

# rename our old date column to date_string
alter table ubuzima_report change column date date_string varchar(10) default NULL;

# add a date column to ubuzima_report that is a real date
alter table ubuzima_report add column date date default null after date_string;

# rename our advice texts table to triggered_texts
rename table ubuzima_advicetext to ubuzima_triggeredtext, ubuzima_advicetext_triggers to ubuzima_triggeredtext_triggers;

# remap our association
alter table ubuzima_triggeredtext_triggers change column advicetext_id triggeredtext_id int;

# add two fields for type and destination
alter table ubuzima_triggeredtext add column destination varchar(3) default 'CHW' after name;

