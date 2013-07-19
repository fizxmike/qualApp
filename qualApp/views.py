#---------DJANGO MODULES----------
import time

#this is the main code for the web app
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings

#from django.template import Context, loader
from django.shortcuts import render_to_response
from django.template import RequestContext

#cross site hacking protection
from django.core.context_processors import csrf

#url reverse lookup
#from django.core.urlresolvers import reverse, reverse_lazy

#used to update an ImageFile model object
from django.core.files import File
#file system to store data in MEDIA_URL etc:
from django.core.files.storage import FileSystemStorage as fs
#from django.core.files.storage import default_storage

#import django models (database)
from django.contrib.auth.models import User #for authentication
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required

from django.utils.decorators import method_decorator

#import our models and forms:
from qualApp.models import Qual, Problem, Solution, Note
from qualApp.forms import QualEditForm, QualCreateForm,\
                           PartialProblemForm, ProblemEditForm, PartialSolutionForm,\
                           NoteEditForm
#handle forms:
from django import forms

#generic views:
from django.views.generic.edit import UpdateView, CreateView

#---------OTHER LIBS--------------
#import pdf library
from pyPdf import PdfFileWriter, PdfFileReader

#test imageMagick bindings
import PythonMagick as Magick
#import pgmagick as Magick

#fs ops
import os
import subprocess
import shutil

#time
from datetime import timedelta, date, datetime

#---------CODE--------------------
#__GLOBALS:
REPARSE_FULL_TEXT = True



def index(request):
	#count
	qual_count = len(Qual.objects.all())
	probs = Problem.objects.all()
	solns = Solution.objects.filter(private=False)
	notes = Note.objects.filter(private=False)
	
	today = datetime.today()

	#process alerts for recently updated items
	try:
		soln_delta = (today - solns.latest('date_created').date_created)
			
		if soln_delta.days == 0:
			hours = soln_delta.seconds/3600
			soln_recent = str(hours) + " hour"
			if hours != 1:
				soln_recent += "s"
		else:
			soln_recent = str(soln_delta.days) + " day"
			if soln_delta.days != 1:
				soln_recent += "s"
	except:
		soln_recent = 'zero days'
	
	
	try:
		note_delta = (today - notes.latest('date_created').date_created)

		if note_delta.days == 0:
			hours = note_delta.seconds/3600
			note_recent = str(hours) + " hour"
			if hours != 1:
				note_recent += "s"
		else:
			note_recent = str(note_delta.days) + " day"
			if note_delta.days != 1:
				note_recent += "s"
	except:
		note_recent = 'zero days'
	
		
	qualDate = datetime(2013,9,19,12,0,0) 	#todo: convert this in an object model/database table
	delta = qualDate - today
	return render_to_response('qualApp/index.html',
		RequestContext(request,{
			"days_to_qual": delta.days,
			"seconds_to_qual":delta.seconds,
			"qual_count":qual_count,
			"problem_count":len(probs),
			"solution_count":len(solns),
			"solution_recent":soln_recent,
			"note_count":len(notes),
			"note_recent":note_recent,
		})
	)

#	t = loader.get_template('qualApp/index.html')
#	c = Context({
#	  'qual_list': qual_list,
#	})
#	return HttpResponse(t.render(c))

def splicePDF(qual_pdf,target_pages,target_path):
	# qual_pdf is input file path
	# target_pages is a tuple of page numbers to be used to generate new pdf
	# target_path is the path of the derived pdf
	
	#initialize pdf library objects:
	outpdf = PdfFileWriter()
	inpdf = PdfFileReader(file(qual_pdf, "rb"))
	
	try: #loop over pages
		for page in target_pages:
			outpdf.addPage(inpdf.getPage(int(page-1))) #subtract one because pages start at 0 in pdf library
	except: #just one page
		outpdf.addPage(inpdf.getPage(int(target_pages-1)))

	outputStream = file(target_path, "wb")
	outpdf.write(outputStream)
	outputStream.close()	

