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
def reviewer_error_handle(request):
    response = render(request, "login.html", {"islogged_in": False, "is_admin_logged_in":False, 'message':'You are not a reviewer.'})
    response.delete_cookie('user_type')
    response.delete_cookie('email')
    response.delete_cookie('password')
    return response

def check_reviewer_login(request):
    return controller_util.check_type_login(request, models.User.UserType.USERTYPE_REVIEWER)

def reviewer_list_biddable_papers(request, message=None):
    #requires: nothing
    #returns: biddable_papers = list of all the papers that can be bid on
    #returns: bids_additional_info = dictionary of whether reviewer has bid on each paper.
    #                                  dict(int paper_id, bool is_bid)
    islogged_in = controller_util.check_login(request)
    is_author_logged_in = check_reviewer_login(request)

    if not (islogged_in and is_author_logged_in):
        return reviewer_error_handle(request)

    biddable_papers = models.Paper.objects.filter(status=models.Paper.PaperStatus.PAPERSTATUS_SUBMITTEDPENDING)
    
    email = request.COOKIES.get('email')
    reviewer = models.Reviewer.objects.get(login_email=email)

    bids_additional_info = dict()
    for biddable_paper in biddable_papers:
        bids_additional_info[biddable_paper.paper_id] = models.Bids.get_reviewer_bid(reviewer.user_id, biddable_paper.paper_id)

    context = {"islogged_in":islogged_in,"is_admin_logged_in":False,"user_type":request.COOKIES.get('user_type'), "biddable_papers":biddable_papers, "bids_additional_info":bids_additional_info}

    if message != None and not "message" in context:
        context["message"] = message

    return render(request,"reviewer_listbiddablepapers.html", context)

def reviewer_BidPaper(request):
    #requires: paper_id = id of selected paper
    #returns: biddable_papers = list of all the papers that can be bid on
    #returns: bids_additional_info = dictionary of whether reviewer has bid on each paper.
    #                                  dict(int paper_id, bool is_bid)
    if request.method == "POST":
        paper_id = request.POST.get('paper_id')
        
        try:
            paper = models.Paper.objects.get(paper_id=paper_id)
            email = request.COOKIES.get('email')
            reviewer = models.Reviewer.objects.get(login_email=email)

            bidExists, bid = models.Bids.does_bid_exist(reviewer.user_id, paper_id)
            if not bidExists:
                bid = models.Bids.objects.create(reviewer_user_id=reviewer, paper_id=paper)
            else:
                bid.toggle_reviewer_bid()
            
            message = "Successfully removed bid on "
            if bid.is_bidding:
                message = "Successfully bid on "

            return reviewer_list_biddable_papers(request, message+paper.paper_name)
        except models.Paper.DoesNotExist as e:
            return reviewer_list_biddable_papers(request, "Error: Specified paper cannot be found.")
        except models.Reviewer.DoesNotExist as e:
            return reviewer_list_biddable_papers(request, "Error: Reviewer account cannot be found.")
    

def reviewer_list_unreviewed_papers(request, message=None):
    #requires: nothing
    #returns: reviewed_papers = list of all the papers that user is listed as reviewer of
    islogged_in = controller_util.check_login(request)
    is_author_logged_in = check_reviewer_login(request)

    if not (islogged_in and is_author_logged_in):
        return reviewer_error_handle(request)

    email = request.COOKIES.get('email')
    reviewer = models.Reviewer.objects.get(login_email=email)

    all_reviews = models.Reviews.objects.filter(reviewer_user_id=reviewer, reviewer_rating=models.Reviews.Rating.UNRATED)
    reviewed_papers = list()
    for review in all_reviews:
        paper = review.paper_id
        reviewed_papers.append(paper)
    reviewed_papers.reverse()

    context = {"islogged_in":islogged_in,"is_admin_logged_in":False,"user_type":request.COOKIES.get('user_type'), "reviewed_papers":reviewed_papers}

    if len(reviewed_papers) == 0:
        context["message"] = "There are no papers allocated to you that have not been reviewed."

    if message != None and not "message" in context:
        context["message"] = message

    return render(request,"reviewer_listreviewingpapers.html", context)

def reviewer_view_paper(request, message=None):
    #requires: paper_id = id of selected paper
    #returns: selected_paper = all the details of the paper that the user selected
    #returns: author_name_string = names of all the authors of the selected paper

    islogged_in = controller_util.check_login(request)
    is_reviewer_logged_in = check_reviewer_login(request)

    if not (islogged_in and is_reviewer_logged_in):
        return reviewer_error_handle(request)
        
    context = {"islogged_in":islogged_in,"is_admin_logged_in":False,"user_type":request.COOKIES.get('user_type')}

    if request.method == "POST":
        paper_id = request.POST.get('paper_id')

        email = request.COOKIES.get('email')
        reviewer = models.Reviewer.objects.get(login_email=email)

        if not reviewer.is_reviewer_of_paper(paper_id):
            return reviewer_list_unreviewed_papers(request, "Not reviewer of selected paper")

        context['author_name_string'] = models.Writes.get_names_of_authors(paper_id)

        paper = models.Paper.objects.get(paper_id=paper_id)
        context["selected_paper"] = paper

    if message != None and not "message" in context:
        context["message"] = message

    return render(request,"reviewer_viewpaper.html", context)

