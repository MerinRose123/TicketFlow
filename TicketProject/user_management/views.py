from __future__ import absolute_import, unicode_literals
from django.shortcuts import render, redirect
from django.contrib.auth.models import Group
from django.contrib.auth import (
    authenticate,
    login,
    logout,
)
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from .forms import LoginForm, RegisterForm, TicketAddForm
from django.contrib.auth.decorators import login_required
from .models import Ticket, User
from .tasks import change_state
from django.contrib.auth.decorators import user_passes_test


# Adding user to group according to designation
def add_user_to_group(user, designation):
    # Adding the user to a group according to the designation option
    if designation == 'super_admin':
        group = Group.objects.get(name='super_admin')
    elif designation == 'senior_system_admin':
        group = Group.objects.get(name='senior_system_admin')
    else:
        group = Group.objects.get(name='system_admin')
    user.groups.add(group)


def is_super_admin(user):
    """
    Checks whether the user is a super admin
    :param user:The request user who is logged in
    :return: True if the user is a member of super admin group
    """
    return user.groups.filter(name='super_admin').exists()


def is_system_admin(user):
    """
    Checks whether the user is a system admin
    :param user:The request user who is logged in
    :return: True if the user is a member of system admin group
    """
    return user.groups.filter(name='system_admin').exists()


def is_senior_system_admin(user):
    return user.groups.filter(name='senior_system_admin').exists()


# Registering a new user
def register(request):
    if request.method == 'POST':  # processing the data after the data is posted
        form = RegisterForm(request.POST)
        username = form.data['username']
        email = form.data['email']
        password = form.data["password"]
        designation = form.data["designation"]
        if password == form.data["password1"]:  # checking if the the two passwords are same.
            # Checking if the username or password already exists in the database
            if User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists():
                messages.error(request, 'Username or email already taken.')
                response = redirect('../register/')
            else:  # Creating a new user with given details
                q = User(first_name=form.data['first_name'], last_name=form.data['last_name'],
                         username=username, email=email, phone=form.data["phone"], password=make_password(password))
                q.save()
                add_user_to_group(q, designation)
                messages.success(request, 'user registered successfully.')
                response = redirect('login_view')
        else:
            messages.error(request, 'The passwords are not matching.')
            response = redirect('../register/')
        return response
    else:  # Rendering the form in html initially with get request
        form = RegisterForm()
        return render(request, 'register.html', {'form': form})


# To login a current user
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        username = form.data['username']
        password = form.data["password"]
        # Authenticating the user by checking in the database
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, username + ' you are now logged in..!!!.')
            response = redirect('../home/')
            return response
        else:
            messages.error(request, 'username or password are not correct.')
            return render(request, 'login.html', {'form': form})
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


# To logout an already logged in user
@login_required
def logoutview(request):
    logout(request)
    response = redirect('../login/')
    return response


# deleting a user
@login_required
@user_passes_test(is_super_admin)
def deleteuser(request):
    if request.method == 'POST':
        id = request.POST.get('id')
        User.objects.get(id=id).delete()
        messages.success(request, 'User deleted successfully.')
        return redirect('../listuser/')
    else:
        response = redirect('../home/')
        return response


# Viewing the details of all the users in the home page
@login_required
@user_passes_test(is_super_admin)
def listuser(request):
    data = User.objects.all()
    return render(request, 'userlistview.html', {'userlogin': data})