def pdf2text(source_pdf,target_pages):
	pdf = PdfFileReader(file(source_pdf, "rb"))
	text_string = ''
	try: #loop over pages
		for page in target_pages:
			text_string += pdf.getPage(int(page-1)).extractText()
			
	except: #just one page
		text_string += pdf.getPage(int(target_pages-1)).extractText()
	
	return text_string

def pdf2png(source_path,target_path, trim=True, transparent=False):
	#source_path is a png file
	#target_path is a path to a .png file (with extension included)
	
	text_string = ''
	
	pdf = PdfFileReader(file(source_path))
	#if len(pdf.pages) > 1:

	for i in range(0,len(pdf.pages)):
		tmp_path = target_path[0:len(target_path)-4]+str(i)
		f = file(tmp_path+".pdf","w")
		tmpPdf = PdfFileWriter()
		tmpPdf.addPage(pdf.getPage(i))
		#test text extraction
		#text_string += pdf.getPage(i).extractText() + "\n"
		tmpPdf.write(f)
		f.close()
		#render png from using image magic
		img = Magick.Image()
		img.density("100") #pixels per inch
		img.read(tmp_path+".pdf") #read in pdf file
		img.trim() #autocrop
		#img.transparent("white") #make white = transparent
		#save the largest value of columns
		img.quality(100) #full compression
		img.magick('PNG')
		img.write(tmp_path+".png")

	#now use imagemagick CLI to tile images together (cound not find it in PythonMagick, might be in PythonMagickWand?)
	#ImageMagick CLI is better documented anyway (-background none preserves transparency)
	subprocess.call("montage -border 2 -bordercolor none -background white -geometry +0+0 -tile 1x "+target_path[0:len(target_path)-4]+"[0-9]*.png "+target_path,shell=True)

	#cleanup files
	for i in range(0,len(pdf.pages)):
		tmp_path = target_path[0:len(target_path)-4]+str(i)
		os.remove(tmp_path+".pdf")
		os.remove(tmp_path+".png")
			
	#else: #single page
		#img = Magick.Image()
		#img.density("100") #pixels per inch
		#img.read(str(source_path)) #read in pdf file
		#img.trim() #autocrop 		
		##img.transparent("white") #make white = transparent
		#img.quality(100) #full compression
		#img.magick('PNG')
		#img.write(str(target_path))	

	if trim: #crop all white space
		pass#subprocess.call("convert -trim "+target_path+" "+target_path, shell=True)
	
	#return text_string + str(len(text_string))



def browse(request,qual_id):
	#get page number from request
	page = request.GET.get('page',1)
	
	#create/get the png path
	png_path = get_page_url(qual_id,page)
	
	#return blank image if problem
	if png_path:
		full_url = settings.MEDIA_URL+png_path
	else:
		full_url = ''
			
	return render_to_response('qualApp/tag_detail.html',
		RequestContext(request,{
			'qual':Qual.objects.get(id=qual_id),
			'page':page,
			'page_url': full_url,
			#'tot_pages': totPages,
			#'error_message':error_message,
		})#template_keyword:local_variable
	)


def get_recentPage(qual_id,inKey):
	"""
	get the last (most recent) saved problem or solution page in database for a given qual
	"""
	probs = Problem.objects.filter(qual=qual_id).order_by('-id')
	if probs:
		tmpString = probs[0].__dict__[inKey]
		if tmpString:
			pageList = eval(tmpString)
			if type(pageList) == int:
				return pageList
			else:
				return pageList[len(pageList) - 1]
	return 1

