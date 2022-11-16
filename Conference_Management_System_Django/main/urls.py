from django.urls import path

from .controller import loginout_controller, sysadmin_controller, author_controller, reviewer_controller, conferencechair_controller, commentor_controller
from . import views
#from .controller import *
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('', loginout_controller.index, name='index'),
    path('login', loginout_controller.login, name='login'),
    path('login_ValidateInfo', loginout_controller.login_ValidateInfo, name='login_ValidateInfo'),
    path('logout',loginout_controller.logout_handle,name='logout_handle'),

    path('admin_create_user', sysadmin_controller.admin_create_user, name='register'),
    path('admin_AddUserProfile', sysadmin_controller.admin_AddUserProfile, name='register_handle'),
    path('view_all_users', sysadmin_controller.admin_ViewAllUsers, name='view_all_users'),
    path('search_users', sysadmin_controller.admin_SearchUsers, name='search_users'),
    path('view_user', sysadmin_controller.admin_ViewUser, name='view_user'),
    path('update_user', sysadmin_controller.admin_UpdateUser, name='update_user'),
    path('suspend_user', sysadmin_controller.admin_SuspendUser, name='suspend_user'),

    path('author_start_new_paper', author_controller.author_start_new_paper, name='new_paper'),
    path('author_StartNewPaper', author_controller.author_StartNewPaper, name='new_paper_handle'),
    path('author_list_papers', author_controller.author_list_papers, name='list_papers'),
    path('author_view_paper', author_controller.author_view_paper, name='view_paper'),
    path('author_SavePaper', author_controller.author_SavePaper, name='save_paper'),
    path('author_SubmitPaper', author_controller.author_SubmitPaper, name='submit_paper'),
    path('author_view_all_reviews', author_controller.author_view_all_reviews, name='author_view_all_reviews'),
    path('author_view_review', author_controller.author_view_review, name='author_view_review'),
    path('author_GiveRating', author_controller.author_GiveRating, name='author_GiveRating'),
    
    path('reviewer_list_biddable_papers', reviewer_controller.reviewer_list_biddable_papers, name='reviewer_list_biddable_papers'),
    path('reviewer_BidPaper', reviewer_controller.reviewer_BidPaper, name='reviewer_BidPaper'),
    path('reviewer_list_reviewed_papers', reviewer_controller.reviewer_list_unreviewed_papers, name='reviewer_list_reviewed_papers'),
    path('reviewer_view_paper', reviewer_controller.reviewer_view_paper, name='reviewer_view_paper'),
    path('reviewer_give_review', reviewer_controller.reviewer_give_review, name='reviewer_give_review'),
    path('reviewer_SaveReview', reviewer_controller.reviewer_SaveReview, name='reviewer_SaveReview'),
    path('reviewer_GiveRating', reviewer_controller.reviewer_GiveRating, name='reviewer_GiveRating'),
    
    path('conferencechair_view_submitted_papers', conferencechair_controller.conferencechair_view_submitted_papers, name='conferencechair_view_submitted_papers'),
    path('conferencechair_view_reviewers', conferencechair_controller.conferencechair_view_reviewers, name='conferencechair_view_reviewers'),
    path('conferencechair_AllocatePaper', conferencechair_controller.conferencechair_AllocatePaper, name='conferencechair_AllocatePaper'),
    path('conferencechair_view_reviewed_papers', conferencechair_controller.conferencechair_view_reviewed_papers, name='conferencechair_view_reviewed_papers'),
    path('conferencechair_view_reviewer_ratings', conferencechair_controller.conferencechair_view_reviewer_ratings, name='conferencechair_view_reviewer_ratings'),
    path('conferencechair_AcceptPaper', conferencechair_controller.conferencechair_AcceptPaper, name='conferencechair_AcceptPaper'),
    path('conferencechair_RejectPaper', conferencechair_controller.conferencechair_RejectPaper, name='conferencechair_RejectPaper'),
    
    path('commentor_view_fully_reviewed_papers', commentor_controller.commentor_view_fully_reviewed_papers, name='commentor_view_fully_reviewed_papers'),
    path('commentor_view_reviews', commentor_controller.commentor_view_reviews, name='commentor_view_reviews'),
    path('commentor_view_review_comments', commentor_controller.commentor_view_review_comments, name='commentor_view_review_comments'),
    path('commentor_add_comment', commentor_controller.commentor_add_comment, name='commentor_add_comment'),
    path('commentor_AddComment', commentor_controller.commentor_AddComment, name='commentor_AddComment'),

    path('test_template', loginout_controller.test_template, name='test_template'),
    path('emergency_manual_method', loginout_controller.emergency_manual_method, name='emergency_manual_method'),

    path('conferences',views.conferences, name="conferences"),
    path('add_conference_handle',views.add_conference_handle, name="add_conference_handle"),
    path('conference',views.conference,name='conference'),
    path('add_paper_handle',views.add_paper_handle,name='add_paper_handle'),
    path('accept_reject_chair_reviewer_handle',views.accept_reject_chair_reviewer_handle,name='accept_reject_chair_reviewer_handle'),
    path('chair_reviewer_application',views.chair_reviewer_application,name='chair_reviewer_application'),
    path('author_papers',views.author_papers,name="author_papers"),
    path('submit_paper',views.submit_paper,name='submit_paper'),
    path('assign_paper',views.assign_paper,name="assign_paper"),
    path('assign_paper_handle',views.assign_paper_handle,name="assign_paper_handle"),
    path('reviewer_assignments',views.reviewer_assignments,name='reviewer_assignments'),
    path('download_file',views.download_file,name="download_file"),
    path('add_review',views.add_review,name="add_review"),
    path('add_review_handle',views.add_review_handle,name="add_review_handle"),
    path('edit_review',views.edit_review,name='edit_review'),
    path('edit_review_handle',views.edit_review_handle,name='edit_review_handle'),
    path('paper_reviews',views.paper_reviews,name='paper_reviews'),
    path('paper_review',views.paper_review,name="paper_review"),
    path('accept_reject_paper',views.accept_reject_paper,name='accept_reject_paper'),
    path('paper',views.paper,name="paper"),
    path('update_paper_files',views.update_paper_files,name='update_paper_files'),
    path('schedule_conference',views.schedule_conference,name='schedule_conference'),
    path('schedule_paper_handle',views.schedule_paper_handle,name='schedule_paper_handle'),
    path('unschedule_paper_handle',views.unschedule_paper_handle,name='unschedule_paper_handle')
]