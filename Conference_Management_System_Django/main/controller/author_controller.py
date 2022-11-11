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
def author_error_handle(request):
    response = render(request, "login.html", {"islogged_in": False, "is_admin_logged_in":False, 'message':'You are not an author.'})
    response.delete_cookie('user_type')
    response.delete_cookie('email')
    response.delete_cookie('password')
    return response

def check_author_login(request):
    return controller_util.check_type_login(request, models.User.UserType.USERTYPE_AUTHOR)

def author_start_new_paper(request, message):
    #requires: nothing
    #returns: nothing
    islogged_in = controller_util.check_login(request)
    is_author_logged_in = check_author_login(request)

    if not (islogged_in and is_author_logged_in):
        return author_error_handle(request)
    
    context = {"islogged_in":islogged_in,"is_admin_logged_in":False,"user_type":request.COOKIES.get('user_type')}
    
    if message != None:
        context["message"] = message

    return render(request,"author_newpaper.html", context)

def author_StartNewPaper(request):
    #requires: author_emails = emails of all the selected authors, split by ',' excluding own email
    #returns: nothing

    islogged_in = controller_util.check_login(request)
    is_author_logged_in = check_author_login(request)

    if not (islogged_in and is_author_logged_in):
        return author_error_handle(request)
    
    if request.method == "POST":

        user_emails = request.POST.get('author_emails').strip().split(",")
        user_emails.append(request.COOKIES.get('email'))
        author_list = list()
        for email in user_emails:
            email = email.strip()
            if email == "":
                continue
            
            try:
                author = models.Author.objects.get(login_email=email)
                author_list.append(author)
            except models.Author.DoesNotExist as e:
                return author_start_new_paper(request, "Author account with the specified email does not exist.")

        new_paper = models.Paper.objects.create()

        for author in author_list:
            models.Authors.objects.create(author_user_id=author.user_id, paper_id=new_paper.paper_id)

        return author_start_new_paper(request, "Paper successfully created.")

def author_list_papers(request, message=None):
    #requires: nothing
    #returns: authored_papers = list of all the papers that user is listed as author of
    islogged_in = controller_util.check_login(request)
    is_author_logged_in = check_author_login(request)

    if not (islogged_in and is_author_logged_in):
        return author_error_handle(request)

    email = request.COOKIES.get('email')
    author = models.Author.objects.get(login_email=email)

    all_writes = models.Writes.objects.get(author_user_id=author.user_id)
    authored_papers = list()
    for writes in all_writes:
        paper = models.Paper.objects.get(paper_id=writes.paper_id)
        authored_papers.append(paper)

    context = {"islogged_in":islogged_in,"is_admin_logged_in":False,"user_type":request.COOKIES.get('user_type'), "authored_papers":authored_papers}
    return render(request,"author_listpapers.html", context)

def author_view_paper(request, message=None):
    #requires: paper_id = id of selected paper
    #returns: selected_paper = all the details of the paper that the user selected
    islogged_in = controller_util.check_login(request)
    is_author_logged_in = check_author_login(request)

    if not (islogged_in and is_author_logged_in):
        return author_error_handle(request)
        
    context = {"islogged_in":islogged_in,"is_admin_logged_in":False,"user_type":request.COOKIES.get('user_type')}

    if request.method == "POST":
        paper_id = request.POST.get('paper_id')

        author = models.Author.objects.get(login_email=request.COOKIES.get('email'))

        try:
            writes = models.Writes.objects.get(paper_id=paper_id, author_user_id=author.user_id)
            paper = models.Paper.objects.get(paper_id=paper_id)
            context["selected_paper"] = paper
        except models.Writes.DoesNotExist as e:
            return author_list_papers(request, "Not author of selected paper")

    if message != None:
        context["message"] = message

    return render(request,"author_viewpaper.html", context)

def author_SavePaper(request):
    #requires: paper_id = id of selected paper
    #returns: selected_paper = all the details of the paper that the user selected
    islogged_in = controller_util.check_login(request)
    is_author_logged_in = check_author_login(request)

    if not (islogged_in and is_author_logged_in):
        return author_error_handle(request)
    
    if request.method == "POST":
        paper_id = request.POST.get('paper_id')
        author = models.Author.objects.get(login_email=request.COOKIES.get('email'))

        try:
            writes = models.Writes.objects.get(paper_id=paper_id, author_user_id=author.user_id)
            paper = models.Paper.objects.get(paper_id=paper_id)
            paper.paper_name = request.POST.get('new_name')
            paper.paper_details = request.POST.get('new_details')
            paper.save()

            return author_view_paper(request, "Paper successfully saved")
        except models.Writes.DoesNotExist as e:
            return author_list_papers(request, "Not author of selected paper")
            

