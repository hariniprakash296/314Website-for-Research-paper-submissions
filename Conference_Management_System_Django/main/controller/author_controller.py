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
    #return: reviewed_authored_papers = dict whether paper has been fully reviewed
    #return: paperstatus_dict = dict of the statuses' labels

    islogged_in = controller_util.check_login(request)
    is_author_logged_in = check_author_login(request)

    if not (islogged_in and is_author_logged_in):
        return author_error_handle(request)

    email = request.COOKIES.get('email')
    author = models.Author.objects.get(login_email=email)
    

    context = {"islogged_in":islogged_in,"is_admin_logged_in":False,"user_type":request.COOKIES.get('user_type')}

    authored_papers = list()
    reviewed_authored_papers = dict()
    try:
        all_writes = models.Writes.objects.filter(author_user_id=author.user_id)

        for writes in all_writes:
            paper = writes.paper_id
            authored_papers.append(writes.paper_id)

            reviewed_authored_papers[paper.paper_id] = paper.is_paper_fully_reviewed()

    except models.Writes.DoesNotExist as e:
        context["message"] = "No written papers."

    context['authored_papers'] = authored_papers
    context['reviewed_authored_papers'] = reviewed_authored_papers
    
    paperstatus_dict = dict()
    for key, value in models.Paper.PaperStatus.choices:
        paperstatus_dict[key] = value
    context['paperstatus_dict'] = paperstatus_dict
    
    if message != None and not "message" in context:
        context["message"] = message

    return render(request,"author_listpapers.html", context)

def author_view_paper(request, message=None):
    #requires: paper_id = id of selected paper
    #returns: selected_paper = all the details of the paper that the user selected
    #returns: author_name_string = string of all the names joined

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

    context['author_name_string'] = models.Writes.get_names_of_authors(paper_id)

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

def author_view_all_reviews(request, message=None):
    #requires: paper_id = id of selected paper
    #returns: paper = selected paper
    #returns: reviews = all the reviews of the paper that the user selected
    #returns: reviewrating_dict = dict of the ratings' labels

    islogged_in = controller_util.check_login(request)
    is_author_logged_in = check_author_login(request)

    if not (islogged_in and is_author_logged_in):
        return author_error_handle(request)

    context = {"islogged_in":islogged_in,"is_admin_logged_in":False,"user_type":request.COOKIES.get('user_type')}

    if request.method == "POST":
        paper_id = request.POST.get('paper_id')

        paper = models.Paper.objects.get(paper_id=paper_id)
        context["paper"] = paper
        reviews = models.Reviews.objects.filter(paper_id=paper_id)
        context["reviews"] = reviews
        context["authors"] = models.Writes.get_names_of_authors(paper_id)

    reviewrating_dict = dict()
    for key, value in models.Reviews.Rating.choices:
        reviewrating_dict[key] = value
    context["reviewrating_dict"] = reviewrating_dict

    if message != None and not "message" in context:
        context["message"] = message

    return render(request,"author_viewallreviews.html", context)
    
def author_view_review(request, message=None):
    #requires: review_id = id of selected review
    #returns: review = the review that the user selected
    #returns: reviewrating_dict = dict of the ratings' labels

    islogged_in = controller_util.check_login(request)
    is_author_logged_in = check_author_login(request)

    if not (islogged_in and is_author_logged_in):
        return author_error_handle(request)

    context = {"islogged_in":islogged_in,"is_admin_logged_in":False,"user_type":request.COOKIES.get('user_type')}
    if request.method == "POST":
        review_id = request.POST.get('review_id')
        review = models.Reviews.objects.get(review_id=review_id)
        context["review"] = review    
        context["paper"] = review.paper_id
        context["authors"] = models.Writes.get_names_of_authors(review.paper_id)

    reviewrating_dict = dict()
    for key, value in models.Reviews.Rating.choices:
        reviewrating_dict[key] = value
    context["reviewrating_dict"] = reviewrating_dict

    return render(request,"author_viewreview.html", context)

def author_GiveRating(request):
    #requires: review_id = id of selected review
    #requires: rating = rating of the author to save
    #returns: review = the review that the user selected

    islogged_in = controller_util.check_login(request)
    is_author_logged_in = check_author_login(request)

    if not (islogged_in and is_author_logged_in):
        return author_error_handle(request)

    context = {"islogged_in":islogged_in,"is_admin_logged_in":False,"user_type":request.COOKIES.get('user_type')}
    if request.method == "POST":
        review_id = request.POST.get('review_id')
        review = models.Reviews.objects.get(review_id=review_id)
    
        rating = int(request.POST.get('rating'))
        
        if review.author_rating != models.Reviews.Rating.UNRATED:
            return author_view_review(request, "You have aleady rated this review.")

        if rating == models.Reviews.Rating.UNRATED:
            return author_view_review(request, "Please select a rating to give the paper.")

        review.author_rating = rating
        review.save()

        return author_view_all_reviews(request, "Successfully rated review.")