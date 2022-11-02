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
def admin_error_handle(request):
    response = render(request, "login.html", {"islogged_in": False, "is_admin_logged_in":False, 'message':'You are not a system admin.'})
    response.delete_cookie('user_type')
    response.delete_cookie('email')
    response.delete_cookie('password')
    return response


def admin_create_user(request):
    islogged_in = controller_util.check_login(request)
    is_admin_logged_in = controller_util.check_admin_login(request)

    if islogged_in and is_admin_logged_in:
        return render(request,"sign_up.html",{"islogged_in":islogged_in,"is_admin_logged_in":is_admin_logged_in,"user_type":request.COOKIES.get('user_type')})
    else:
        admin_error_handle(request)

def admin_AddUserProfile(request):
    islogged_in = controller_util.check_login(request)
    is_admin_logged_in = controller_util.check_admin_login(request)
    if not islogged_in or not is_admin_logged_in:
        admin_error_handle(request)
    if request.method == "POST":
        # TODO add form checks here or in html as javascript
        user_type = request.POST.get('user_type')
        email = request.POST.get('email')
        name = request.POST.get('name')
        password = request.POST.get('password').encode('utf-8')
        hashed_password = hashlib.sha224(password).hexdigest()
        context = {"islogged_in": False,"is_admin_logged_in":is_admin_logged_in,"user_type":request.COOKIES.get('user_type')}

        if user_type == "System Admin":
            #0 = system admin
            models.Author.objects.create(login_email=email, login_pw=hashed_password, name=name, type=models.User.UserType.USERTYPE_SYSTEMADMIN)
            
        elif user_type == "Conference Chair":
            #1 = conference chair
            models.ConferenceChair.objects.create(login_email=email, login_pw=hashed_password, name=name, type=models.User.UserType.USERTYPE_CONFERENCECHAIR)
            
        elif user_type == "Reviewer":
            #2 = reviewer
            max_papers = int(request.POST.get('max_papers'))
            models.Reviewer.objects.create(login_email=email, login_pw=hashed_password, name=name, max_papers=max_papers, type=models.User.UserType.USERTYPE_REVIEWER)
            
        elif user_type == "Author":
            #3 = author
            models.Author.objects.create(login_email=email, login_pw=hashed_password, name=name, type=models.User.UserType.USERTYPE_AUTHOR)

        return render(request, "sign_up_handle.html", context)
        
        """
        # if user_type == "author":
        #     context['islogged_in'] = True
        #     user = models.User(email=email,password=hashed_password, type="author")
        #     user.save()
        #     author = models.Author(email=email,password=hashed_password, name=name)
        #     author.save()

        #     response = render(request, "sign_up_handle.html", context)
        #     create_login_cookies(response,email,author.password,'author')
        #     email_send_thread = Thread(target=Utils.send_email, args=("About your registration to conference management system",
        #                                                                "You have been registered as an author",
        #                                                               author.email,
        #                                                                email_lock
        #                                                                ))
        #     email_send_thread.start()

        # else:
        #     response = render(request, "sign_up_handle.html", context)

        #     if user_type == "chair":
        #         is_chair = True
        #         user = models.User(email=email, password=hashed_password, type="chair")
        #         user.save()
        #         chair = models.Chair(email=email, password=hashed_password, name=name)
        #         chair.save()

        #     elif user_type == "reviewer":
        #         is_chair = False
        #         user = models.User(email=email, password=hashed_password, type="reviewer")
        #         user.save()
        #         reviewer = models.Reviewer(email=email, password=hashed_password, name=name)
        #         reviewer.save()
        #     email_send_thread = Thread(target=Utils.send_email_for_user_sign_up, args=(is_chair,
        #                                                                                email,
        #                                                                                email_lock
        #                                                                                ))
        #     email_send_thread.start()
        # return response
        """

def admin_SearchUser(request):
    islogged_in = controller_util.check_login(request)
    is_admin_logged_in = controller_util.check_admin_login(request)

    if not islogged_in or not is_admin_logged_in:
        admin_error_handle(request)

    if request.method == "POST":
        if request.POST.get('name'):
            searched_name = request.POST.get('name')
            users = models.User.objects.filter(Q(name__contains=searched_name))
        else:
            users = models.User.objects.all()

        return render(request, ,{"islogged_in":islogged_in,"is_admin_logged_in":is_admin_logged_in,"user_type":request.COOKIES.get('user_type'), "users":users})

def admin_view_users(request):
    islogged_in = controller_util.check_login(request)
    is_admin_logged_in = controller_util.check_admin_login(request)

    if not islogged_in or not is_admin_logged_in:
        admin_error_handle(request)

    if request.method == "POST":
        if request.POST.get('user_type'):
            user_type = int(request.POST.get('user_type'))
            if user_type == models.User.UserType.USERTYPE_SYSTEMADMIN:
                #0 = system admin
                users = models.SystemAdmin.objects.all()
                #users = models.User.objects.instance_of(SystemAdmin)

            elif user_type == models.User.UserType.USERTYPE_CONFERENCECHAIR:
                #1 = conference chair
                users = models.ConferenceChair.objects.all()
                
            elif user_type == models.User.UserType.USERTYPE_REVIEWER:
                #2 = reviewer
                users = models.Reviewer.objects.all()
                
            elif user_type == models.User.UserType.USERTYPE_AUTHOR:
                #3 = author
                users = models.Author.objects.all()
        else:
            users = models.User.objects.all()

        return render(request, ,{"islogged_in":islogged_in,"is_admin_logged_in":is_admin_logged_in,"user_type":request.COOKIES.get('user_type'), "users":users})

def admin_UpdateUser(request):
    islogged_in = controller_util.check_login(request)
    is_admin_logged_in = controller_util.check_admin_login(request)

    if not islogged_in or not is_admin_logged_in:
        admin_error_handle(request)

    if request.method == "POST":
        # TODO add form checks here or in html as javascript
        user_id = request.POST.get('user_id')
        
        user = models.User.objects.get(user_id=user_id)
        user_type = user.user_type

        if user_type == models.User.UserType.USERTYPE_SYSTEMADMIN:
            #0 = system admin
            user = models.SystemAdmin.objects.get(user_id=user_id)
            
        elif user_type == models.User.UserType.USERTYPE_CONFERENCECHAIR:
            #1 = conference chair
            user = models.ConferenceChair.objects.get(user_id=user_id)
            
        elif user_type == models.User.UserType.USERTYPE_REVIEWER:
            #2 = reviewer
            user = models.Reviewer.objects.get(user_id=user_id)
            
        elif user_type == models.User.UserType.USERTYPE_AUTHOR:
            #3 = author
            user = models.Author.objects.get(user_id=user_id)

        return render(request, ,{"islogged_in":islogged_in,"is_admin_logged_in":is_admin_logged_in,"user_type":request.COOKIES.get('user_type'), "selected_user":user})

def admin_SuspendUser(request):

