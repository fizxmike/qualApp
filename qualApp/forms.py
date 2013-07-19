#qualApp forms
#create related forms
from django.forms import ModelForm, ValidationError

#import our models:
from qualApp.models import Qual, Problem, Solution, Note
from django.forms.widgets import RadioSelect, TextInput, ClearableFileInput

#create form from model
class PartialProblemForm(ModelForm):
	error_css_class = 'error'
	required_css_class = 'required'

	class Meta:
		model = Problem
		fields = ('level','subject','topic','problem_pages','solution_pages')
		#widgets = {
            #'level': RadioSelect(),
            #'topic': TextInput(attrs={'size': 40}),
        #}
        
#create form from model
class PartialSolutionForm(ModelForm):
	error_css_class = 'error'
	required_css_class = 'required'

	class Meta:
		model = Solution
		fields = ('image','private','solution_TeX')
		#widgets = {
		#	'png': ClearableFileInput()
		#}
	#make sure text or image is supplied
	def clean(self):
		cleaned_data = self.cleaned_data
		image = cleaned_data.get("image")
		tex = cleaned_data.get("solution_TeX")

		if not image and not tex:
			# Only do something if both fields are valid so far.
			raise ValidationError("Please either upload a picure or type something in the text box.")
			
		# Always return the full collection of cleaned data.
		return cleaned_data		

#create form from model
#class PartialNoteForm(ModelForm):
	#error_css_class = 'error'
	#required_css_class = 'required'

	#class Meta:
		#model = Note
		#fields = ('image','private','solution_TeX')


class ProblemEditForm(ModelForm):
	error_css_class = 'error'
	required_css_class = 'required'
	
	class Meta:
		model = Problem
		fields = ('level','subject','topic','problem_pages','solution_pages')

class NoteEditForm(ModelForm):
	error_css_class = 'error'
	required_css_class = 'required'
	
	class Meta:
		model = Note
		fields = ('subject','topic','TeX','private')


#to not allow PDF to be changed
class QualEditForm(ModelForm):
	class Meta:
		model = Qual
		exclude = ('pdf')

#to not allow PDF to be changed
class QualCreateForm(ModelForm):
	class Meta:
		model = Qual
