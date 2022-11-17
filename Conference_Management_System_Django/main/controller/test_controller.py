from django.shortcuts import render
from django.http import HttpResponse,Http404
from main.controller import controller_util
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
import random

email_lock = Lock()

#view funcs	
def index(request, message=None):
    islogged_in = controller_util.check_login(request)
    is_admin_logged_in = controller_util.check_type_login(request, models.User.UserType.USERTYPE_SYSTEMADMIN)

    user_type = request.COOKIES.get('user_type')
    if user_type:
        if user_type == controller_util.hash_string(str(models.User.UserType.USERTYPE_SYSTEMADMIN)):
            #0 = system admin
            template_name = "admin_homepage.html"
            
        elif user_type == controller_util.hash_string(str(models.User.UserType.USERTYPE_CONFERENCECHAIR)):
            #1 = conference chair
            template_name = "conferencechair_homepage.html"
            
        elif user_type == controller_util.hash_string(str(models.User.UserType.USERTYPE_REVIEWER)):
            #2 = reviewer
            template_name = "reviewer_homepage.html"
            
        elif user_type == controller_util.hash_string(str(models.User.UserType.USERTYPE_AUTHOR)):
            #3 = author
            template_name = "author_homepage.html"
    else:
        template_name = "index.html"

    context = {"islogged_in":islogged_in,"is_admin_logged_in":is_admin_logged_in,"user_type":request.COOKIES.get('user_type')}

    if message != None and not "message" in context:
        context["message"] = message

    #print("Using template: "+template_name)
    return render(request,template_name,context)
	
def emergency_manual_method(request):
    # call via "http://127.0.0.1:8000/emergency_manual_method?user_id="
    # if request.method == "GET":
    #     try:
    #         user_id = request.GET.get('user_id')
    #         user = models.User.objects.get(user_id=user_id)
    #         user.delete()
    #     except Exception as e:
    #         print(e)
    
    return index(request)

def test_template(request):
    # call via "http://127.0.0.1:8000/test_template"

    # template_name = "conferencechair_listsubmittedpapers.html"
    template_name = "conferencechair_listreviewers.html"

    return render(request,template_name,{"islogged_in":False, 'message':'Bad Authentication.', "is_admin_logged_in":False
                                                , "user_type":request.COOKIES.get('user_type')})

def create_users(request):
    print(os.getcwd())
    namelist_file_name = "../namelist.txt"
    if not os.path.exists(namelist_file_name):
        raise Exception("Password file does not exist.")
    fr = open(namelist_file_name, "r")
    string_names = fr.read().splitlines()
    fr.close()
    #return index(request)

    string_names = list(set(string_names))

    user_type_choices = range(models.User.UserType.USERTYPE_SYSTEMADMIN, models.User.UserType.USERTYPE_AUTHOR+1)
        
    for i in range(120):
        string_name = string_names[i]
    
        name = string_name.split(",")[0]

        user_type = random.choice(user_type_choices)
        email = name.lower()+"@gmail.com"
        password = "password".encode('utf-8')
        max_papers = random.randint(5,10)

        hashed_password = hashlib.sha224(password).hexdigest()
        try:
            user = models.User.objects.get(login_email=email)
            continue

        except models.User.DoesNotExist as e:
            print("creating "+str(user_type))
            if user_type == models.User.UserType.USERTYPE_SYSTEMADMIN:
                #0 = system admin
                models.SystemAdmin.objects.create(login_email=email, login_pw=hashed_password, name=name, user_type=models.User.UserType.USERTYPE_SYSTEMADMIN)
                
            elif user_type == models.User.UserType.USERTYPE_CONFERENCECHAIR:
                #1 = conference chair
                models.ConferenceChair.objects.create(login_email=email, login_pw=hashed_password, name=name, user_type=models.User.UserType.USERTYPE_CONFERENCECHAIR)
                
            elif user_type == models.User.UserType.USERTYPE_REVIEWER:
                #2 = reviewer
                models.Reviewer.objects.create(login_email=email, login_pw=hashed_password, name=name, max_papers=max_papers, user_type=models.User.UserType.USERTYPE_REVIEWER)
                
            elif user_type == models.User.UserType.USERTYPE_AUTHOR:
                #3 = author
                models.Author.objects.create(login_email=email, login_pw=hashed_password, name=name, user_type=models.User.UserType.USERTYPE_AUTHOR)

    return index(request, "")

