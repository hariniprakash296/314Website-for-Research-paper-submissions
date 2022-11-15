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

def author_start_new_paper(request, message=None):
    #requires: nothing
    #returns: nothing
    islogged_in = controller_util.check_login(request)
    is_author_logged_in = check_author_login(request)

    if not (islogged_in and is_author_logged_in):
        return author_error_handle(request)
    
    context = {"islogged_in":islogged_in,"is_admin_logged_in":False,"user_type":request.COOKIES.get('user_type')}
    
    if message != None and not "message" in context:
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
                return author_start_new_paper(request, "Author account with the email '"+email+"' does not exist.")

        new_paper = models.Paper.objects.create()

        for author in author_list:
            #models.Authors.objects.create(author_user_id=author.user_id, paper_id=new_paper.paper_id)
            models.Writes.objects.create(author_user_id=author, paper_id=new_paper)

        return author_start_new_paper(request, "Paper successfully created.")

def author_list_papers(request, message=None):
    #requires: nothing
    #returns: authored_papers = list of all the papers that user is listed as author of
    #return: paperstatus_dict

    islogged_in = controller_util.check_login(request)
    is_author_logged_in = check_author_login(request)

    if not (islogged_in and is_author_logged_in):
        return author_error_handle(request)

    email = request.COOKIES.get('email')
    author = models.Author.objects.get(login_email=email)

    authored_papers = list()
    try:
        all_writes = models.Writes.objects.filter(author_user_id=author.user_id)

        for writes in all_writes:
            authored_papers.append(writes.paper_id)
    except models.Writes.DoesNotExist as e:
        print("No written papers.")

    
    paperstatus_dict = dict()
    for key, value in models.Paper.PaperStatus.choices:
        paperstatus_dict[key] = value

    context = {"islogged_in":islogged_in,"is_admin_logged_in":False,"user_type":request.COOKIES.get('user_type'), "authored_papers":authored_papers}

    context['paperstatus_dict'] = paperstatus_dict
    if message != None and not "message" in context:
        context["message"] = message

    return render(request,"author_listpapers.html", context)

def author_view_paper(request, message=None):
    #requires: paper_id = id of selected paper
    #returns: selected_paper = all the details of the paper that the user selected
    #returns: author_emails_string = string of all the emails joined

    islogged_in = controller_util.check_login(request)
    is_author_logged_in = check_author_login(request)

    if not (islogged_in and is_author_logged_in):
        return author_error_handle(request)
        
    context = {"islogged_in":islogged_in,"is_admin_logged_in":False,"user_type":request.COOKIES.get('user_type')}

    if request.method == "POST":
        paper_id = request.POST.get('paper_id')

        author = models.Author.objects.get(login_email=request.COOKIES.get('email'))

        try:
            writes = models.Writes.objects.get(paper_id=paper_id, author_user_id=author)
            paper = writes.paper_id
            context["selected_paper"] = paper

            print(paper.paper_details)

        except models.Writes.DoesNotExist as e:
            return author_list_papers(request, "Not author of selected paper")

        writes = models.Writes.objects.filter(paper_id=paper_id)
        author_emails = list()
        for write in writes:
            author_emails.append(write.author_user_id.login_email)

    context['author_emails_string'] = ",".join(author_emails)
    print(context['author_emails_string'])

    if message != None and not "message" in context:
        context["message"] = message

    return render(request,"author_viewpaper.html", context)

def author_SavePaper(request):
    #requires: paper_id = id of selected paper
    #requires: new_name = name of selected paper
    #requires: new_details = details of selected paper
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
            paper = writes.paper_id
            
            if paper.status != models.Paper.PaperStatus.PAPERSTATUS_NOTSUBMITTED:
                return author_view_paper(request, "Error. Paper has already been submitted.")

            paper.paper_name = request.POST.get('new_name')
            paper.paper_details = request.POST.get('new_details')
            paper.save()

            return author_view_paper(request, "Paper successfully saved")
        except models.Writes.DoesNotExist as e:
            return author_list_papers(request, "Not author of selected paper")
            
def author_SubmitPaper(request):
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
            paper = writes.paper_id

            if paper.status != models.Paper.PaperStatus.PAPERSTATUS_NOTSUBMITTED:
                return author_view_paper(request, "Paper has already been submitted.")

            paper.paper_name = request.POST.get('new_name')
            paper.paper_details = request.POST.get('new_details')
            paper.status = models.Paper.PaperStatus.PAPERSTATUS_SUBMITTEDPENDING
            paper.save()

            return author_view_paper(request, "Paper successfully submitted.")
        except models.Writes.DoesNotExist as e:
            return author_list_papers(request, "Not author of selected paper.")
