#from django.conf.urls.defaults import patterns, include, url
from django.conf.urls.defaults import *
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from django.db.models.loading import cache as model_cache
if not model_cache.loaded:
    model_cache.get_models()

admin.autodiscover()

dev_mode = True
url_prefix = "qualApp"

if not dev_mode:
	url_prefix = '' #this is blank when running from Apache


urlpatterns = patterns('',
	# Examples:
	# url(r'^$', 'qualPrep.views.home', name='home'),
	
	url(r'^'+url_prefix+'/*', include('qualApp.urls')),
	
	# Uncomment the admin/doc line below to enable admin documentation:
	# url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

	# Uncomment the next line to enable the admin:
	url(r'^admin/', include(admin.site.urls)),

	url(r'^accounts/', include('accounts.urls')),
	url(r'^accounts/login/$', 'django.contrib.auth.views.login',{'redirect_field_name':'continue'}),
	#url(r'^login$', 'sign_in'),
	url(r'^accounts/logout/$', 'django.contrib.auth.views.logout',{'redirect_field_name':'continue'}),
	url(r'^accounts/password/$', 'django.contrib.auth.views.password_change',{'post_change_redirect':'/qualApp/'}),

)


#serve files when in dev mode
import sys
if 'runserver' in sys.argv:
	from django.conf import settings
	urlpatterns += patterns('',	url(r'^files/(.*)$',
		'django.views.static.serve',
		kwargs={'document_root': str(settings.PATH_TO_PROJECT+'db.files')}), )
