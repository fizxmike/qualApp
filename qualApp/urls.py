
from django.conf.urls.defaults import patterns, include, url
from django.views.generic import DetailView, ListView, edit
from qualApp.models import Qual, Problem, Solution, Note
#from qualApp.forms import QualEditForm
from qualApp.views import QualEditView, ProblemEditView, SolutionEditView, NoteEditView



urlpatterns = patterns('qualApp.views',
	#-----[qualApp]/
	url(r'^$','index'), #home page
	#-----[qualApp]/quals/-----
	#default index is qual list view:
	url(r'^quals/$',
		ListView.as_view(
			queryset=Qual.objects.order_by('-year','term'),
			#context_object_name='qual_list', #default
			#template_name='qualApp/qual_list.html' #default
		)
	),
	url(r'^quals/add$', 'add_qual'),
	#url(r'^quals/add$',
		#edit.CreateView.as_view(
			#model=Qual,
			#template_name="qual_form.html", #default
		#)
	#),
	
	url(r'^quals/(?P<pk>\d+)/edit$',
		QualEditView.as_view(
				template_name="qualApp/qual_editForm.html", #special form for editing
				#success_url="/qualApp/quals/", #back to qual list
		),{"success_root":"/qualApp/quals/"}, #kwargs['pk'] will be appended on success
	),

	url(r'^quals/(?P<qual_id>\d+)/browse$','browse'),
	url(r'^quals/(?P<qual_id>\d+)/tag$','tag_problem'),

	url(r'^quals/(?P<qual_id>\d+)/changePage$','changePage'),	

	#url(r'^quals/(?P<pk>\d+)/$',
		#DetailView.as_view(
			#model=Qual, #object name becomes qual?
			##template_name='qualApp/qual_detail.html' #default
		#)
	#),
	url(r'^quals/(?P<qual_id>\d+)/$','qual_detail'),

	#-----[qualApp]/problems/-----
	url(r'^problems/$',
		ListView.as_view(
			queryset=Problem.objects.order_by('-id'),
			#context_object_name='qual_list', #default
			#template_name='qualApp/qual_list.html' #default
		),
	),



	#quick sorting
	url(r'^problems/byLevel$',
		ListView.as_view(
			queryset=Problem.objects.order_by('level','subject'),
			#context_object_name='qual_list', #default
			#template_name='qualApp/qual_list.html' #default
		)
	),
	
	url(r'^problems/bySubject$',
		ListView.as_view(
			queryset=Problem.objects.order_by('subject','level'),
			#context_object_name='qual_list', #default
			#template_name='qualApp/qual_list.html' #default
		)
	),

	url(r'^problems/search$','problem_search'),
	url(r'^problems/random$','random_problem'),

	url(r'^problems/(?P<pk>\d+)/$','problem_detail'),
	url(r'^problems/(?P<pk>\d+)/crop$','crop_image'),

	url(r'^problems/add$', 'add_problem'),
	url(r'^problems/(?P<pk>\d+)/edit$',
			ProblemEditView.as_view(
			#	template_name="qualApp/problem_editForm.html", #using default: qualApp/problem_form.html
			),{"success_root":"/qualApp/problems/"}, #kwargs['pk'] will be appended on success
		),
	url(r'^problems/(?P<pk>\d+)/add_solution$','add_solution'),
	url(r'^solutions/(?P<pk>\d+)/edit$',
			SolutionEditView.as_view(
			),{"success_root":"/qualApp/problems/"}, #kwargs['pk'] will be appended on success
		),
	#add a solution to a problem from problem detail view
	#include list of solutions in detail

	url(r'^solutions/$',
		ListView.as_view(
			queryset=Solution.objects.filter(private=False).order_by('user'),
		),
	),
	url(r'^solutions/user(?P<uid>\d+)$', 'user_solutions'),	



	url(r'^notes/$',
		ListView.as_view(
			queryset=Note.objects.filter(private=False).order_by('subject'),
		),
	),
	url(r'^notes/create$','add_note'),
	url(r'^notes/(?P<pk>\d+)/$',
		DetailView.as_view(
			model=Note, #object name becomes note?
			#template_name='qualApp/qual_detail.html' #default
		)
	),
	url(r'^notes/(?P<pk>\d+)/edit$',
			NoteEditView.as_view(
			),{"success_root":"/qualApp/notes/"}, #kwargs['pk'] will be appended on success
	),
	url(r'^notes/user(?P<uid>\d+)$', 'user_notes'),
	
	
	#-----JUNK/DEV-----
#	url(r'^solutions/(?P<pk>\d+)/preview$','MathJaxConf'),
	#url(r'^quals/(?P<qual_id>\d+)/$', 'detail'),
	url(r'^(?P<qual_id>\d+)/test/$', 'test'),



)

#dev serving:
import sys
from django.conf import settings
if 'runserver' in sys.argv or 'runserver_plus':
	urlpatterns += patterns('', url(r'^'+settings.MEDIA_URL+'(.*)$', 'django.views.static.serve', kwargs={'document_root': settings.MEDIA_ROOT}), )
	#os.path.join(settings.PROJECT_PATH, 'media')}), )
	
	
	
