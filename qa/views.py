from django.contrib.auth.models import Group, User
from django.db import transaction
from django.shortcuts import render, render_to_response, get_object_or_404
from django.template.context import RequestContext
from qa.models import Question, Answer, QuestionUpvote
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest

def home(request):
    return render(request, "home.html")

def candidates(request):
    g = Group.objects.get(name="candidates")
    candidates = g.user_set.all()
    return render_to_response("candidates.html", locals(), context_instance=RequestContext(request))

def view_candidate(request, candidate_id):
    candidate = get_object_or_404(User, id=candidate_id)
    answers = candidate.answers.all()
    return render_to_response("view_candidate.html", locals(), context_instance=RequestContext(request))

def voters(request):
    g = Group.objects.get(name="voters")
    voters = g.user_set.all()
    return render_to_response("voters.html", locals(), context_instance=RequestContext(request))

def view_voter(request, voter_id):
    voter = get_object_or_404(User, id=voter_id)
    return render_to_response("view_voter.html", locals(), context_instance=RequestContext(request))

def questions(request):
    questions = Question.objects.all()
    return render_to_response("questions.html", locals(), context_instance=RequestContext(request))

def view_question(request, q_id):
    question = get_object_or_404(Question, id=q_id)
    answers = question.answers.all()
    return render_to_response("view_question.html", locals(), context_instance=RequestContext(request))

def add_question(request):
    if not request.user.is_authenticated():
        return HttpResponseForbidden(_("You cannot post questions"))

    subject = request.POST.get("subject")
    content = request.POST.get("content")

    q = Question(author=request.user, subject=subject, content=content)
    q.save()

    return HttpResponse("OK")

def add_answer(request, q_id):
    if not request.user.is_authenticated(): # TODO: check that user is a candidate (can answer questions)
        return HttpResponseForbidden(_("You must be a candidate to add an answer"))

    question = Question.objects.get(id=q_id)
    content = request.POST.get("content")

    if not (question and content):
        return HttpResponseBadRequest(_("Question does not exist, or empty answer"))

    answer = Answer(author=request.user, content=content, question=question)
    answer.save()

    return HttpResponse(_("Your answer was recorded"))

def upvote_question(request, q_id):
    q = get_object_or_404(Question, id=q_id)
    user = request.user

    if q.author == user:
        return HttpResponseForbidden(_("You cannot upvote your own question"))
    voted_questions = [vote.question for vote in user.upvotes.all()]
    if q in voted_questions:
        return HttpResponseForbidden(_("You already upvoted this question"))
    else:
        upvote = QuestionUpvote(question=q, user=user)
        upvote.save()
        increase_rating(q)
    return HttpResponse(_("Your vote was recorded"))

@transaction.commit_on_success
def increase_rating(q):
    q = Question.objects.get(id=q.id)
    q.rating += 1
    q.save()