def create_papers(request):
    paper_titles_start = ["Research into ", "Looking into ", "Queries about ", "Journal about ", "Facts regarding ", "Recipe for ", "Paper for "]
    paper_titles_end = "Bacon ipsum dolor amet short ribs brisket venison rump drumstick pig sausage prosciutto chicken spare ribs salami picanha doner Kevin capicola sausage buffalo bresaola venison turkey shoulder picanha ham pork tri-tip meatball meatloaf ribeye Doner spare ribs andouille bacon sausage Ground round jerky brisket pastrami shank".split(" ")
    paper_details = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Nullam vehicula ipsum a arcu cursus vitae congue mauris. Pretium quam vulputate dignissim suspendisse in. Sit amet tellus cras adipiscing enim eu. In fermentum et sollicitudin ac orci phasellus egestas. Gravida arcu ac tortor dignissim. Diam vel quam elementum pulvinar etiam non quam. Libero volutpat sed cras ornare arcu dui vivamus arcu felis. Massa sapien faucibus et molestie ac feugiat sed lectus vestibulum. Nec dui nunc mattis enim ut tellus elementum sagittis. Neque ornare aenean euismod elementum nisi quis.

Lorem ipsum dolor sit amet consectetur adipiscing. Urna et pharetra pharetra massa massa. Sem et tortor consequat id porta nibh venenatis cras. Faucibus a pellentesque sit amet. Pretium nibh ipsum consequat nisl. Purus ut faucibus pulvinar elementum integer enim. Turpis tincidunt id aliquet risus feugiat in. Sagittis aliquam malesuada bibendum arcu. Quis viverra nibh cras pulvinar mattis nunc sed. Consequat nisl vel pretium lectus quam id leo in vitae. Est placerat in egestas erat imperdiet sed. Velit scelerisque in dictum non consectetur a erat nam at. Adipiscing elit pellentesque habitant morbi tristique senectus et netus et. Eget magna fermentum iaculis eu non diam. Aliquet porttitor lacus luctus accumsan tortor posuere ac ut consequat. Eu feugiat pretium nibh ipsum consequat nisl vel pretium. Urna nunc id cursus metus aliquam eleifend mi.

Nec ultrices dui sapien eget mi. Quis eleifend quam adipiscing vitae proin. Libero enim sed faucibus turpis. Malesuada fames ac turpis egestas maecenas. Sit amet consectetur adipiscing elit. Amet cursus sit amet dictum. Diam vulputate ut pharetra sit amet aliquam id. Adipiscing vitae proin sagittis nisl rhoncus mattis. Quis commodo odio aenean sed adipiscing diam donec. Vel pretium lectus quam id. Cursus sit amet dictum sit amet justo donec.

Et leo duis ut diam quam nulla porttitor massa id. Odio ut enim blandit volutpat. Quam id leo in vitae turpis massa. Laoreet id donec ultrices tincidunt arcu non sodales neque sodales. Tincidunt arcu non sodales neque sodales. Montes nascetur ridiculus mus mauris. Sed faucibus turpis in eu mi bibendum neque egestas. Lacus suspendisse faucibus interdum posuere lorem ipsum dolor sit. Eget est lorem ipsum dolor sit amet consectetur adipiscing elit. Ut pharetra sit amet aliquam id diam. Eget est lorem ipsum dolor sit amet consectetur adipiscing. Volutpat sed cras ornare arcu dui vivamus arcu. Ut placerat orci nulla pellentesque dignissim enim sit amet. Ultrices sagittis orci a scelerisque purus semper eget duis. Amet massa vitae tortor condimentum lacinia quis. In metus vulputate eu scelerisque.

