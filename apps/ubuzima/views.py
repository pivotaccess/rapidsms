#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseServerError
from django.template import RequestContext
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404
from django.db import transaction

from rapidsms.webui.utils import *
from reporters.models import *
from reporters.utils import *
from ubuzima.models import *

@permission_required('reports.can_view')
@require_GET
def index(req):
    return render_to_response(req,
        "ubuzima/index.html", {
        "reports": paginated(req, Report.objects.all(), prefix="rep")
    })

@require_http_methods(["GET"])
def by_patient(req, pk):
    patient = get_object_or_404(Patient, pk=pk)
    reports = Report.objects.filter(patient=patient)
    
    return render_to_response(req,
                              "ubuzima/patient.html", { "patient":    patient,
                                                        "reports":    paginated(req, reports, prefix="rep") })
    
@require_http_methods(["GET"])
def by_type(req, pk):
    report_type = get_object_or_404(ReportType, pk=pk)
    reports = Report.objects.filter(type=report_type)
    
    return render_to_response(req,
                              "ubuzima/type.html", { "type":    report_type,
                                                     "reports":    paginated(req, reports, prefix="rep") })
    
    pass
    
@require_http_methods(["GET"])
def by_reporter(req, pk):
    reporter = Reporter.objects.get(pk=pk)
    reports = Report.objects.filter(reporter=reporter)
    
    return render_to_response(req,
                              "ubuzima/reporter.html", { "reports":    paginated(req, reports, prefix="rep"),
                                                         "reporter":   reporter })
