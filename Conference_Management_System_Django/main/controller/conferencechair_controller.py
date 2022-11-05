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

def conferencechair_view_bidding(request):
    islogged_in = controller_util.check_login(request)
    is_conferencechair_logged_in = check_conferencechair_login(request)

    if not (islogged_in and is_conferencechair_logged_in):
        conferencechair_error_handle(request)

    ''' 
    first is to find the name of the reviewer
    then view the reviewer's bidding and workload    
    '''
    
    if request.method == "POST":
        name = request.POST.get('name')
        max_papers = request.POST.get('maxpapers')
        workload = models.Reviewer.get_max_papers(max_papers=max_papers)

        user = models.Reviewer.objects.get(name=name)
        user.bidding = request.POST.get('bidding')
        user.workload = request.POST.get('workload')

        return conferencechair_view_bidding(request, "Reviewer's bidding and preferred workload displayed.")

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



    