Risus feugiat in ante metus. Consequat mauris nunc congue nisi. Nisi est sit amet facilisis. Dui id ornare arcu odio ut sem. Id aliquet lectus proin nibh nisl condimentum id venenatis a. Elit scelerisque mauris pellentesque pulvinar. Nulla facilisi nullam vehicula ipsum a arcu. Tincidunt eget nullam non nisi est sit amet facilisis. Rhoncus mattis rhoncus urna neque viverra justo. Feugiat in fermentum posuere urna nec. Viverra nam libero justo laoreet sit. At elementum eu facilisis sed odio morbi. Fringilla est ullamcorper eget nulla facilisi. Aenean vel elit scelerisque mauris. Lobortis elementum nibh tellus molestie nunc. Aliquam nulla facilisi cras fermentum."""
        
    authors = models.Author.objects.all()
    paper_status_choices = range(models.Paper.PaperStatus.PAPERSTATUS_NOTSUBMITTED, models.Paper.PaperStatus.PAPERSTATUS_SUBMITTEDACCEPTED+1)

    for i in range(120):
        paper_title_start = random.choice(paper_titles_start)
        paper_title_end = random.choice(paper_titles_end)
        paper_title = paper_title_start + paper_title_end.capitalize()
        author_num = random.randint(1,5)
        paper_status = random.choice(paper_status_choices)
        paper_status = models.Paper.PaperStatus.PAPERSTATUS_NOTSUBMITTED if paper_status == models.Paper.PaperStatus.PAPERSTATUS_NOTSUBMITTED else models.Paper.PaperStatus.PAPERSTATUS_SUBMITTEDPENDING

        author_list = list()

        for j in range(author_num):
            author = random.choice(authors)
            if not author in author_list:
                author_list.append(author)


        author_list = list(set(author_list))

        paper = models.Paper.objects.create(paper_name=paper_title, paper_details=paper_details, status=paper_status)

        for author in author_list:
            models.Writes.objects.create(author_user_id=author, paper_id=paper)

    return index(request, "")

def create_papers(request):
    paper_titles_start = ["Research into ", "Looking into ", "Queries about ", "Journal about ", "Facts regarding ", "Recipe for ", "Paper for "]
    paper_titles_end = "Bacon ipsum dolor amet short ribs brisket venison rump drumstick pig sausage prosciutto chicken spare ribs salami picanha doner Kevin capicola sausage buffalo bresaola venison turkey shoulder picanha ham pork tri-tip meatball meatloaf ribeye Doner spare ribs andouille bacon sausage Ground round jerky brisket pastrami shank".split(" ")
    paper_details = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Nullam vehicula ipsum a arcu cursus vitae congue mauris. Pretium quam vulputate dignissim suspendisse in. Sit amet tellus cras adipiscing enim eu. In fermentum et sollicitudin ac orci phasellus egestas. Gravida arcu ac tortor dignissim. Diam vel quam elementum pulvinar etiam non quam. Libero volutpat sed cras ornare arcu dui vivamus arcu felis. Massa sapien faucibus et molestie ac feugiat sed lectus vestibulum. Nec dui nunc mattis enim ut tellus elementum sagittis. Neque ornare aenean euismod elementum nisi quis.

Lorem ipsum dolor sit amet consectetur adipiscing. Urna et pharetra pharetra massa massa. Sem et tortor consequat id porta nibh venenatis cras. Faucibus a pellentesque sit amet. Pretium nibh ipsum consequat nisl. Purus ut faucibus pulvinar elementum integer enim. Turpis tincidunt id aliquet risus feugiat in. Sagittis aliquam malesuada bibendum arcu. Quis viverra nibh cras pulvinar mattis nunc sed. Consequat nisl vel pretium lectus quam id leo in vitae. Est placerat in egestas erat imperdiet sed. Velit scelerisque in dictum non consectetur a erat nam at. Adipiscing elit pellentesque habitant morbi tristique senectus et netus et. Eget magna fermentum iaculis eu non diam. Aliquet porttitor lacus luctus accumsan tortor posuere ac ut consequat. Eu feugiat pretium nibh ipsum consequat nisl vel pretium. Urna nunc id cursus metus aliquam eleifend mi.

Nec ultrices dui sapien eget mi. Quis eleifend quam adipiscing vitae proin. Libero enim sed faucibus turpis. Malesuada fames ac turpis egestas maecenas. Sit amet consectetur adipiscing elit. Amet cursus sit amet dictum. Diam vulputate ut pharetra sit amet aliquam id. Adipiscing vitae proin sagittis nisl rhoncus mattis. Quis commodo odio aenean sed adipiscing diam donec. Vel pretium lectus quam id. Cursus sit amet dictum sit amet justo donec.

Et leo duis ut diam quam nulla porttitor massa id. Odio ut enim blandit volutpat. Quam id leo in vitae turpis massa. Laoreet id donec ultrices tincidunt arcu non sodales neque sodales. Tincidunt arcu non sodales neque sodales. Montes nascetur ridiculus mus mauris. Sed faucibus turpis in eu mi bibendum neque egestas. Lacus suspendisse faucibus interdum posuere lorem ipsum dolor sit. Eget est lorem ipsum dolor sit amet consectetur adipiscing elit. Ut pharetra sit amet aliquam id diam. Eget est lorem ipsum dolor sit amet consectetur adipiscing. Volutpat sed cras ornare arcu dui vivamus arcu. Ut placerat orci nulla pellentesque dignissim enim sit amet. Ultrices sagittis orci a scelerisque purus semper eget duis. Amet massa vitae tortor condimentum lacinia quis. In metus vulputate eu scelerisque.

Risus feugiat in ante metus. Consequat mauris nunc congue nisi. Nisi est sit amet facilisis. Dui id ornare arcu odio ut sem. Id aliquet lectus proin nibh nisl condimentum id venenatis a. Elit scelerisque mauris pellentesque pulvinar. Nulla facilisi nullam vehicula ipsum a arcu. Tincidunt eget nullam non nisi est sit amet facilisis. Rhoncus mattis rhoncus urna neque viverra justo. Feugiat in fermentum posuere urna nec. Viverra nam libero justo laoreet sit. At elementum eu facilisis sed odio morbi. Fringilla est ullamcorper eget nulla facilisi. Aenean vel elit scelerisque mauris. Lobortis elementum nibh tellus molestie nunc. Aliquam nulla facilisi cras fermentum."""
        
    authors = models.Author.objects.all()
    paper_status_choices = range(models.Paper.PaperStatus.PAPERSTATUS_NOTSUBMITTED, models.Paper.PaperStatus.PAPERSTATUS_SUBMITTEDACCEPTED+1)

    for i in range(120):
        paper_title_start = random.choice(paper_titles_start)
        paper_title_end = random.choice(paper_titles_end)
        paper_title = paper_title_start + paper_title_end.capitalize()
        author_num = random.randint(1,5)
        paper_status = random.choice(paper_status_choices)
        paper_status = models.Paper.PaperStatus.PAPERSTATUS_NOTSUBMITTED if paper_status == models.Paper.PaperStatus.PAPERSTATUS_NOTSUBMITTED else models.Paper.PaperStatus.PAPERSTATUS_SUBMITTEDPENDING

        author_list = list()

        for j in range(author_num):
            author = random.choice(authors)
            if not author in author_list:
                author_list.append(author)


        author_list = list(set(author_list))

        paper = models.Paper.objects.create(paper_name=paper_title, paper_details=paper_details, status=paper_status)

        for author in author_list:
            models.Writes.objects.create(author_user_id=author, paper_id=paper)

    return index(request, "")