@login_required(login_url='/qualApp/accounts/login/',redirect_field_name='continue')
def tag_problem(request,qual_id):
	
	getQual = Qual.objects.get(id=qual_id)
	request.session['tag_mode'] = "on"
	
	if request.method == 'POST': # If the form has been submitted...
		tempProb = Problem(qual=getQual) # initialize a problem with the apropriate qual
		form = PartialProblemForm(request.POST, instance=tempProb) # A form bound to the POST data, using above instance
		if form.is_valid(): # All validation rules pass
			if request.user.has_perm('qualApp.add_problem'):
				newProb = form.save() #finally save the row in the DB
				return HttpResponseRedirect('../../problems/'+str(newProb.id)+'/?tagged=1') # Redirect after POST
			else:
				return HttpResponse('You do not have permissions to add a problem, please login or register.')
		#else:
			#pass
			#this doesn't work right since problem_pages could be a list...
		#	ProbPage = request.POST.get('page',get_recentPage(qual_id,'problem_pages'))
	#else:
	#get recent values of solution and problem pages
	recent_solution = get_recentPage(qual_id,'solution_pages')
	recent_problem = get_recentPage(qual_id,'problem_pages')
	
	#get page number from request
	ProbPage = request.GET.get('page',False)
	if ProbPage: #if page was in the request
		#create form with page number
		form = PartialProblemForm(initial={'problem_pages':ProbPage}) # An unbound form
	else:
		#create empty form
		form = PartialProblemForm()
		#set problem page same as recent (default)
		ProbPage = recent_problem
			
	#this is done always (except on sucessful post)
	png_path = get_page_url(qual_id,ProbPage)

	#return blank image if problem
	if png_path:
		full_url = settings.MEDIA_URL+png_path
	else:
		full_url = ''

	#create a csrf context and response
	ctex = {'form':form,
			'qual':getQual,
			'page':ProbPage, #page to display image for
			'recent_problem':recent_problem, #recent solution page (for jump to)
			'recent_solution':recent_solution, #recent solution page (for jump to)
			'page_url': full_url,}
	ctex.update(csrf(request))
	return render_to_response('qualApp/tag_detail.html',RequestContext(request,ctex))

def changePage(request,qual_id):
	#handles request from javascript to get url for a page
	
	#get page number from request
	page = request.GET.get('page',1)
	
	#create/get the png path
	png_path = get_page_url(qual_id,page)
	
	#build response object
	resp = HttpResponse()
	
	#return blank image if problem
	if png_path:
		resp.status_code = 200
		resp.write(settings.MEDIA_URL+png_path)
	else:
		resp.status_code = 400
		resp.write('some error generating png')

	return resp
	 
	 
def get_page_url(qual_id,page):
	#create a png in media root based on qual id and page number
	#returns url

	png_path = "qualApp/pages/_page_"+str(qual_id)+"_"+str(page)+".png"
	
	#check directory exists, if not create it:
	if not os.path.isdir(os.path.dirname(settings.MEDIA_ROOT+png_path)):
		os.mkdir(os.path.dirname(settings.MEDIA_ROOT+png_path))
	
	if not os.path.isfile(settings.MEDIA_ROOT+png_path):	
		qual = Qual.objects.get(id=qual_id) #maybe try in case qual is not found
		inpdf = PdfFileReader(file(qual.pdf.path, "rb"))
		
		#if page is in range
		totPages = len(inpdf.pages)
		if totPages >= int(page) and int(page) > 0:
			#create the page
			pdf_path = settings.TEMPORARY_ROOT+"_page"+str(qual_id)+"_"+str(page)+".pdf"
			splicePDF(qual.pdf.path,int(page),pdf_path)
			#pdf_path = settings.TEMPORARY_ROOT+"_page"+str(qual_id)+"_"+str(page)+".png" 		
			pdf2png(pdf_path, settings.MEDIA_ROOT+png_path)
			#save to storage
			
			#delete tmp file
			os.remove(pdf_path)
			return png_path	
		else:
			return ""
			#error_message = "outOfRange"
	else:
		return png_path
		#File Exists

def fieldAndFileExist(fileFieldObj):
	if fileFieldObj: #if populated
		if not os.path.isfile(fileFieldObj.path): #check existence of file
			return False #when file does not exist
	else: #field is not populated
		return False
	return True #field is populated and file exists.

def subjectsKey(prob):
	my_order = ['CM','EM','QM','SM','MM']
	return my_order.index(prob.subject)

