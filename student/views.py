from django.shortcuts import render, redirect, reverse, get_object_or_404
from . import forms
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required, user_passes_test
from quiz import models as QMODEL
from student.models import Student
from quiz.models import Course, Question, Result
from django.db import IntegrityError 
from django.utils import timezone
from django.core import serializers
import json
from django.db.models import Avg

def studentclick_view(request):
    if request.user.is_authenticated:
        return redirect('afterlogin')
    return render(request, 'student/studentclick.html')

def student_signup_view(request):
    userForm = forms.StudentUserForm()
    studentForm = forms.StudentForm()
    mydict = {'userForm': userForm, 'studentForm': studentForm}
    if request.method == 'POST':
        userForm = forms.StudentUserForm(request.POST)
        studentForm = forms.StudentForm(request.POST, request.FILES)
        if userForm.is_valid() and studentForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            student = studentForm.save(commit=False)
            student.user = user
            student.save()
            my_student_group = Group.objects.get_or_create(name='STUDENT')
            my_student_group[0].user_set.add(user)
        return redirect('studentlogin')
    return render(request, 'student/studentsignup.html', context=mydict)

def is_student(user):
    return user.groups.filter(name='STUDENT').exists()

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_dashboard_view(request):
    student = request.user.student  # This assumes you have set up the OneToOneField correctly
    available_exams = Course.objects.all()  # Or filter as needed
    recent_attempts = Result.objects.filter(student=student).order_by('-date')[:5]  # Get last 5 attempts

    available_exams_count = available_exams.count()
    total_attempts = Result.objects.filter(student=student).count()
    average_score = Result.objects.filter(student=student).aggregate(Avg('marks'))['marks__avg']
    if average_score is not None:
        average_score = round(average_score, 2)
    else:
        average_score = 0

    context = {
        'student': student,
        'available_exams': available_exams,
        'recent_attempts': recent_attempts,
        'available_exams_count': available_exams_count,
        'total_attempts': total_attempts,
        'average_score': average_score,
    }
    return render(request, 'student/student_dashboard.html', context)

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_exam_view(request):
    courses = QMODEL.Course.objects.all()
    return render(request, 'student/student_exam.html', {'courses': courses})

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_courses_view(request):
    courses = Course.objects.all()
    courses_json = serializers.serialize('json', courses)
    return render(request, 'student/student_courses.html', {
        'courses': courses,
        'courses_json': json.dumps(courses_json)
    })

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def take_exam_view(request, pk):
    course = QMODEL.Course.objects.get(id=pk)
    total_questions = QMODEL.Question.objects.all().filter(course=course).count()
    questions = QMODEL.Question.objects.all().filter(course=course)
    total_marks = sum(q.marks for q in questions)
    return render(request, 'student/take_exam.html', {
        'course': course,
        'total_questions': total_questions,
        'total_marks': total_marks,
    })


@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def display_question_view(request, course_id, question_num):
    course = get_object_or_404(Course, id=course_id)
    questions = list(Question.objects.filter(course=course).order_by('id'))
    total_questions = len(questions)

    if question_num < 1 or question_num > total_questions:
        return redirect('display_question', course_id=course_id, question_num=1)

    question = questions[question_num - 1]

    if request.method == 'POST':
        selected_answer = request.POST.get('answer')
        hint1_used = request.POST.get('hint1_used') == 'true'
        hint2_used = request.POST.get('hint2_used') == 'true'

        response = redirect('display_question', course_id=course_id, question_num=question_num + 1)
        
        if question_num >= total_questions:
            response = redirect('calculate-marks')

        # Set cookies
        response.set_cookie(f'question_{question_num}_answer', selected_answer)
        response.set_cookie('course_id', course_id)
        if hint1_used:
            response.set_cookie(f'hint1_used_{question_num}', 'true')
        if hint2_used:
            response.set_cookie(f'hint2_used_{question_num}', 'true')

        return response

    context = {
        'course': course,
        'question': question,
        'question_num': question_num,
        'total_questions': total_questions
    }
    return render(request, 'student/display_question.html', context)


@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def calculate_marks_view(request):
    course_id = request.COOKIES.get('course_id')
    if not course_id:
        return redirect('student-dashboard')

    course = get_object_or_404(Course, id=course_id)
    questions = Question.objects.filter(course=course)
    total_marks = 0

    for i, question in enumerate(questions, start=1):
        selected_ans = request.COOKIES.get(f'question_{i}_answer')
        question_marks = question.marks

        # Check if hints were used for this question
        hint1_used = request.COOKIES.get(f'hint1_used_{i}') == 'true'
        hint2_used = request.COOKIES.get(f'hint2_used_{i}') == 'true'

        # Reduce marks for hints used
        if hint1_used:
            question_marks = max(0, question_marks - 1)
        if hint2_used:
            question_marks = max(0, question_marks - 1)

        # Award marks if the answer is correct
        if selected_ans == question.answer:
            total_marks += question_marks

    student = get_object_or_404(Student, user=request.user)

    try:
        result = Result.objects.create(
            student=student,
            exam=course,
            marks=total_marks,
            date=timezone.now()
        )
    except IntegrityError:
        # Log the error and redirect
        print(f"IntegrityError: Unable to save result for student {student.id} in course {course.id}")
        return redirect('student-dashboard')

    response = redirect('view-result', course_id=course_id)
    
    # Clear cookies
    for key in request.COOKIES:
        if key.startswith('question_') or key.startswith('hint') or key == 'course_id':
            response.delete_cookie(key)

    return response

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def view_result_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    student = get_object_or_404(Student, user=request.user)
    results = Result.objects.filter(student=student, exam=course).order_by('-date')
    
    context = {
        'course': course,
        'results': results
    }
    return render(request, 'student/view_result.html', context)

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def check_marks_view(request, pk):
    course = QMODEL.Course.objects.get(id=pk)
    student = Student.objects.get(user_id=request.user.id)
    results = QMODEL.Result.objects.all().filter(exam=course).filter(student=student)
    return render(request, 'student/check_marks.html', {'results': results})

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_marks_view(request):
    courses = QMODEL.Course.objects.all()
    return render(request, 'student/student_marks.html', {'courses': courses})

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_results_view(request):
    results = Result.objects.filter(student__user=request.user)
    return render(request, 'student/student_results.html', {'results': results})

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_questions_view(request):
    student = request.user.student
    courses = Course.objects.filter(students=student)
    questions = Question.objects.filter(course__in=courses)
    return render(request, 'student/student_questions.html', {'questions': questions})
