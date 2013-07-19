from django.db import models

#imports for member methods:
import datetime
from django.core.exceptions import ValidationError

#for authentication
from django.contrib.auth.models import User



#input validators
def validate_year(value):
	if (value < 1980) | (value > datetime.datetime.now().year):
		raise ValidationError(u'%s is not a valid year (Valid Range: 1980 to Present Year)' % value)


def validate_pdf(value):
	if ('.pdf' in value.name) == False & ('.PDF' in value.name) == False:
		raise ValidationError(u'Please upload a .pdf file')	

#app objects
class Qual(models.Model):
	#choices for qual terms
	QUAL_TERM_CHOICES = (
		('FA', 'Fall'),
		('SP', 'Spring'),
	)

	term = models.CharField(
		max_length=2,
		choices=QUAL_TERM_CHOICES
	)
	year = models.PositiveIntegerField(
		help_text='Any 4-digit year since 1980',validators=[validate_year]
	)
	pdf = models.FileField(
		upload_to='qualApp/qual_pdf',
		validators=[validate_pdf],
		blank=False #require the PDF for the qual
	)
	def __unicode__(self):
		return (u'%s %s' % (self.get_term_display(), self.year))
	#some meta data
	class Meta:
		unique_together = (("term", "year"),) #assure no duplicate quals

#the problem table object
#an actual qual problem with meta-data associated to an uploaded .png (later .pdf or just TeX)
class Problem(models.Model):
		
	#fixed options for qual subjects:
	PROB_SUBJ_CHOICES = (
		('CM', 'Classical Mechanics'),#0
		('QM', 'Quantum Mechanics'),#4
		('SM', 'Statistical Mechanics & Thermodynamics'),#5
		('EM', 'Electricity and Magnetism'),#1
		('MM', 'Math Methods, Physical Estimates, General'),#3
	)

	#fixed options for qual levels (days):
	PROB_LEVEL_CHOICES = (
		('U', 'Undergraduate'),
		('G', 'Graduate'),
	)
	
	#returns the human-readable portion of the level choice:
	def level_readable(self):
		return (u'%s' % self.get_level_display())
	level_readable.short_description = 'Level (Qual Day)'

	#member values (DB table columns)
	qual = models.ForeignKey(Qual) #maps to a row in the Qual table
	level = models.CharField(
		max_length=1,
		choices=PROB_LEVEL_CHOICES
	)
	subject = models.CharField(
		max_length=2,
		choices=PROB_SUBJ_CHOICES
	)
	topic = models.CharField(
		max_length=300,
		help_text="Ex: 'some topic - a brief description of the problem'"
	)
	problem_pages = models.CommaSeparatedIntegerField(
		max_length=20,
		help_text="Reference page(s) in qual PDF. (Examples: '19' for single page, '20,21,22' for page range)"
	)
	solution_pages = models.CommaSeparatedIntegerField(
		max_length=20,
		help_text="Reference page(s) in qual PDF. (Examples: '19' for single page, '20,21,22' for page range)",
		blank=True
	)
	problem_pdf = models.FileField(
		upload_to='qualApp_processed/problems',
		validators=[validate_pdf],
		blank=True #generated on demand
	)
	solution_pdf = models.FileField(
		upload_to='qualApp_processed/solutions',
		validators=[validate_pdf],
		blank=True #generated on demand
	)
	problem_pic = models.ImageField( #path to uploaded file (with image meta-data)
		upload_to='qualApp_processed/problems',
		blank=True,
	)
	solution_pic = models.ImageField( #path to uploaded file (with image meta-data)
		upload_to='qualApp_processed/solutions',
		blank=True,
	)
	duplicate = models.BooleanField(
		help_text="Check here if you notice this is a duplicate of a question from a different year's qual"
	)	
	problem_TeX = models.TextField( #not implemented yet
		max_length=2000,
		blank=True,
		help_text="Use this field for short description as TeX (not yet implemented)"
	)
	solution_TeX = models.TextField( #not implemented yet
		max_length=2000,
		blank=True,
		help_text="Use this field for short description as TeX (not yet implemented)"
	)
	
	def __unicode__(self):
		return (u'%s%s: %s' % (self.level, self.subject, self.topic))

	def subject_readable(self):
		return self.get_subject_display()
	subject_readable.short_description = 'Subject'


class Solution(models.Model):

	problem = models.ForeignKey(Problem)

	user = models.ForeignKey(User)

	image = models.ImageField(
		upload_to='qualApp/student_solutions',
		blank=True,
		help_text = "upload an image of your solution (optional)",
	)
	
	date_modified = models.DateTimeField(auto_now = True)
	date_created = models.DateTimeField(auto_now_add = True)
	private = models.BooleanField(
		default=False,
		help_text = "Check this box to hide this solution from others.",
	)
	solution_TeX = models.TextField(
		max_length=2000,
		blank=True,
		help_text="Enter solution (optional), LaTeX/TeX and ASCIIMath input is supported.",
		verbose_name="Solution"
	)
	def __unicode__(self):
		return (u'%s: %s (%s)' % (self.user.username, self.problem, self.problem.qual))

class Note(models.Model):

	#fixed options for qual subjects:
	PROB_SUBJ_CHOICES = (
		('CM', 'Classical Mechanics'),#0
		('QM', 'Quantum Mechanics'),#4
		('SM', 'Statistical Mechanics & Thermodynamics'),#5
		('EM', 'Electricity and Magnetism'),#1
		('MM', 'Math Methods, Physical Estimates, General'),#3
	)
	user = models.ForeignKey(User)
	
	subject = models.CharField(
		max_length=2,
		choices=PROB_SUBJ_CHOICES
	)
	
	topic = models.CharField(
		max_length=300,
		help_text="A title for your notes."
	)
	
	#add pdf later
	#image = models.ImageField(
	#	upload_to='qualApp/student_solutions',
	#	blank=True,
	#	help_text = "upload an image of your solution (optional)",
	#)
	
	date_modified = models.DateTimeField(auto_now = True)
	date_created = models.DateTimeField(auto_now_add = True)
	private = models.BooleanField(
		default=False,
		help_text = "Check this box to hide these notes from others.",
	)
	
	TeX = models.TextField( #not implemented yet
		max_length=200000,#200KB #should we really enforce this?
		blank=False,
		help_text="Enter notes, LaTeX/TeX math and ASCIIMath code input is supported.",
		verbose_name="TeX Notes"
	)

	def __unicode__(self):
		return (u'(%s) %s: %s' % (self.user.username, self.get_subject_display(), self.topic))
	