def qual_detail(request,qual_id):
	from operator import attrgetter
	
	qual = Qual.objects.get(id=qual_id)
	
	problem_set = qual.problem_set.all() #order_by('-level')#,'subject')
	
	problem_set_sorted = sorted(problem_set,key=subjectsKey)
	problem_set_sorted.sort(key=attrgetter('level'),reverse=True)
	
	#render page and include media url to pdf
	return render_to_response('qualApp/qual_detail.html',
		RequestContext(request,{
			'problem_set':problem_set_sorted,
			'qual':qual,
		})#template_keyword:local_variable
	)


def findPrevAndNextProbInQual(prob):#find previous and next question in qual:
	from operator import attrgetter
	
	qual_probs = prob.qual.problem_set.all() #order_by('-level')#,'subject')
	qual_probs = sorted(qual_probs,key=subjectsKey)
	qual_probs.sort(key=attrgetter('level'),reverse=True)

	prob_ids = [p.id for p in qual_probs] #eval(str(qual_probs.values_list('id',flat=True)))
	
	#find index of current problem:
	this_idx = prob_ids.index(prob.id)
	
	#if last, return empty value for next_id
	if this_idx + 1 == len(prob_ids):
		next_id = ''
	else:
		next_id = str(prob_ids[this_idx+1])
	
	#if first, return empyt value for prev_id
	if this_idx == 0:
		prev_id = ''
	else:
		prev_id = str(prob_ids[this_idx-1])
		
	#return tuple:
	return prev_id, next_id
	

