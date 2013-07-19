from qualApp.models import Qual, Problem, Solution, Note
from django.contrib import admin

#customizing admin display
class QualAdmin(admin.ModelAdmin):
	list_display = ('qual_readable')
	list_filter = ['qual']

class ProblemAdmin(admin.ModelAdmin):
	list_display = ('subject','topic','level','qual')
	list_filter = ['level','subject']
	search_fields = ['topic']#,'qual__term','qual__year']

admin.site.register(Qual)
admin.site.register(Problem,ProblemAdmin)
admin.site.register(Solution)
admin.site.register(Note)
