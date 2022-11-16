from django.shortcuts import render
from django.http import HttpResponse,Http404
from main import models
import hashlib
from main import Utils
from threading import Lock
from threading import Thread
from conferencesystem import settings
import datetime
from django.core.files.storage import FileSystemStorage
import os
from main import constants
from django.db.models import Q
from django.utils import timezone
from django.utils.encoding import smart_str
from django.shortcuts import redirect
from main.controller import controller_util

email_lock = Lock()

#view funcs	
def conferencechair_error_handle(request):
    response = render(request, "login.html", {"islogged_in": False, "is_admin_logged_in":False, 'message':'You are not a conference chair.'})
    response.delete_cookie('user_type')
    response.delete_cookie('email')
    response.delete_cookie('password')
    return response

def check_conferencechair_login(request):
    return controller_util.check_type_login(request, models.User.UserType.USERTYPE_CONFERENCECHAIR)

#view papers that have been submitted
def conferencechair_view_submitted_papers(request):
    #requires: none
    #returns: paperstatus_dict = dictionary of all the paper status labels, key = int, val = string
    #returns: papers = list of all the papers
    #returns: papers_additional_info = nested dictionary of additional values for papers.
    #                                  dict(int paper_id, dict(string key, ? value))
    #                                                           ^ "is_allocated", "is_bid"

    islogged_in = controller_util.check_login(request)
    is_conferencechair_logged_in = check_conferencechair_login(request)

    if not (islogged_in and is_conferencechair_logged_in):
        return conferencechair_error_handle(request)

    context = {"islogged_in":islogged_in,"is_admin_logged_in":False,"user_type":request.COOKIES.get('user_type')}
        
    paperstatus_dict = dict()
    for key, value in models.Paper.PaperStatus.choices:
        paperstatus_dict[key] = value

    papers = list()
    papers_additional_info = dict()

    try:
        papers = models.Paper.objects.filter(status=models.Paper.PaperStatus.PAPERSTATUS_SUBMITTEDPENDING)

        for paper in papers:
            additional_info = dict()
            paper_id = paper.paper_id

            try:
                bids = models.Bids.objects.filter(paper_id=paper_id)
                additional_info["is_bid"] = True
            except models.Bids.DoesNotExist as e:
                additional_info["is_bid"] = False

            try:
                reviews = models.Reviews.objects.filter(paper_id=paper_id)
                additional_info["is_allocated"] = True
            except models.Reviews.DoesNotExist as e:
                additional_info["is_allocated"] = False

            papers_additional_info[paper_id] = additional_info
    except models.Paper.DoesNotExist as e:
        context["message"] = "There are no submitted papers that have not been accepted or rejected."
        
    context["papers"] = papers
    context["paperstatus_dict"] = paperstatus_dict
    context["papers_additional_info"] = papers_additional_info

    return render(request,"conferencechair_listsubmittedpapers.html", context)

#view reviewers of selected paper, including biddings
def conferencechair_view_reviewers(request, message=None):
    #requires: paper_id = id of selected paper
    #returns: paper = details of selected paper
    #returns: reviewers = list of all the reviewers
    #returns: reviewer_additional_info = nested dictionary of additional values for reviewers.
    #                                    dict(int reviewer_user_id, dict(string key, ? value))
    #                                                           ^ "is_allocated", "is_bid", "currently_reviewing_count"

    islogged_in = controller_util.check_login(request)
    is_conferencechair_logged_in = check_conferencechair_login(request)

    if not (islogged_in and is_conferencechair_logged_in):
        return conferencechair_error_handle(request)
    
    if request.method == "POST":
        paper_id = request.POST.get('paper_id')
        paper= models.Paper.objects.get(paper_id=paper_id)

        reviewers = models.Reviewer.objects.all()

        reviewer_additional_info = dict()
        for reviewer in reviewers:
            additional_info = dict()

            additional_info["is_bid"] = models.Bids.get_reviewer_bid(reviewer.user_id, paper_id)

            additional_info["is_allocated"], review = models.Reviews.does_review_exist(reviewer.user_id, paper_id)

            additional_info["currently_reviewing_count"] = reviewer.get_currently_reviewing_count()

            reviewer_additional_info[reviewer.user_id] = additional_info

        context = {"islogged_in":islogged_in,"is_admin_logged_in":False,"user_type":request.COOKIES.get('user_type'),
                    "paper":paper, "reviewers":reviewers, "reviewer_additional_info":reviewer_additional_info}
                    
    if message != None and not "message" in context:
        context["message"] = message

    return render(request,"conferencechair_listreviewers.html", context)

