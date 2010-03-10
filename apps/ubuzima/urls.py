#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
import ubuzima.views as views

urlpatterns = patterns('',
    url(r'^ubuzima$', views.index),
    url(r'^ubuzima/reporter/(?P<pk>\d+)$', views.by_reporter),
    url(r'^ubuzima/patient/(?P<pk>\d+)$', views.by_patient),
    url(r'^ubuzima/type/(?P<pk>\d+)$', views.by_type),
    url(r'^ubuzima/alerts$', views.alerts),
    url(r'^ubuzima/alert/(?P<pk>\d+)$', views.alert)
)
