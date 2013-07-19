#from django.db import models
#from django.contrib.auth.forms import UserCreationForm #for authentication
from django.contrib.auth.models import User
#create related forms
from django import forms

#create form from model
class CreationRequestForm(forms.Form):
	username = forms.RegexField(label='e-mail:',regex=r'[A-Za-z0-9_]*',max_length=20, min_length=4,help_text='@physics.ucsd.edu')
		
	def clean_username(self): #called after catch-all "clean()"
		#make lowercase!
		if not self.errors:
			uname = self.cleaned_data['username'].lower()
			try:
				user = User.objects.get(username=uname)
			except User.DoesNotExist:
				return uname
			raise forms.ValidationError(u'The user "%s" already exists.' % uname )


class CreationActivationForm(forms.Form):
	username = forms.RegexField(regex=r'[A-Za-z0-9_]*',max_length=20, min_length=4)
	key = forms.CharField(max_length=25)
	new_password = forms.CharField(label='New Password (at least 6 characters)',widget=forms.PasswordInput,max_length=50,min_length=6,help_text="Warning: For your own safety DO NOT use the same password as your physics account.")
	verify_password = forms.CharField(label='Verify New Password',widget=forms.PasswordInput,max_length=50,min_length=6)
	
	
	def clean_username(self):
		if not self.errors:
			uname = self.cleaned_data['username']
			try:
				user = User.objects.get(username=uname)
				return uname
			except User.DoesNotExist:
				raise forms.ValidationError(u'The user "%s" does not exist or was not created properly. Check confirmation e-mail, capitalization counts!' % uname )
		
	def clean_key(self):
		if not self.errors:
			key = self.cleaned_data['key']
			username = self.clean_username
			user = User.objects.get(username=username)
			if user.check_password(key):
				return key
			else:
				raise forms.ValidationError(u'Invalid Key')