def create_bids(request):
    reviewers = models.Reviewer.objects.all()
    biddable_papers = models.Paper.objects.filter(status=models.Paper.PaperStatus.PAPERSTATUS_SUBMITTEDPENDING)

    for i in range(120):
        reviewer = random.choice(reviewers)
        paper = random.choice(biddable_papers)
        
        bidExists, bid = models.Bids.does_bid_exist(reviewer.user_id, paper.paper_id)
        if not bidExists:
            bid = models.Bids.objects.create(reviewer_user_id=reviewer, paper_id=paper)

    return index(request, "")

def create_reviews(request):
    unrated_papers = models.Paper.objects.filter(status=models.Paper.PaperStatus.PAPERSTATUS_SUBMITTEDPENDING)
    reviewers = models.Reviewer.objects.all()
    review_details = """Cupcake ipsum dolor sit amet icing pie soufflé. Cheesecake ice cream gingerbread jelly beans sesame snaps marzipan macaroon toffee croissant. Toffee macaroon dragée jujubes powder sesame snaps gummi bears.

Danish marshmallow candy canes macaroon sweet biscuit chupa chups danish. Brownie cotton candy jelly cookie croissant sugar plum. Sweet roll fruitcake halvah pastry brownie shortbread tootsie roll cheesecake.

Tiramisu sweet roll fruitcake candy canes tootsie roll gummies gummi bears cookie. Sweet roll pastry sesame snaps cupcake macaroon muffin fruitcake bonbon lemon drops. Candy canes chocolate cake tiramisu jujubes cake macaroon cotton candy jelly. Cake chupa chups icing jujubes marzipan.

Biscuit cheesecake sesame snaps macaroon halvah powder jelly-o topping. Jelly-o cupcake pie donut cake soufflé ice cream cupcake ice cream. Tootsie roll dragée ice cream sweet roll cookie oat cake jelly beans.

Carrot cake ice cream halvah cotton candy cake oat cake dragée fruitcake. Pudding pie ice cream gummies powder cupcake. Cake pie chocolate cake cake cheesecake. Danish icing liquorice icing dragée croissant oat cake liquorice dragée."""
    
    rating_choices = list()
    for key, value in models.Reviews.Rating.choices:
        rating_choices.append(key)

    for i in range(120):
        paper = random.choice(unrated_papers)
        reviewer = random.choice(reviewers)
        author_rating = random.choice(rating_choices)
        reviewer_rating = random.choice(rating_choices)

        if not reviewer.can_be_allocated_another_paper():
            continue
        
        if reviewer.is_reviewer_of_paper(paper.paper_id):
            continue

        models.Reviews.objects.create(reviewer_user_id=reviewer, paper_id=paper, review_details=review_details, author_rating=author_rating, reviewer_rating=reviewer_rating)


    return index(request, "")
    
