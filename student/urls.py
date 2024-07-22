from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('studentclick', views.studentclick_view, name='studentclick'),
    path('studentlogin', LoginView.as_view(template_name='student/studentlogin.html'), name='studentlogin'),
    path('studentlogout', LogoutView.as_view(next_page='studentlogin'), name='studentlogout'),
    path('studentsignup', views.student_signup_view, name='studentsignup'),
    path('student-dashboard', views.student_dashboard_view, name='student-dashboard'),
    path('student-exam', views.student_exam_view, name='student-exam'),
    path('student-courses', views.student_courses_view, name='student-courses'),
    path('student-results', views.student_results_view, name='student-results'),
    path('student-questions', views.student_questions_view, name='student-questions'),
    path('take-exam/<int:pk>', views.take_exam_view, name='take-exam'),
    path('course/<int:course_id>/question/<int:question_num>/', views.display_question_view, name='display_question'),
    path('calculate-marks', views.calculate_marks_view, name='calculate-marks'),
    path('check-marks/<int:pk>', views.check_marks_view, name='check-marks'),
    path('student-marks', views.student_marks_view, name='student-marks'),
    path('view-result/<int:course_id>/', views.view_result_view, name='view-result')
]