@login_required
@user_passes_test(is_super_admin)
def edituser(request):
    """
    Editing the details of a current user
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        id = request.POST.get('id')
        designation = request.POST.get('designation')
        user = User.objects.get(id=id)
        user.username = username
        user.email = email
        user.save()
        user.groups.clear()
        add_user_to_group(user, designation)
        response = redirect('../listuser')
    else:
        response = redirect('../home/')
    return response


def base(request):
    """
    Rendering the base page which is to be displayed when initially the site is loaded
    """
    return render(request, 'base1.html')


@login_required
def home(request):
    """
      Rendering home page
    """
    celeryview(request)  # to change the date if current date is greater than end date.
    return render(request, 'home.html')


@login_required
@user_passes_test(is_senior_system_admin)
def addticket(request):
    """
     Adding a new ticket to database
    """
    if request.method == 'POST':
        form = TicketAddForm(request.POST)
        #assigned_to_id = form.data['assigned_to']
        start_date = form.data['start_date']
        end_date = form.data['end_date']
        subject = form.data['subject']
        message = form.data['message']
        state = "CRT"
        priority = form.data['priority']
        #assigned_to = User.objects.get(id=assigned_to_id)
        q = Ticket(start_date=start_date, end_date=end_date,
                   subject=subject, message=message, state=state, priority=priority)
        q.save()
        print('Ticket added')
        response = redirect('../home/')
        return response
    else:
        # Rendering the form in html initially
        form = TicketAddForm()
    return render(request, 'addticket.html', {'form': form})


@login_required
@user_passes_test(is_super_admin)
def deleteticket(request):
    """
    Deleting an existing ticket
    """
    if request.method == 'POST':
        ticket_id = request.POST.get("ticket_id")
        if Ticket.objects.filter(ticket_id=ticket_id).exists():
            instance = Ticket.objects.get(ticket_id=ticket_id)
            instance.delete()
            messages.success(request, 'Ticket deleted successfully.')
    else:
        messages.error(request, 'No ticket with the given Ticket id.')
    response = redirect('../listticket/')
    return response


# Viewing the details of all tickets
@login_required
def listticket(request):
    data = Ticket.objects.all()
    return render(request, 'ticketlistview.html', {'ticketlist': data})


@login_required
def viewticket(request):
    """
    Viewing all tickets to super_admin and senior_sysem_admin.
    """
    user = request.user
    data = Ticket.objects.filter(assigned_to=user)
    return render(request, 'viewticket.html', {'ticketlist': data})


@login_required
@user_passes_test(is_system_admin)
def edit_state_ticket_to_progress(request):
    """
    When system admin clicks begin changing state of ticket to progress
    """
    if request.method == 'POST':
        ticket_id = request.POST.get('ticket_id')
        ticket = Ticket.objects.get(ticket_id=ticket_id)
        if ticket.state != "DNE":
            ticket.state = "PRG"
            ticket.save()
        else:
            messages.error(request, 'Ticket is in done state.So you can not begin this ticket')
        response = redirect('../view_ticket_system_admin')
    else:
        response = redirect('../home/')
    return response


@login_required
@user_passes_test(is_system_admin)
def edit_state_ticket_to_done(request):
    """
    When the respective system_admin clicks end moving ticket to done state
    """

    if request.method == 'POST':
        ticket_id = request.POST.get('ticket_id')
        ticket = Ticket.objects.get(ticket_id=ticket_id)
        if ticket.state == "PRG":
            ticket.state = "DNE"
            ticket.save()
        else:
            messages.error(request, 'Ticket is in create state.So have to begin before ending the ticket.')
        response = redirect('../view_ticket_system_admin')
    else:
        response = redirect('../home/')
    return response


@login_required
@user_passes_test(is_senior_system_admin)
def editticket(request):
    """
    Editing a ticket
    """
    if request.method == 'POST':
        assigned_to = request.POST.get('assigned_to')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        ticket_id = request.POST.get('ticket_id')
        subject = request.POST.get('subject')
        state = request.POST.get('state')
        ticket = Ticket.objects.get(ticket_id=ticket_id)
        user = User.objects.get(username=assigned_to)
        ticket.assigned_to = user
        if start_date < end_date:
            ticket.start_date = start_date
            ticket.end_date = end_date
        ticket.subject = subject
        ticket.state = state
        ticket.save()
        response = redirect('../listticket')
    else:
        response = redirect('../home/')
    return response


@login_required
@user_passes_test(is_super_admin)
def addticketadmin(request):
    """
     Adding a new ticket to database by super admin. Cannot add assigned to field
    """
    if request.method == 'POST':
        form = TicketAddForm(request.POST)
        # assigned_to_id = form.data['assigned_to']
        start_date = form.data['start_date']
        end_date = form.data['end_date']
        subject = form.data['subject']
        message = form.data['message']
        state = "CRT"
        priority = form.data['priority']
        # assigned_to = User.objects.get(id=assigned_to_id)
        q = Ticket(start_date=start_date, end_date=end_date,
                   subject=subject, message=message, state=state, priority=priority)
        q.save()
        print('Ticket added')
        response = redirect('../home/')
        return response
    else:
        # Rendering the form in html initially
        form = TicketAddForm()
    return render(request, 'addticket.html', {'form': form})


@login_required
@user_passes_test(is_super_admin)
def editticketadmin(request):
    """
    Editing a ticket by super admin. Can not edit assigned to field
    """
    if request.method == 'POST':
        # assigned_to = request.POST.get('assigned_to')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        ticket_id = request.POST.get('ticket_id')
        subject = request.POST.get('subject')
        state = request.POST.get('state')
        ticket = Ticket.objects.get(ticket_id=ticket_id)
        # user = User.objects.get(username=assigned_to)
        # ticket.assigned_to = user
        if start_date < end_date:
            ticket.start_date = start_date
            ticket.end_date = end_date
        ticket.subject = subject
        ticket.state = state
        ticket.save()
        response = redirect('../listticket')
    else:
        response = redirect('../home/')
    return response


def celeryview(request):
    """Queue due-date maintenance without delaying the dashboard response."""
    return change_state.apply_async((), retry=False)


