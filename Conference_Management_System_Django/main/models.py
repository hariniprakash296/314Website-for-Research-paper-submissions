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

    def toggle_user_suspension(self):
        self.is_suspended = not self.is_suspended
        self.save()
    
class SystemAdmin(User):
    def __str__(self):
        return "System Admin"

class ConferenceChair(User):
    def __str__(self):
        return "Conference Chair"

class Reviewer(User):
    max_papers = models.PositiveIntegerField(null=False, default=5)

    def get_currently_reviewing_count(self):
        currently_reviewing_count = 0
        try:
            currently_reviewing = Reviews.objects.filter(reviewer_user_id=self, reviewer_rating=Reviews.Rating.UNRATED)

            currently_reviewing_count = len(currently_reviewing)
        except Reviews.DoesNotExist as e:
            currently_reviewing_count = 0

        return currently_reviewing_count

    def can_be_allocated_another_paper(self):
        return self.get_currently_reviewing_count() < self.max_papers

    def is_reviewer_of_paper(self, paper_id):
        try:
            reviews = Reviews.objects.get(reviewer_user_id=self, paper_id=paper_id)
            return True
        except Reviews.DoesNotExist as e:
            return False


    def __str__(self):
        return "Reviewer"

class Author(User):

    @staticmethod
    def get_all_authors_of_paper(paper_id):
        authors = list()

        try:
            writes = Writes.objects.filter(paper_id=paper_id)
            for write in writes:
                author = write.author_user_id
                authors.append(author)
        except Writes.DoesNotExist as e:
            #no authors for specified paper id
            print(e)

        return authors

    def __str__(self):
        return "Author"
    
class Paper(models.Model):
    class PaperStatus(models.IntegerChoices):
        PAPERSTATUS_NOTSUBMITTED = 0,       _("Not Submitted")
        PAPERSTATUS_SUBMITTEDPENDING = 1,   _("Submitted, but Pending")
        PAPERSTATUS_SUBMITTEDREJECTED = 2,  _("Submitted, and Rejected")
        PAPERSTATUS_SUBMITTEDACCEPTED = 3,  _("Submitted, and Accepted")

    paper_id = models.AutoField(null=False, primary_key=True)
    paper_name = models.TextField(null=False, default="Temp Title")
    paper_details = models.TextField(null=False, default="")
    status = models.IntegerField(null=False, choices=PaperStatus.choices, default=PaperStatus.PAPERSTATUS_NOTSUBMITTED)
    
    def is_paper_fully_reviewed(self):
        reviews = Reviews.objects.filter(paper_id=self)
        unrated_reviews = reviews.filter(reviewer_rating=Reviews.Rating.UNRATED)
        completed_reviews = reviews.exclude(reviewer_rating=Reviews.Rating.UNRATED)
        return (len(unrated_reviews) == 0 and len(reviews) == len(completed_reviews) and len(reviews) > 0)
        
    def is_paper_reviews_author_rated(self):
        reviews = Reviews.objects.filter(paper_id=self)
        unrated_reviews = reviews.filter(author_rating=Reviews.Rating.UNRATED)
        completed_reviews = reviews.exclude(author_rating=Reviews.Rating.UNRATED)
        return self.is_paper_fully_reviewed() and (len(unrated_reviews) == 0 and len(reviews) == len(completed_reviews) and len(reviews) > 0)
    
#relationships
class Bids(models.Model):
    reviewer_user_id = models.ForeignKey('User', on_delete=models.CASCADE)
    paper_id = models.ForeignKey('Paper', on_delete=models.CASCADE)
    is_bidding = models.BooleanField(null=False, default=True)

    def toggle_reviewer_bid(self):
        self.is_bidding = not self.is_bidding
        self.save()

    @staticmethod
    def does_bid_exist(reviewer_user_id, paper_id):
        try:
            bid = Bids.objects.get(reviewer_user_id=reviewer_user_id, paper_id=paper_id)
            return (True, bid)
        except Bids.DoesNotExist as e:
            return (False, None)

    @staticmethod
    def get_reviewer_bid(reviewer_user_id, paper_id):
        bidExists, bid = Bids.does_bid_exist(reviewer_user_id, paper_id)
        if bidExists:
            return bid.is_bidding
        
        return False

class Writes(models.Model):
    author_user_id = models.ForeignKey('User', on_delete=models.CASCADE)
    paper_id = models.ForeignKey('Paper', on_delete=models.CASCADE)

    @staticmethod
    def get_names_of_authors(paper_id):
        try:
            writes = Writes.objects.filter(paper_id=paper_id)
            author_names = list()
            for write in writes:
                author_names.append(write.author_user_id.name)

            return ",".join(author_names)
        except Writes.DoesNotExist as e:
            return ""

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
    
    @staticmethod
    def does_review_exist(reviewer_user_id, paper_id):
        try:
            review = Reviews.objects.get(reviewer_user_id=reviewer_user_id, paper_id=paper_id)
            return (True, review)
        except Reviews.DoesNotExist as e:
            return (False, None)

class ReviewComments(models.Model):
    comment_id = models.AutoField(null=False, primary_key=True)
    review_id = models.ForeignKey('Reviews', on_delete=models.CASCADE)
    commenter_user_id = models.ForeignKey('User', on_delete=models.CASCADE)
    comment_text = models.TextField(null=False, default="")
    
    # type = models.TextField(null=False)
    # end_date = models.DateTimeField(null=False)
    # is_accepted = models.BooleanField(default=False)
    # author = models.ForeignKey('Author',on_delete=models.CASCADE)