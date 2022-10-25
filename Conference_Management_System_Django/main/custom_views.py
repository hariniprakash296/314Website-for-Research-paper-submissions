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

email_lock = Lock()

#utility funcs
def check_login(request):
    if request.COOKIES.get('password'):
        return True
    else:
        return False
def check_admin_login(request):
    if request.COOKIES.get('password') == hash_string('admin') and request.COOKIES.get('user_type') == hash_string('admin'):
        return True
    else:
        return False
def hash_string(string):
    return hashlib.sha224(string.encode('utf-8')).hexdigest()

def create_login_cookies(response,email,hashed_password,non_hashed_user_type):
    max_age = 60 * 30
    hashed_user_type = hash_string(non_hashed_user_type)
    expires = datetime.datetime.strftime(datetime.datetime.utcnow() + datetime.timedelta(seconds=max_age),
                                         "%a, %d-%b-%Y %H:%M:%S GMT")
    response.set_cookie(key="email", value=email, max_age=max_age, expires=expires)
    response.set_cookie(key="password", value=hashed_password, max_age=max_age, expires=expires)
    response.set_cookie(key="user_type", value=hashed_user_type, max_age=max_age, expires=expires)
	
#view funcs	
def index(request):
    islogged_in = check_login(request)
    is_admin_logged_in = check_admin_login(request)
    return render(request,"index.html",{"islogged_in":islogged_in,"is_admin_logged_in":is_admin_logged_in,"user_type":request.COOKIES.get('user_type')})
	
def login(request):
    islogged_in = check_login(request)
    is_admin_logged_in = check_admin_login(request)
    return render(request,"login.html",{"islogged_in":islogged_in,'message':"","is_admin_logged_in":is_admin_logged_in,"user_type":request.COOKIES.get('user_type')})
def login_handle(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        if email == 'admin' and password == 'admin':
            chairs = models.Chair.objects.all()
            reviewers = models.Reviewer.objects.all()
            context = {"islogged_in":True,"is_admin_logged_in":True,"chairs":chairs,
                                                                         "reviewers":reviewers,"user_type":request.COOKIES.get('user_type')}
            response = render(request,"chair_reviewer_application.html",context)
            hashed_admin_password = hash_string('admin')
            create_login_cookies(response,'admin',hashed_admin_password,'admin')
            return response
        else:
            password = password.encode('utf-8')
            hashed_password = hashlib.sha224(password).hexdigest()
            user_type = None
            max_age = 60 * 30
            try:
                user = models.User.objects.get(login_email=email,login_pw=hashed_password)
                user_type = user.user_type
                try:
                    if user_type == '0':
                        #0 = system admin
                        template_name = "admin_homepage.html"
                        
                    elif user_type == '1':
                        #1 = conference chair
                        template_name = "conference_chair_homepage.html"
                        
                    elif user_type == '2':
                        #2 = reviewer
                        template_name = "reviewer_homepage.html"
                        
                    elif user_type == '3':
                        #3 = author
                        template_name = "author_homepage.html"
                        
                    hashed_user_type = hashlib.sha224(user_type.encode('utf-8')).hexdigest()
                    context = {"islogged_in":True,"user_type":hash_string(user_type)}
                    response = render(request, template_name, context)
                    expires = datetime.datetime.strftime(datetime.datetime.utcnow() + datetime.timedelta(seconds=max_age),
                                                         "%a, %d-%b-%Y %H:%M:%S GMT")
                    response.set_cookie(key="email", value=email, max_age=max_age, expires=expires)
                    response.set_cookie(key="password", value=hashed_password, max_age=max_age, expires=expires) 
                    response.set_cookie(key="user_type", value=hashed_user_type, max_age=max_age, expires=expires)
                    
                    return response
                except Exception as e:
                    return HttpResponse("Unexpected error. Exception : ",e)
            except Exception as e:
                # Non existing user
                print(e)
                return render(request,"login.html",{"islogged_in":False, 'message':'Bad Authentication.', "is_admin_logged_in":False
                                                    , "user_type":request.COOKIES.get('user_type')})
													
def logout_handle(request):
    response = render(request, "login.html", {"islogged_in": False,"is_admin_logged_in":False})
    response.delete_cookie('user_type')
    response.delete_cookie('email')
    response.delete_cookie('password')
    return response