def problem_detail(request,pk):
	#special cases that might not be set before context is rendered
	text_string = ''
	solution_user = ''
	solution_user_id = ''
	solution_text = ''
	sol_url = ''
	pic_url = '' #should change this variable name to prob_url
	
	if request.user.is_authenticated:
		#handle changing session variables
		if request.GET.get("show_solution","no-change") == "true":
			#set the session variable
			request.session["show_solution"] = "true";
		
		if request.GET.get("show_solution","no-change") == "false":
			#set the session variable
			request.session["show_solution"] = "false";
		
		#turn off tagging mode (is only set if user is logged in)
		if request.GET.get("tag_mode","") == "off":
			request.session["tag_mode"] = "off"
			
		
		#manage local variables
		if request.session.get("show_solution","false") == "true":
			show_solution = True;
		else:
			show_solution = False;
	else:
		if request.GET.get("show_solution","false") == "true":
			show_solution = True;
		else:
			show_solution = False;

	#problem object:
	prob = Problem.objects.get(id=pk)
	
	#solutions list (non-private):
	##TODO: allow owners of problems to view thier own solution in the dropdown
	solution_list = prob.solution_set.filter(private=False)
	solution_id = request.GET.get('sol',False)
	
	#get previous and next question in qual:
	prob_id_prev,prob_id_next = findPrevAndNextProbInQual(prob)

	if request.user.is_authenticated and request.GET.get("update",False): #default to False if "update" is not passed
		#delete files/fields on update based on session variable
		
	#FIX: update does not work then there is no tagged solution for a problem and show_solution is set!!
		if show_solution:
			if prob.solution_pdf:
				prob.solution_pdf.delete()
			if prob.solution_pic:
				prob.solution_pic.delete()
		else:
			if prob.problem_pdf:
				prob.problem_pdf.delete()
			if prob.problem_pic:
				prob.problem_pic.delete()
	
	#show a solution instead of other things
	if solution_id:
		#set the session variable
		request.session["show_solution"] = "true";
		show_solution = True
		
		sol = Solution.objects.get(id=solution_id)
		solution_user = str(sol.user.username).upper()
		solution_user_id = sol.user.id
		#for now we will only show the problem text when there is no uploaded image:
		if sol.image:
			sol_url = sol.image.url
		#else: might as well show the problem anyway, even if there is a pic of the solution!
		##TODO: add an option to the solution form (checkbox) to allow user to disable/enable problem pic
		pic_url = prob.problem_pic.url+"?ts=" + str(int( os.path.getmtime(prob.problem_pic.path) ))

		if sol.solution_TeX:
			solution_text = sol.solution_TeX
			
	elif show_solution and prob.solution_pages: #default to false (skip to problem only display)
		#if the solution fields are not populated, poputlate them
		#then save objects to database
		
		#take care of case where database is populated but file does not exist:
		#this takes care of one reason "update" is used, perhaps change to "purge" or "redraw" ...

		if not fieldAndFileExist(prob.solution_pdf):
			pdf_path = settings.TEMPORARY_ROOT+"_solution"+str(prob.id)+".pdf"
			splicePDF(prob.qual.pdf.path,eval(prob.solution_pages),pdf_path) #eval csv field
			#save pdf to database
			f = open(pdf_path, 'r')
			prob.solution_pdf = File(f)
			prob.save() #update database here
			f.close()
			os.remove(pdf_path) #cleanup

		if not fieldAndFileExist(prob.solution_pic):
			png_path = settings.TEMPORARY_ROOT+"_solution"+str(prob.id)+".png"
			text_string = pdf2png(prob.solution_pdf.path,png_path)
			#save png to database				
			f = open(png_path, 'r')
			prob.solution_pic = File(f)
			prob.save() #update database here
			f.close()
			os.remove(png_path) #cleanup
		#in case OS doesn't know file is there yet
		try:	
			pic_url = prob.solution_pic.url+"?ts=" + str(int( os.path.getmtime(prob.solution_pic.path) ))
		except:
			pic_url = prob.solution_pic.url
	else:
		#if the problem fields are not populated, populate them
		#then save objects to database	
		if not fieldAndFileExist(prob.problem_pdf):
			pdf_path = settings.TEMPORARY_ROOT+"_problem"+str(prob.id)+".pdf"
			splicePDF(prob.qual.pdf.path,eval(prob.problem_pages),pdf_path) #eval csv field
			#save pdf to database
			f = open(pdf_path, 'r')
			prob.problem_pdf = File(f)
			prob.save() #update database here
			f.close()
			os.remove(pdf_path) #cleanup
				
		if not fieldAndFileExist(prob.problem_pic):
			png_path = settings.TEMPORARY_ROOT+"_problem"+str(prob.id)+".png" 
			text_string = pdf2png(prob.problem_pdf.path, png_path)
			#also save updated png image file in database
			f = open(png_path, 'r')
			prob.problem_pic = File(f)
			prob.save() #update database here
			f.close()
			os.remove(png_path) #cleanup
		#slow OS?
		try:
			pic_url = prob.problem_pic.url+"?ts=" + str(int( os.path.getmtime(prob.problem_pic.path) ))
		except:
			pic_url = prob.problem_pic.url

	#redirect to clear update GET request from url
	if request.user.is_authenticated and request.GET.get("update",False):
		return HttpResponseRedirect("../"+str(prob.id))
	else:
		#render page and include media url to pdf
		return render_to_response('qualApp/problem_detail.html',
			RequestContext(request,{
				'problem':prob,
				'solution_list':solution_list,
				#since browser may escape '\(' ??
				#this removes HTML tags and helps MathJax parse greater than and less than signs
				'solution_text':solution_text.replace("<"," < ").replace(">"," > "),
				'solution_user':solution_user,
				'solution_user_id':solution_user_id,
				'sol_url':sol_url,
				'pic_url':pic_url,
				'prob_id_prev':prob_id_prev,
				'prob_id_next':prob_id_next,
				#'prob_text':text_string, #experiment
			})#template_keyword:local_variable
		)

def MathJaxConf(request,pk):
	return HttpResponse('   MathJax.Hub.Config({ \
	tex2jax: { \
      inlineMath: [ ["$","$"], ["\\(","\\)"] ], \
      displayMath: [ ["$$","$$"], ["\\[","\\]"] ], \
      processEscapes: true \
    }, \
	asciimath2jax: { \
		delimiters: [["`","`"], ["$","$"]] \
	} \
	});')


