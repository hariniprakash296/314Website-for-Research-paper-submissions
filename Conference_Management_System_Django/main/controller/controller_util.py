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
    if request.COOKIES.get('user_type') == hash_string(constants.USERTYPE_SYSTEMADMIN):
        return True
    else:
        return False

def hash_string(string):
    return hashlib.sha224(string.encode('utf-8')).hexdigest()