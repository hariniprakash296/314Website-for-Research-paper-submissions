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

def check_admin_login(request):
    return controller_util.check_type_login(request, models.User.UserType.USERTYPE_SYSTEMADMIN)

def admin_create_user(request):
    islogged_in = controller_util.check_login(request)
    is_admin_logged_in = check_admin_login(request)

    if islogged_in and is_admin_logged_in:
        return render(request,"admin_register.html",{"islogged_in":islogged_in,"is_admin_logged_in":is_admin_logged_in,"user_type":request.COOKIES.get('user_type')})
    else:
        return admin_error_handle(request)

def admin_AddUserProfile(request):
    islogged_in = controller_util.check_login(request)
    is_admin_logged_in = check_admin_login(request)
    if not (islogged_in and is_admin_logged_in):
        return admin_error_handle(request)

    if request.method == "POST":
        # TODO add form checks here or in html as javascript
        user_type = request.POST.get('user_type')
        email = request.POST.get('email').strip().lower()
        password = request.POST.get('password').strip().encode('utf-8')
        name = request.POST.get('name').strip()
        max_papers = request.POST.get('max_papers')

        context = {"islogged_in": islogged_in,"is_admin_logged_in":is_admin_logged_in,"user_type":request.COOKIES.get('user_type')}
        
        if user_type == None or len(email) == 0 or len(password) == 0 or len(name) == 0 or (user_type == "reviewer" and len(max_papers) == 0):
            context["message"] = "Please fill all fields."
            return render(request, "admin_register.html", context)

        if user_type == "reviewer": 
            max_papers = int(max_papers.strip())
            if max_papers < 1:
                context["message"] = "Reviewer max paper number must be a positive integer."
                return render(request, "admin_register.html", context)

        hashed_password = hashlib.sha224(password).hexdigest()
        try:
            user = models.User.objects.get(login_email=email)
            context["message"] = "Account with the specified email already exists."

        except models.User.DoesNotExist as e:
            if user_type == "admin":
                #0 = system admin
                models.SystemAdmin.objects.create(login_email=email, login_pw=hashed_password, name=name, user_type=models.User.UserType.USERTYPE_SYSTEMADMIN)
                
            elif user_type == "chair":
                #1 = conference chair
                models.ConferenceChair.objects.create(login_email=email, login_pw=hashed_password, name=name, user_type=models.User.UserType.USERTYPE_CONFERENCECHAIR)
                
            elif user_type == "reviewer":
                #2 = reviewer
                models.Reviewer.objects.create(login_email=email, login_pw=hashed_password, name=name, max_papers=max_papers, user_type=models.User.UserType.USERTYPE_REVIEWER)
                
            elif user_type == "author":
                #3 = author
                models.Author.objects.create(login_email=email, login_pw=hashed_password, name=name, user_type=models.User.UserType.USERTYPE_AUTHOR)
            
            #print(e)
            context["message"] = "User successfully created."

            
        return render(request, "admin_register.html", context)

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

def admin_ViewAllUsers(request):
    islogged_in = controller_util.check_login(request)
    is_admin_logged_in = check_admin_login(request)

    if not (islogged_in and is_admin_logged_in):
        return admin_error_handle(request)

    if request.method != "POST" or not request.POST.get('user_type'):
        users = models.User.objects.all()
    else:
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

    usertype_dict = dict()
    for key, value in models.User.UserType.choices:
        usertype_dict[key] = value

    return render(request, "admin_listuser.html",{"islogged_in":islogged_in,"is_admin_logged_in":is_admin_logged_in,"user_type":request.COOKIES.get('user_type'), 
        "users":users, "usertype_dict":usertype_dict})

def admin_SearchUsers(request):
    islogged_in = controller_util.check_login(request)
    is_admin_logged_in = check_admin_login(request)

    if not (islogged_in and is_admin_logged_in):
        return admin_error_handle(request)

    if request.method == "POST":
        if request.POST.get('name'):
            searched_name = request.POST.get('name')
            users = models.User.objects.filter(Q(name__contains=searched_name))
        else:
            users = models.User.objects.all()

        return render(request, "admin_listuser.html",{"islogged_in":islogged_in,"is_admin_logged_in":is_admin_logged_in,"user_type":request.COOKIES.get('user_type'), "users":users})

def admin_ViewUser(request, message=None):
    islogged_in = controller_util.check_login(request)
    is_admin_logged_in = check_admin_login(request)

    if not (islogged_in and is_admin_logged_in):
        return admin_error_handle(request)

    if request.method == "POST":
        # TODO add form checks here or in html as javascript
        user_id = request.POST.get('user_id')
        
        template = "admin_viewuser.html"
        context = {"islogged_in":islogged_in,"is_admin_logged_in":is_admin_logged_in,"user_type":request.COOKIES.get('user_type')}
        try:
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

            context["selected_user"] = user

        except models.User.DoesNotExist as e:
            template = "admin_listuser.html"
            context["message"] = "Failed to retrieve user."

        if message != None and not "message" in context:
            context["message"] = message

        return render(request, template, context)

def admin_UpdateUser(request):
    islogged_in = controller_util.check_login(request)
    is_admin_logged_in = check_admin_login(request)

    if not (islogged_in and is_admin_logged_in):
        return admin_error_handle(request)

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

        new_user_type = None
        new_user_type_str = request.POST.get('new_user_type')
        if new_user_type_str == "admin":
            #0 = system admin
            new_user_type = models.User.UserType.USERTYPE_SYSTEMADMIN
            
        elif new_user_type_str == "chair":
            #1 = conference chair
            new_user_type = models.User.UserType.USERTYPE_CONFERENCECHAIR
            
        elif new_user_type_str == "reviewer":
            #2 = reviewer
            new_user_type = models.User.UserType.USERTYPE_REVIEWER
            
        elif new_user_type_str == "author":
            new_user_type = models.User.UserType.USERTYPE_AUTHOR
            
        user.login_email = request.POST.get('new_email')
        user.name = request.POST.get('new_name')
        user.user_type = new_user_type
        
        password = request.POST.get('new_password').strip()
        if password != None and password != "":
            hashed_password = hashlib.sha224(password.encode('utf-8')).hexdigest()
            user.login_pw = hashed_password
        user.save()

        return admin_ViewUser(request, "User successfully edited.")

def admin_SuspendUser(request):
    islogged_in = controller_util.check_login(request)
    is_admin_logged_in = check_admin_login(request)

    if not (islogged_in and is_admin_logged_in):
        return admin_error_handle(request)

    if request.method == "POST":
        # TODO add form checks here or in html as javascript
        user_id = request.POST.get('user_id')
        
        user = models.User.objects.get(user_id=user_id)

        user.toggle_user_suspension()

        un_str = "un"
        if user.is_suspended:
            un_str = ""

        return admin_ViewUser(request, "User successfully "+un_str+"suspended.")