def problem_search(request):
	probs = Problem.objects.all()
	searchStr = request.GET.get('q','')
	
	if request.GET.get('fullText',False) == "on":
		#loop through problems and grab text (only need to do this once really, and for each new problem)
		if REPARSE_FULL_TEXT:
			for p in probs:
				if not p.problem_TeX:
					temp_text = pdf2text(p.qual.pdf.path, eval(p.problem_pages) )
					if len(temp_text) > 2000: #the size in the db
						temp_text = temp_text[0:2000]
					p.problem_TeX = temp_text
					p.save() #update database
		
		from django.db.models import Q
		results = probs.filter( Q(topic__contains=searchStr) | Q(problem_TeX__contains=searchStr) )
	else:
		results = probs.filter( topic__contains=searchStr )
		 
	return render_to_response('qualApp/problem_list.html',
		RequestContext(request,{
				'problem_list': results,
	}))

def random_problem(request):
	import random
	probs = Problem.objects.all()
	rand_idx = random.randrange(0,len(probs)-1,1)
	rand_id_str = str(probs[rand_idx].id)
	
	return HttpResponseRedirect(rand_id_str)

def user_solutions(request,uid):
	
	if str(request.user.id) == str(uid):
		#show private entries
		solution_list = Solution.objects.filter(user = uid)
		user = request.user
	else:
		solution_list = Solution.objects.filter(user = uid).filter(private=False)
		user = User.objects.get(id=uid)

	return render_to_response('qualApp/solution_list.html',
		RequestContext(request,{
				'solution_list': solution_list,
				'by_user':user,
	}))

def user_notes(request,uid):
	
	if str(request.user.id) == str(uid):
		#show private entries
		note_list = Note.objects.filter(user = uid)
		user = request.user
	else:
		note_list = Note.objects.filter(user = uid).filter(private=False)
		user = User.objects.get(id=uid)

	return render_to_response('qualApp/note_list.html',
		RequestContext(request,{
				'note_list': note_list,
				'by_user':user,
	}))


@login_required(login_url='/qualApp/accounts/login/',redirect_field_name='continue')
def crop_image(request,pk):
	
	# we assume the pngs have already been rendered	
	cropAbove = request.GET.get('above',False)
	cropBelow = request.GET.get('below',False)
	cropSolution = request.GET.get('show_solution',False)
	
	# problem object:
	prob = Problem.objects.get(id=pk)
	
	#this will automatically crop the problem image is there is no solution image.
	if request.session.get("show_solution","false") == "true" and fieldAndFileExist(prob.solution_pic):
		png_path = prob.solution_pic.path
	else:
		png_path = prob.problem_pic.path
	
	# use imageMagick convert -chop tool to trim top or bottom
	if cropAbove:
		subprocess.call("convert "+png_path+" -chop 0x"+cropAbove+" "+png_path ,shell=True)
		#shortcut to crop top if problem pages are same as solution pages?

	if cropBelow:
		subprocess.call("convert "+png_path+" -gravity SouthWest -chop 0x"+cropBelow+" "+png_path ,shell=True)
		
	# render page and include media url to pdf
	#pic_url = prob.problem_pic.url + "?v="+str(time.time())
	
	#redirect to clear GET request
	return HttpResponseRedirect("../"+str(prob.id))
#	return render_to_response('qualApp/problem_detail.html',
#		RequestContext(request,{
#			'problem':prob,
#			'pic_url':pic_url,
#		})#template_keyword:local_variable
#	)

		
def test(request, qual_id):
	return HttpResponse("You're looking at a test %s." % qual_id)

@login_required(login_url='/qualApp/accounts/login/',redirect_field_name='continue')
def add_problem(request):

	qual = Qual.objects.get(id=request.GET['qual']) # TODO: may not be air tight: try GET.get() instead
	
	if request.method == 'POST': # If the form has been submitted...
		form = PartialProblemForm(request.POST) # A form bound to the POST data
		if form.is_valid(): # All validation rules pass
			
			if request.user.has_perm('qualApp.add_problem'):
				# Process the data
				#form = PartialProblemForm(request.POST)
				prob = form.save(commit=False) #this allows us to add data in next line before hitting DB
				prob.qual = qual #add some more data
				prob.save() #finally save the row in the DB
				return HttpResponseRedirect('../problems/'+str(prob.id)) # Redirect after POST
			else:
				return HttpResponse('You do not have permissions to add a problem, please login or register.')
	else:
		form = PartialProblemForm() # An unbound form
	
	#create a csrf context
	ctex = {'form':form,
			'qual':qual,}
	ctex.update(csrf(request))	
	return render_to_response('qualApp/problem_add.html',RequestContext(request,ctex))