#allocate paper to reviewer
def conferencechair_AllocatePaper(request):
    #requires: paper_id = id of selected paper
    #requires: reviewer_user_id = id of selected reviewer
    #returns: paper = details of selected paper
    #returns: reviewers = list of all the reviewers
    #returns: reviewer_additional_info = nested dictionary of additional values for reviewers.
    #                                    dict(int reviewer_user_id, dict(string key, ? value))
    #                                                           ^ "is_allocated", "is_bid", "currently_reviewing_count"
    islogged_in = controller_util.check_login(request)
    is_conferencechair_logged_in = check_conferencechair_login(request)

    if not (islogged_in and is_conferencechair_logged_in):
        return conferencechair_error_handle(request)

    if request.method == "POST":
        paper_id = request.POST.get('paper_id')
        reviewer_user_id = request.POST.get('reviewer_user_id')

        try:
            paper = models.Paper.objects.get(paper_id=paper_id)
            reviewer = models.Reviewer.objects.get(user_id=reviewer_user_id)

            if not reviewer.can_be_allocated_another_paper():
                return conferencechair_view_reviewers(request, "Error. Reviewer has already been allocated the maximum number of papers.")
            
            if reviewer.is_reviewer_of_paper(paper_id):
                return conferencechair_view_reviewers(request, "Error. Reviewer has already been allocated the selected paper.")

            models.Reviews.objects.create(reviewer_user_id=reviewer_user_id, paper_id=paper_id)

            return conferencechair_view_reviewers(request, "Paper successfully allocated to reviewer.")

        except models.Paper.DoesNotExist as e:
            return conferencechair_view_reviewers(request, "Error. Paper not found.")
        except models.Reviewer.DoesNotExist as e:
            return conferencechair_view_reviewers(request, "Error. Reviewer not found.")

#view papers that have been rated by reviewers
def conferencechair_view_reviewed_papers(request, message=None):
    #requires: none
    #returns: fully_reviewed_papers = list of all the papers that have been reviewed by all the reviewers allocated

    islogged_in = controller_util.check_login(request)
    is_conferencechair_logged_in = check_conferencechair_login(request)

    if not (islogged_in and is_conferencechair_logged_in):
        return conferencechair_error_handle(request)

    fully_reviewed_papers = list()
    context = {"islogged_in":islogged_in,"is_admin_logged_in":False,"user_type":request.COOKIES.get('user_type')}

    try:
        papers = models.Paper.objects.filter(status=models.Paper.PaperStatus.PAPERSTATUS_SUBMITTEDPENDING)

        for paper in papers:
            paper_id = paper.paper_id

            fully_reviewed = True
            try:
                reviews = models.Reviews.objects.filter(paper_id=paper_id)
                for review in reviews:
                    if review.reviewer_rating == models.Reviews.Rating.UNRATED:
                        fully_reviewed = False
                        break
            except models.Reviews.DoesNotExist as e:
                fully_reviewed = False

            if fully_reviewed:
                fully_reviewed_papers.append(paper)
    except models.Paper.DoesNotExist as e:
        context["message"] = "There are no submitted papers that have been fully reviewed by their allocated reviewers."

    context["fully_reviewed_papers"] = fully_reviewed_papers

    return render(request,"conferencechair_listreviewedpapers.html", context)

