from django.contrib import admin
from main import models

admin.site.register(models.User)
admin.site.register(models.Paper)
admin.site.register(models.Reviewer)
admin.site.register(models.Bids)
admin.site.register(models.Authors)
admin.site.register(models.Reviews)
admin.site.register(models.ReviewComments)