def tagging_mode():
	pass

#create view from modelForm
class QualEditView(UpdateView):
	form_class = QualEditForm
	model = Qual

	#redirect on success
	def get_success_url(self): 
#		if self.kwargs['success_root']
		return self.kwargs['success_root'] + self.kwargs['pk']

	#assure permissions are satisfied
	def dispatch(self, request, *args, **kwargs):
		if not request.user.has_perm('qualApp.change_qual'):
			return HttpResponse("You do not have permission to edit this qual, please login or register and account.")
		return super(QualEditView, self).dispatch(request, *args, **kwargs)


#@method_decorator(login_required)
#@method_decorator(login_required)
#def dispatch(self, *args, **kwargs):
	#return super(ProtectedView, self).dispatch(*args, **kwargs)


#create view from modelForm
class ProblemEditView(UpdateView):
	form_class = ProblemEditForm
	model = Problem

	#redirect on success
	def get_success_url(self): 
#		if self.kwargs['success_root']
		return self.kwargs['success_root'] + self.kwargs['pk']

	def get_context_data(self, **kwargs):
		# Call the base implementation first to get a context
		context = super(ProblemEditView, self).get_context_data(**kwargs)
		# Add in some context variables
		thisProb = Problem.objects.get(id=self.kwargs['pk'])
		context['qual_str'] = thisProb.qual
		context['qual_id'] = thisProb.qual.id
		context['create'] = False
		#context['tagging'] = request.GET.get('tagging')
		return context

	#assure permissions are satisfied
	def dispatch(self, request, *args, **kwargs):
		if not request.user.has_perm('qualApp.change_problem'):
			return HttpResponse("You do not have permission to edit this problem, please login or register and account.")
		return super(ProblemEditView, self).dispatch(request, *args, **kwargs)


#create view from modelForm
class NoteEditView(UpdateView):
	form_class = NoteEditForm
	model = Note

	#redirect on success
	def get_success_url(self): 
#		if self.kwargs['success_root']
		return self.kwargs['success_root'] + self.kwargs['pk']

	def get_context_data(self, **kwargs):
		# Call the base implementation first to get a context
		context = super(NoteEditView, self).get_context_data(**kwargs)
		# Add in some context variables
#		thisProb = Problem.objects.get(id=self.kwargs['pk'])
#		context['qual_str'] = thisProb.qual
#		context['qual_id'] = thisProb.qual.id
		context['create'] = False
		#context['tagging'] = request.GET.get('tagging')
		return context

	#assure permissions are satisfied
	def dispatch(self, request, *args, **kwargs):
		if not request.user.has_perm('qualApp.change_note'):
			return HttpResponse("You do not have permission to edit this n, please login or register and account.")
		return super(NoteEditView, self).dispatch(request, *args, **kwargs)

#create view from modelForm
class SolutionEditView(UpdateView):
	form_class = PartialSolutionForm
	model = Solution

	#redirect on success
	def get_success_url(self):
		thisSol = Solution.objects.get(id=self.kwargs['pk'])
#		if self.kwargs['success_root']
		# return to url of problem detail with solution in focus
		return self.kwargs['success_root'] + str(thisSol.problem.id) + "/" + "?show_solution=true&sol=" + str(thisSol.id) 

	def get_context_data(self, **kwargs):
		# Call the base implementation first to get a context
		context = super(SolutionEditView, self).get_context_data(**kwargs)
		# Add in some context variables
		thisSol = Solution.objects.get(id=self.kwargs['pk'])
		context['qual_str'] = thisSol.problem.qual
		context['qual_id'] = thisSol.problem.qual.id
		context['problem_str'] = thisSol.problem
		context['problem_id'] = thisSol.problem.id
		context['create'] = False
		return context

	#assure permissions are satisfied
	def dispatch(self, request, *args, **kwargs):
		thisSol = Solution.objects.get(id=kwargs['pk'])
		if not request.user.id == thisSol.user.id:
			if not request.user.has_perm('qualApp.change_solution'):
				return HttpResponse("You do not have permission to edit this solution. You did not create it or you are not an editor. Make sure you are logged in.")
		return super(SolutionEditView, self).dispatch(request, *args, **kwargs)

