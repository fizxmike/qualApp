from django.conf.urls.defaults import patterns, include, url
from django.views.generic import DetailView, ListView
from qualApp.models import Qual, Problem

urlpatterns = patterns('accounts.views',
	url(r'^create/$', 'request_account'),
	url(r'^activate/$', 'activate_account'),
)
