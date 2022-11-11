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

#view papers
def conferencechair_view_all_papers(request):
    #requires: none
    #returns: paperstatus_dict = dictionary of all the paper status labels, key = int, val = string
    #returns: papers = list of all the papers
    #returns: papers_additional_info = nested dictionary of additional values for papers.
    #                                  dict(int paper_id, dict(string key, ? value))
    #                                                           ^ "isAllocated", "isBid"

    islogged_in = controller_util.check_login(request)
    is_conferencechair_logged_in = check_conferencechair_login(request)

    if not (islogged_in and is_conferencechair_logged_in):
        return conferencechair_error_handle(request)

    papers = models.Paper.objects.all()

    papers_additional_info = dict()
    for paper in papers:
        additional_info = dict()
        paper_id = paper.paper_id

        try:
            bids = models.Bids.objects.get(paper_id=paper_id)
            additional_info["is_bid"] = True
        except models.Bids.DoesNotExist as e:
            additional_info["is_bid"] = False

        try:
            reviews = models.Reviews.objects.get(paper_id=paper_id)
            additional_info["is_allocated"] = True
        except models.Reviews.DoesNotExist as e:
            additional_info["is_allocated"] = False

        papers_additional_info[paper_id] = additional_info

    
    paperstatus_dict = dict()
    for key, value in models.Paper.PaperStatus.choices:
        paperstatus_dict[key] = value
        
    context = {"islogged_in":islogged_in,"is_admin_logged_in":False,"user_type":request.COOKIES.get('user_type'),
                "papers":papers, "paperstatus_dict":paperstatus_dict, "papers_additional_info":papers_additional_info}

    return render(request,"conferencechair_listpapers.html", context)

#view biddings of papers
def conferencechair_view_bidding(request):
    #requires: paper_id = id of selected paper
    #returns: paper = details of selected paper
    #returns: reviewers = list of all the reviewers
    #returns: reviewer_additional_info = nested dictionary of additional values for reviewers.
    #                                    dict(int reviewer_user_id, dict(string key, ? value))
    #                                                           ^ "isAllocated", "isBid", "unreviewed_num"

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

            try:
                user_bid = models.Bids.objects.get(reviewer_user_id=reviewer.user_id, paper_id=paper_id)
                additional_info["is_bid"] = user_bid.is_bidding
            except models.Bids.DoesNotExist as e:
                additional_info["is_bid"] = False

            try:
                user_reviews = models.Reviews.objects.get(reviewer_user_id=reviewer.user_id, paper_id=paper_id)
                additional_info["is_allocated"] = True
            except models.Reviews.DoesNotExist as e:
                additional_info["is_allocated"] = False

            try:
                unreviewed_num = len(models.Reviews.objects.get(reviewer_user_id=reviewer.user_id, reviewer_rating=models.Reviews.Rating.UNRATED))
                additional_info["unreviewed_num"] = unreviewed_num
            except models.Reviews.DoesNotExist as e:
                additional_info["unreviewed_num"] = 0

            reviewer_additional_info[reviewer.user_id] = additional_info

        context = {"islogged_in":islogged_in,"is_admin_logged_in":False,"user_type":request.COOKIES.get('user_type'),
                    "paper":paper, "reviewers":reviewers, "reviewer_additional_info":reviewer_additional_info}

        return render(request,"conferencechair_listpapers.html", context)

#allocate paper to reviewer
def conferencechair_allocate(request):
    islogged_in = controller_util.check_login(request)
    is_conferencechair_logged_in = check_conferencechair_login(request)

    if not (islogged_in and is_conferencechair_logged_in):
        conferencechair_error_handle(request)

    if request.method == "POST":
        paper_id = request.POST.get('paper_id')
        name = request.POST.get('name')

        ''' 
            first is to go to paper page(?) and view a list of papers available to be allocated
            maybe there's like a button(?) for the conference chair to select and assign the paper to the reviewer_homepage

            or it is to go to the reviewer page and have a assign button where the conference chair 
            clicks and selects reviewer to assign to  

            
            '''
        paper = models.Paper.objects.get(paper_id=paper_id)

        reviewer = models.Reviewer.objects.get(name=name)
        #(no idea) the paper will be allocated to the reviewer, thats why i included paper.append(reviewer)
        paper.append(reviewer)

        return conferencechair_allocate(request, "Paper assigned to reviewer.")

def conferencechair_view_paper_ratingreview(request):
    islogged_in = controller_util.check_login(request)
    is_conferencechair_logged_in = check_conferencechair_login(request)

    if not (islogged_in and is_conferencechair_logged_in):
        conferencechair_error_handle(request)
    """
    View paper page, view paper and upon clicking will display review and rating
    """
    if request.method == "POST":
        paper_id = request.POST.get('paper_id')
        paper = models.Paper.objects.get(paper_id=paper_id)

        paper.paper_details = request.POST.get('paper_details')
        paper.display()

        return conferencechair_view_paper_ratingreview(request)



    