def acceptrejectpaper(request):
    unrated_papers = models.Paper.objects.filter(status=models.Paper.PaperStatus.PAPERSTATUS_SUBMITTEDREJECTED)

    for paper in unrated_papers:
        fully_reviewed = paper.is_paper_fully_reviewed()

        if fully_reviewed:
            rated_reviews = models.Reviews.objects.filter(paper_id=paper).exclude(reviewer_rating=models.Reviews.Rating.UNRATED)

            total_rating = 0
            for review in rated_reviews:
                total_rating += review.reviewer_rating

            avg = total_rating / len(rated_reviews)

            new_status = models.Paper.PaperStatus.PAPERSTATUS_SUBMITTEDACCEPTED if avg > 0 else models.Paper.PaperStatus.PAPERSTATUS_SUBMITTEDREJECTED
            paper.status = new_status
            paper.save()

    return index(request, "")

def create_comments(request):
    acceptreject_papers = models.Paper.objects.exclude(status=models.Paper.PaperStatus.PAPERSTATUS_NOTSUBMITTED).exclude(status=models.Paper.PaperStatus.PAPERSTATUS_SUBMITTEDPENDING)
    reviewers = models.Reviewer.objects.all()

    comment_text="""The most significant things we can think about, when we think about Apollo, is that it has opened for us, for us being the World, a challenge of the future. The door is now cracked, but the promise of that future lies in the young people, not just in America, but the young people all over the world. Learning to live and learning to work together. In order to remind all the peoples of the World, in so many countries throughout the world, that this is what we all are striving for in the future, Jack has picked up a very significant rock, typical of what we have here in the valley of Taurus Littrow. It's a rock composed of many fragments, of many sizes, and many shapes, probably from all parts of the Moon, perhaps billions of years old. But a rock of all sizes and shapes, fragments of all sizes and shapes, and even colors that have grown together to become a cohesive rock outlasting the nature of Space, sort of living together in a very coherent, very peaceful manner. When we return this rock or some of the others like it to Houston, we'd like to share a piece of this rock with so many of the countries throughout the world. We hope that this will be a symbol of what our feelings are, what the feelings of the Apollo Program are, and a symbol of mankind that we can live in peace and harmony in the future."""

    fully_reviewed_reviews = list()
    for paper in acceptreject_papers:
        fully_reviewed = paper.is_paper_reviews_author_rated()

        if fully_reviewed:
            fully_reviewed_reviews += models.Reviews.objects.filter(paper_id=paper)

    for i in range(360):
        review = random.choice(fully_reviewed_reviews)
        reviewer = random.choice(reviewers)
        
        models.ReviewComments.objects.create(review_id=review, commenter_user_id=reviewer, comment_text=comment_text)
        
    return index(request, "")