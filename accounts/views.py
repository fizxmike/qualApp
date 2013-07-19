# this handles basic user creation
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings

#from django.template import Context, loader
from django.shortcuts import render_to_response
from django.template import RequestContext

#cross site hacking protection
from django.core.context_processors import csrf

#import django models (database)
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core import mail
from accounts.models import CreationRequestForm, CreationActivationForm
#handle forms
from django import forms

#for e-mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def request_account(request):
	ctex = {}
	if request.method == 'POST': # If the form has been submitted...
		form = CreationRequestForm(request.POST) # A form bound to the POST data
		if form.is_valid(): # All validation rules pass	try attempt to create user
			#create user with random password
			randPass = User.objects.make_random_password(length=20)
			newUserName = form.cleaned_data['username']
			emailAddress = newUserName+"@physics.ucsd.edu"
			newUser = User.objects.create_user(newUserName,emailAddress,randPass)
			
			#set account to inactive
			newUser.is_active = False		
			newUser.save()
			
			#send e-mail
			subject, from_email, to = 'UCSD Physics QualApp - account confirmation', 'QualApp <qualapp@cart.ucsd.edu>', emailAddress
			html_content = render_to_string('email/user_activation.html', {'username':newUserName,'key':randPass})
			text_content = strip_tags(html_content) # this strips the html
			msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
			msg.attach_alternative(html_content, "text/html")
			msg.send()

			ctex.update({'success':('A confirmation e-mail has been sent to %s@physics.ucsd.edu' % request.POST['username'] )})
	else:
		form = CreationRequestForm()
	
	ctex.update({'form':form})
	ctex.update(csrf(request))		
	return render_to_response('accounts/create_user.html',RequestContext(request,ctex))

#TODO: implement a banned user list

def activate_account(request):
	ctex={}
	if request.method == 'POST':
		form = CreationActivationForm(request.POST)
		if form.is_valid():
			if form.cleaned_data['new_password'] == form.cleaned_data['verify_password']:
				newUser = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['key'])
				
				#only activate if user is not banned
				if not newUser.groups.filter(name='banned').count():
					#update password
					newUser.set_password(form.cleaned_data['new_password'])
					
					#set account to active
					newUser.is_active = True

					#set group to "contributor"
					group = Group.objects.get(name='contributor')
					newUser.groups.add(group.id)	
					
					newUser.save()
					
					login(request,newUser)
					#redirect to homepage
					
					return HttpResponseRedirect('/qualApp/')
				else:
					return HttpResponse('You have been banned. Please contact the site administrator.')
			else:
				ctex.update({'error_message':'The passwords you entered did not match, please try again.'})
		else:
			ctex.update({'error_message':'There were errors in your submission...'})
	else:
		form = CreationActivationForm()
	
	ctex.update({'form':form})
	ctex.update(csrf(request))		
	return render_to_response('accounts/activate_user.html',RequestContext(request,ctex))
	
	
