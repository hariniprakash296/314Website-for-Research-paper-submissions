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
def commentor_error_handle(request):
    response = render(request, "login.html", {"islogged_in": False, "is_admin_logged_in":False, 'message':'You do not have the permission to comment.'})
    response.delete_cookie('user_type')
    response.delete_cookie('email')
    response.delete_cookie('password')
    return response

def check_commentor_login(request):
    return controller_util.check_type_login(request, models.User.UserType.USERTYPE_REVIEWER) #or controller_util.check_type_login(request, models.User.UserType.USERTYPE_AUTHOR) 

def is_reviewer_is_author(request):
    user_type = request.COOKIES.get('user_type')

    is_reviewer = user_type == controller_util.hash_string(str(models.User.UserType.USERTYPE_REVIEWER))
    is_author = user_type == controller_util.hash_string(str(models.User.UserType.USERTYPE_AUTHOR))
    
    return (is_reviewer, is_author)
    
def get_appropriate_user(request):
    email = request.COOKIES.get('email')
    is_reviewer, is_author = is_reviewer_is_author(request)

    if is_reviewer: # or is_author:
        return models.User.objects.get(login_email=email)

    return None

def commentor_view_fully_reviewed_papers(request, message=None):
    #requires: nothing
    #returns: fully_reviewed_papers = list of all the papers that have been rated by both reviewer and author
    islogged_in = controller_util.check_login(request)
    is_commentor_logged_in = check_commentor_login(request)

    if not (islogged_in and is_commentor_logged_in):
        return commentor_error_handle(request)
    
    context = {"islogged_in":islogged_in,"is_admin_logged_in":False,"user_type":request.COOKIES.get('user_type')}

    user = get_appropriate_user(request)
    if user == None:
        return commentor_error_handle(request)

    papers = models.Paper.objects.exclude(status=models.Paper.PaperStatus.PAPERSTATUS_NOTSUBMITTED).exclude(status=models.Paper.PaperStatus.PAPERSTATUS_SUBMITTEDPENDING)

    fully_reviewed_papers = list()
    for paper in papers:
        paper_id = paper.paper_id

        fully_reviewed = paper.is_paper_reviews_author_rated()

        if fully_reviewed:
            fully_reviewed_papers.append(paper)

    context['fully_reviewed_papers'] = fully_reviewed_papers
    
    paperstatus_dict = dict()
    for key, value in models.Paper.PaperStatus.choices:
        paperstatus_dict[key] = value
    context['paperstatus_dict'] = paperstatus_dict

    if message != None and not "message" in context:
        context["message"] = message

    return render(request,"commentor_fullyreviewedpapers.html", context)

def commentor_view_reviews(request, message=None):
    #requires: paper_id
    #returns: paper = selected paper
    #returns: reviews = list of all the reviews in selected paper
    #returns: reviewcomment_count = dict of the number of comments each review has
    #returns: reviewrating_dict = dict of the ratings' labels
    islogged_in = controller_util.check_login(request)
    is_commentor_logged_in = check_commentor_login(request)

    if not (islogged_in and is_commentor_logged_in):
        return commentor_error_handle(request)
    
    context = {"islogged_in":islogged_in,"is_admin_logged_in":False,"user_type":request.COOKIES.get('user_type')}

    user = get_appropriate_user(request)
    if user == None:
        return commentor_error_handle(request)

    if request.method == "POST":
        paper_id = request.POST.get('paper_id')
        paper = models.Paper.objects.get(paper_id=paper_id)
        reviews = models.Reviews.objects.filter(paper_id=paper_id)
        reviewcomment_count = dict()
        for review in reviews:
            reviewcomment_count[review.review_id] = len(models.ReviewComments.objects.filter(review_id=review))

        context['paper'] = paper
        context['reviews'] = reviews
        context['reviewcomment_count'] = reviewcomment_count
        context["authors"] = models.Writes.get_names_of_authors(paper.paper_id)

    reviewrating_dict = dict()
    for key, value in models.Reviews.Rating.choices:
        reviewrating_dict[key] = value
    context["reviewrating_dict"] = reviewrating_dict

    if message != None and not "message" in context:
        context["message"] = message

    return render(request,"commentor_viewreviews.html", context)

def commentor_view_review_comments(request, message=None):
    #requires: review_id = id of the selected review
    #returns: paper = selected paper
    #returns: review = selected review
    #returns: reviewcomments = list of comments of the selected review
    #returns: reviewrating_dict = dict of the ratings' labels
    islogged_in = controller_util.check_login(request)
    is_commentor_logged_in = check_commentor_login(request)

    if not (islogged_in and is_commentor_logged_in):
        return commentor_error_handle(request)
    
    context = {"islogged_in":islogged_in,"is_admin_logged_in":False,"user_type":request.COOKIES.get('user_type')}

    user = get_appropriate_user(request)
    if user == None:
        return commentor_error_handle(request)

    if request.method == "POST":
        review_id = request.POST.get('review_id')
        
        review = models.Reviews.objects.get(review_id=review_id)
        paper = review.paper_id

        reviewcomments = models.ReviewComments.objects.filter(review_id=review_id)
            
        context['paper'] = paper
        context['review'] = review
        context['reviewcomments'] = reviewcomments
        context["authors"] = models.Writes.get_names_of_authors(paper.paper_id)

        
    reviewrating_dict = dict()
    for key, value in models.Reviews.Rating.choices:
        reviewrating_dict[key] = value
    context["reviewrating_dict"] = reviewrating_dict

    if message != None and not "message" in context:
        context["message"] = message

    return render(request,"commentor_viewreviewcomments.html", context)

def commentor_add_comment(request):
    #requires: review_id = id of the selected review
    #returns: review = selected review
    #returns: reviewrating_dict = dict of the ratings' labels
    islogged_in = controller_util.check_login(request)
    is_commentor_logged_in = check_commentor_login(request)

    if not (islogged_in and is_commentor_logged_in):
        return commentor_error_handle(request)
    
    context = {"islogged_in":islogged_in,"is_admin_logged_in":False,"user_type":request.COOKIES.get('user_type')}

    user = get_appropriate_user(request)
    if user == None:
        return commentor_error_handle(request)

    if request.method == "POST":
        review_id = request.POST.get('review_id')
        
        review = models.Reviews.objects.get(review_id=review_id)
        paper = review.paper_id

        context['paper'] = paper
        context['review'] = review
        context["authors"] = models.Writes.get_names_of_authors(paper.paper_id)
        
    reviewrating_dict = dict()
    for key, value in models.Reviews.Rating.choices:
        reviewrating_dict[key] = value
    context["reviewrating_dict"] = reviewrating_dict

    return render(request,"commentor_addcomment.html", context)

def commentor_AddComment(request):
    #requires: review_id = id of the selected review
    #requires: comment_text = text of your comment
    #returns: review = selected review
    #returns: reviewcomments = list of comments of the selected review
    #returns: reviewrating_dict = dict of the ratings' labels
    islogged_in = controller_util.check_login(request)
    is_commentor_logged_in = check_commentor_login(request)

    if not (islogged_in and is_commentor_logged_in):
        return commentor_error_handle(request)

    user = get_appropriate_user(request)
    if user == None:
        return commentor_error_handle(request)
  
    if request.method == "POST":
        review_id = request.POST.get('review_id')
        comment_text = request.POST.get('comment_text')
        
        review = models.Reviews.objects.get(review_id=review_id)
        models.ReviewComments.objects.create(review_id=review, commenter_user_id=user, comment_text=comment_text)

    return commentor_view_review_comments(request, "Your comment has been added.")