@login_required(login_url='/qualApp/accounts/login/',redirect_field_name='continue')
def add_qual(request):
	if request.method == 'POST': # If the form has been submitted...
		form = QualCreateForm(request.POST, request.FILES) # A form bound to the POST data

		if form.is_valid(): # All validation rules pass
			if request.user.has_perm('qualApp.add_qual'):
				# Process the data
				newQual = form.save(commit=False)
				#add more data if needed
				newQual.save()
				return HttpResponseRedirect('../quals/'+str(newQual.id)) # Redirect after POST
			else:
				return HttpResponse('You do not have permissions to add a qual.')
	else: #send empty form
#		if request.GET.get('edit',False): #if we are editing a qual
#			form = QualForm(Qual.objects.get( id=int(request.GET.get('edit')) )
		form = QualCreateForm() # An unbound form
	
	#create a csrf context
	ctex = {'form':form,}
	ctex.update(csrf(request))	
	return render_to_response('qualApp/qual_form.html',RequestContext(request,ctex))

@login_required(login_url='/qualApp/accounts/login/',redirect_field_name='continue')
def add_solution(request, pk):
	if request.method == 'POST': # If the form has been submitted...
		form = PartialSolutionForm(request.POST, request.FILES) # A form bound to the POST data

		if form.is_valid(): # All validation rules pass
			if request.user.has_perm('qualApp.add_solution'):
				# Process the data
				newSol = form.save(commit=False) #partial save creates model object (not form anymore)
				newSol.user = User.objects.get(id=request.user.id) #set user
				newSol.problem = Problem.objects.get(id=pk) #set problem
				#add more data if needed
				newSol.save() #save to database
				return HttpResponseRedirect("../"+str(pk)+"?show_solution=true&sol="+str(newSol.id)) # Redirect after POST
			else:
				return HttpResponse('You do not have permissions to add a solution.')
	else: #send empty form
#		if request.GET.get('edit',False): #if we are editing a qual
#			form = QualForm(Qual.objects.get( id=int(request.GET.get('edit')) )
		form = PartialSolutionForm() # An unbound form
	
	thisProb = Problem.objects.get(id=pk)
	#create a csrf context
	ctex = {
		'form':form,
		'qual_str' : thisProb.qual,
		'qual_id' : thisProb.qual.id,
		'problem_str' : thisProb,
		'problem_id' : thisProb.id,
		'create' : True,
	}
	ctex.update(csrf(request))	
	return render_to_response('qualApp/solution_form.html',RequestContext(request,ctex))

@login_required(login_url='/qualApp/accounts/login/',redirect_field_name='continue')
def add_note(request):
	if request.method == 'POST': # If the form has been submitted...
		form = NoteEditForm(request.POST, request.FILES) # A form bound to the POST data

		if form.is_valid(): # All validation rules pass
			if request.user.has_perm('qualApp.add_note'):
				# Process the data
				newNote = form.save(commit=False) #partial save creates model object (not form anymore)
				newNote.user = User.objects.get(id=request.user.id) #set user
				#add more data if needed
				newNote.save() #save to database
				return HttpResponseRedirect(str(newNote.id)) # Redirect after POST
			else:
				return HttpResponse('You do not have permissions to add a note.')
	else: #send empty form
#		if request.GET.get('edit',False): #if we are editing a qual
#			form = QualForm(Qual.objects.get( id=int(request.GET.get('edit')) )
		form = NoteEditForm() # An unbound form
	
	#create a csrf context
	ctex = {
		'form':form,
		'create' : True,
	}
	ctex.update(csrf(request))	
	return render_to_response('qualApp/note_form.html',RequestContext(request,ctex))