def reviewer_give_review(request, message=None):
    #requires: paper_id = id of selected paper
    #returns: selected_paper = all the details of the paper that the user selected
    #returns: authors = all the authors of the selected paper
    #returns: review = details of the saved review
    #returns: reviewrating_dict = dict of the ratings' labels

    islogged_in = controller_util.check_login(request)
    is_reviewer_logged_in = check_reviewer_login(request)

    if not (islogged_in and is_reviewer_logged_in):
        return reviewer_error_handle(request)
        
    context = {"islogged_in":islogged_in,"is_admin_logged_in":False,"user_type":request.COOKIES.get('user_type')}

    if request.method == "POST":
        paper_id = request.POST.get('paper_id')

        email = request.COOKIES.get('email')
        reviewer = models.Reviewer.objects.get(login_email=email)

        if not reviewer.is_reviewer_of_paper(paper_id):
            return reviewer_list_unreviewed_papers(request, "Not reviewer of selected paper")

        context["authors"] = models.Writes.get_names_of_authors(paper_id)
        
        review = models.Reviews.objects.get(reviewer_user_id=reviewer, paper_id=paper_id)
        
        if review.reviewer_rating != models.Reviews.Rating.UNRATED:
            return reviewer_list_unreviewed_papers(request, "You have already reviewed the paper.")

        context["review"] = review

        paper = review.paper_id
        context["selected_paper"] = paper
        
    reviewrating_dict = dict()
    for key, value in models.Reviews.Rating.choices:
        reviewrating_dict[key] = value
    context["reviewrating_dict"] = reviewrating_dict

    if message != None and not "message" in context:
        context["message"] = message

    return render(request,"reviewer_viewreview.html", context)

def reviewer_SaveReview(request):
    #requires: paper_id = id of selected paper
    #requires: new_details = details of the review to save
    #returns: selected_paper = all the details of the paper that the user selected
    #returns: authors = all the authors of the selected paper
    #returns: review = details of the saved review
    islogged_in = controller_util.check_login(request)
    is_reviewer_logged_in = check_reviewer_login(request)

    if not (islogged_in and is_reviewer_logged_in):
        return reviewer_error_handle(request)
        
    if request.method == "POST":
        paper_id = request.POST.get('paper_id')

        email = request.COOKIES.get('email')
        reviewer = models.Reviewer.objects.get(login_email=email)

        if not reviewer.is_reviewer_of_paper(paper_id):
            return reviewer_list_unreviewed_papers(request, "Not reviewer of selected paper")

        review = models.Reviews.objects.get(reviewer_user_id=reviewer, paper_id=paper_id)
        
        if review.reviewer_rating != models.Reviews.Rating.UNRATED:
            return reviewer_view_paper(request, "You have aleady rated this paper.")

        review.review_details = request.POST.get('new_details')
        review.save()

    return reviewer_give_review(request, "Successfully saved editted review.")

def reviewer_GiveRating(request):
    #requires: paper_id = id of selected paper
    #requires: new_details = details of the review to save
    #requires: rating = rating of the reviewer to save
    #returns: reviewed_papers = list of all the papers that user is listed as reviewer of
    islogged_in = controller_util.check_login(request)
    is_reviewer_logged_in = check_reviewer_login(request)

    if not (islogged_in and is_reviewer_logged_in):
        return reviewer_error_handle(request)
        
    if request.method == "POST":
        paper_id = request.POST.get('paper_id')

        email = request.COOKIES.get('email')
        reviewer = models.Reviewer.objects.get(login_email=email)

        if not reviewer.is_reviewer_of_paper(paper_id):
            return reviewer_list_unreviewed_papers(request, "Not reviewer of selected paper")

        review = models.Reviews.objects.get(reviewer_user_id=reviewer, paper_id=paper_id)
            
        review.review_details = request.POST.get('new_details')
        review.save()

        rating = int(request.POST.get('rating'))
        
        if review.reviewer_rating != models.Reviews.Rating.UNRATED:
            return reviewer_view_paper(request, "You have aleady rated this review.")

        if rating == models.Reviews.Rating.UNRATED:
            return reviewer_view_paper(request, "Please select a rating to give the paper.")

        review.reviewer_rating = rating
        review.save()

    return reviewer_list_unreviewed_papers(request, "Successfully submitted your review.")



