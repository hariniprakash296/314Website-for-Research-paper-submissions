from django.db import models
from django.utils import timezone
from main import constants
from polymorphic.models import PolymorphicModel
from django.utils.translation import gettext_lazy as _


#entities
class User(PolymorphicModel):
    class UserType(models.IntegerChoices):
        USERTYPE_SYSTEMADMIN = 0,       _('System Admin')
        USERTYPE_CONFERENCECHAIR = 1,   _('Conference Chair')
        USERTYPE_REVIEWER = 2,          _('Reviewer')
        USERTYPE_AUTHOR = 3,            _('Author')

    user_id = models.AutoField(null=False, primary_key=True)
    login_email = models.EmailField(null=False)
    login_pw = models.TextField(null=False)
    name = models.CharField(null=False, max_length=30)
    is_suspended = models.BooleanField(null=False, default=False)
    user_type = models.IntegerField(null=False, choices=UserType.choices)
    
class SystemAdmin(User):
    def __str__(self):
        return "System Admin"

class ConferenceChair(User):
    def __str__(self):
        return "Conference Chair"

class Reviewer(User):
    max_papers = models.PositiveIntegerField(null=False, default=5)

    def __str__(self):
        return "Reviewer"

class Author(User):
    def __str__(self):
        return "Author"
    
class Paper(models.Model):
    class PaperStatus(models.IntegerChoices):
        PAPERSTATUS_NOTSUBMITTED = 0,       _("Not Submitted")
        PAPERSTATUS_SUBMITTEDPENDING = 1,   _("Submitted, but Pending")
        PAPERSTATUS_SUBMITTEDREJECTED = 2,  _("Submitted, and Rejected")
        PAPERSTATUS_SUBMITTEDACCEPTED = 3,  _("Submitted, and Accepted")

    paper_id = models.AutoField(null=False, primary_key=True)
    paper_name = models.TextField(null=False, default="")
    paper_details = models.TextField(null=False, default="")
    status = models.IntegerField(null=False, choices=PaperStatus.choices, default=PaperStatus.PAPERSTATUS_NOTSUBMITTED)
    
    
    
#relationships
class Bids(models.Model):
    reviewer_user_id = models.ForeignKey('User', on_delete=models.CASCADE)
    paper_id = models.ForeignKey('Paper', on_delete=models.CASCADE)
    is_bidding = models.BooleanField(null=False, default=True)

class Writes(models.Model):
    author_user_id = models.ForeignKey('User', on_delete=models.CASCADE)
    paper_id = models.ForeignKey('Paper', on_delete=models.CASCADE)

class Reviews(models.Model):
    class Rating(models.IntegerChoices):
        UNRATED = -5,       _("Unrated")
        STRONGREJECT = -3,  _("Strong Reject")
        REJECT = -2,        _("Reject")
        WEAKREJECT = -1,    _("Weak Reject")
        BORDERLINE = 0,     _("Borderline")
        WEAKACCEPT = 1,     _("Weak Accept")
        ACCEPT = 2,         _("Accept")
        STRONGACCEPT = 3,   _("Strong Accept")

    review_id = models.AutoField(null=False, primary_key=True)
    paper_id = models.ForeignKey('Paper', on_delete=models.CASCADE)
    reviewer_user_id = models.ForeignKey('User', on_delete=models.CASCADE)
    review_details = models.TextField(null=False, default="")
    reviewer_rating = models.IntegerField(null=False, choices=Rating.choices, default=Rating.UNRATED)  
    author_rating = models.IntegerField(null=False, choices=Rating.choices, default=Rating.UNRATED)     
    

class ReviewComments(models.Model):
    comment_id = models.AutoField(null=False, primary_key=True)
    review_id = models.ForeignKey('Reviews', on_delete=models.CASCADE)
    commenter_user_id = models.ForeignKey('User', on_delete=models.CASCADE)
    comment_text = models.TextField(null=False, default="")
    
    # type = models.TextField(null=False)
    # end_date = models.DateTimeField(null=False)
    # is_accepted = models.BooleanField(default=False)
    # author = models.ForeignKey('Author',on_delete=models.CASCADE)