def conferencechair_view_reviewer_ratings(request, message=None):
    #requires: paper_id = id of selected paper
    #returns: paper = selected paper
    #returns: reviews = list of reviews of selected paper
    #returns: reviewer = dictionary of all the reviewers of the reviews
    #returns: reviewrating_dict = dict of the ratings' labels

    islogged_in = controller_util.check_login(request)
    is_conferencechair_logged_in = check_conferencechair_login(request)

    if not (islogged_in and is_conferencechair_logged_in):
        return conferencechair_error_handle(request)

    context = {"islogged_in":islogged_in,"is_admin_logged_in":False,"user_type":request.COOKIES.get('user_type')}

    if request.method == "POST":
        paper_id = request.POST.get('paper_id')

        reviews = models.Reviews.objects.filter(paper_id=paper_id)
        reviewers = dict()

        for review in reviews:
            if review.reviewer_rating == models.Reviews.Rating.UNRATED:
                return conferencechair_view_reviewed_papers(request, "There are reviewers who have been allocated the paper but have not rated it.")

            #reviewer = models.Reviewer.objects.get(user_id=)
            reviewer = review.reviewer_user_id
            reviewers[review.review_id] = reviewer

        paper = models.Paper.objects.get(paper_id=paper_id)
        context["paper"] = paper
        context["review"] = review
        context["reviewer"] = reviewer
    
    reviewrating_dict = dict()
    for key, value in models.Reviews.Rating.choices:
        reviewrating_dict[key] = value
    context["reviewrating_dict"] = reviewrating_dict

    return render(request,"conferencechair_viewreviewerreviews.html", context)

def conferencechair_AcceptPaper(request):
    #requires: paper_id = id of selected paper
    #returns: fully_reviewed_papers = list of all the papers that have been reviewed by all the reviewers allocated

    islogged_in = controller_util.check_login(request)
    is_conferencechair_logged_in = check_conferencechair_login(request)

    if not (islogged_in and is_conferencechair_logged_in):
        return conferencechair_error_handle(request)

    context = {"islogged_in":islogged_in,"is_admin_logged_in":False,"user_type":request.COOKIES.get('user_type')}

    if request.method == "POST":
        paper_id = request.POST.get('paper_id')
        choice = True

        new_status = models.Paper.PaperStatus.PAPERSTATUS_SUBMITTEDACCEPTED if choice else models.Paper.PaperStatus.PAPERSTATUS_SUBMITTEDREJECTED

        paper = models.Paper.objects.get(paper_id=paper_id)
        paper.status = new_status
        paper.save()

        choice_text = "accepted" if choice else "rejected"

        return conferencechair_view_reviewed_papers(request, "The paper has successfully been "+choice_text)

def conferencechair_RejectPaper(request):
    #requires: paper_id = id of selected paper
    #returns: fully_reviewed_papers = list of all the papers that have been reviewed by all the reviewers allocated

    islogged_in = controller_util.check_login(request)
    is_conferencechair_logged_in = check_conferencechair_login(request)

    if not (islogged_in and is_conferencechair_logged_in):
        return conferencechair_error_handle(request)

    context = {"islogged_in":islogged_in,"is_admin_logged_in":False,"user_type":request.COOKIES.get('user_type')}

    if request.method == "POST":
        paper_id = request.POST.get('paper_id')
        choice = False

        new_status = models.Paper.PaperStatus.PAPERSTATUS_SUBMITTEDACCEPTED if choice else models.Paper.PaperStatus.PAPERSTATUS_SUBMITTEDREJECTED

        paper = models.Paper.objects.get(paper_id=paper_id)
        paper.status = new_status
        paper.save()

        choice_text = "accepted" if choice else "rejected"

        return conferencechair_view_reviewed_papers(request, "The paper has successfully been "+choice_text)

                



    

