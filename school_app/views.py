from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.core.files.storage import FileSystemStorage
from django.http import FileResponse
import os

from .models import *

import re
import bcrypt as bc
import datetime


# Create your views here.


def get_params(request):
    if request.method == 'GET':
        return request.GET
    elif request.method == 'POST':
        return request.POST
    return {}


def get_app_user(request):
    if 'app_user' in request.session:
        try:
            return User.objects.get(login=request.session['app_user'])
        except ObjectDoesNotExist:
            return None
    return None


def index(request):
    if 'app_user' not in request.session or not User.objects.filter(login=request.session['app_user']).exists():
        courseList = Course.objects.order_by('abbrev').filter(confirmed=True)
        params = get_params(request)

        if "search" in params and params["searchThis"] != "":
            search = params["searchThis"]
            courseList = courseList.filter(Q(title__contains=search) | Q(abbrev__contains=search))
        else:
            search = None

        return render(request, 'school_app/index.html', {'courseList': courseList, 'search': search})

    return home(request)


def login(request):
    params = get_params(request)

    if len(params.keys()) == 0:
        return render(request, 'school_app/login.html')

    if params["logreg_btn"] == "Přihlásit se!":
        try:
            thisUser = User.objects.get(login=params["login"])
            login_passwd = params["password"]
            if bc.checkpw(login_passwd.encode('utf-8'), bytes(thisUser.password.encode('UTF-8')[2:-1])):
                if not thisUser.confirmed:
                    content = {'login_err': "Účet ještě nebyl ověřen."}
                    return render(request, 'school_app/login.html', content)
                request.session['app_user'] = thisUser.login
                return redirect("/")
            else:
                content = {'login_err': "Špatné jméno/heslo."}
                return render(request, 'school_app/login.html', content)
        except ObjectDoesNotExist:
            content = {'login_err': "Špatné jméno/heslo."}
            return render(request, 'school_app/login.html', content)
    elif params["logreg_btn"] == "Registrovat se":
        name = params['name']
        surname = params['surname']
        email = params['email']
        tel = params['tel']
        passwd = params['password_reg']
        passwd_ctrl = params['password_reg_ctrl']
        if name == "" or surname == "" or email == "" or passwd == "" or passwd_ctrl == "":
            content = {'register_err': "Musíš vyplnit všechny povinné položky."}
            return render(request, 'school_app/login.html', content)
        # Validace emailu
        try:
            validate_email(email)
        except ValidationError:
            content = {'register_err': "Špatný formát emailu."}
            return render(request, 'school_app/login.html', content)

        if passwd != passwd_ctrl:
            content = {'register_err': "Hesla se neshodují."}
            return render(request, 'school_app/login.html', content)

        xlogin = "x" + (surname + name)[0:5]
        login_num = 0

        while True:
            try:
                User.objects.get(login=(xlogin + str(login_num)))
                login_num += 1
            except User.DoesNotExist:
                break

        new_user = User()
        new_user.login = xlogin.lower() + str(login_num)
        new_user.firstName = name
        new_user.lastName = surname
        new_user.email = email
        new_user.phone = tel
        new_user.password = str(bc.hashpw(passwd.encode('utf-8'), bc.gensalt()))
        new_user.permission = Permission.objects.get(role="Student")
        new_user.save()
        return registered(request, new_user)

    return render(request, 'school_app/login.html')


def home(request):
    if logout(request):
        return index(request)
    app_user = get_app_user(request)
    params = get_params(request)

    registeredCourses = Course.objects.order_by('abbrev').filter(assignedtocourse__user=app_user,
                                                                 assignedtocourse__confirmed=True)
    courseList = Course.objects.order_by('abbrev').filter(confirmed=True)
    if "all" in params:
        onlyUserRegistered = False
    elif "onlyRegistered" in params:
        onlyUserRegistered = True
    else:
        # If not user-specified by clicking button, then default is if you have registered courses, show only them
        onlyUserRegistered = registeredCourses.exists()

    if "search" in params and params["searchThis"] != "":
        onlyUserRegistered = False
        search = params["searchThis"]
        courseList = courseList.filter(Q(title__contains=search) | Q(abbrev__contains=search))
    else:
        search = None

    if "cancelSearch" in params:
        onlyUserRegistered = False

    if onlyUserRegistered:
        courseList = registeredCourses

    if not courseList.exists():
        courseList = None

    content = {'courseList': courseList, 'onlyUserRegistered': onlyUserRegistered,
               'registeredCourses': registeredCourses, 'search': search}

    if app_user is not None:
        content['app_user'] = app_user

    return render(request, 'school_app/index.html', content)


def logout(request):
    params = get_params(request)

    if "logout" in params:
        del request.session['app_user']
        return True
    return False


def registered(request, new_user):
    content = {'new_user': new_user}
    return render(request, 'school_app/registered.html', content)


def users(request):
    app_user = get_app_user(request)
    if app_user is None:
        return render(request, 'school_app/users.html')

    message = ""
    params = get_params(request)

    if "selected_action" in params.keys():
        if app_user.permission_id < 5:
            message += "!!! Nemáš právo na tuto akci !!!"  # Shouldn't happen
        else:
            action = params["selected_action"]
            user_ids = list(params.keys())
            user_ids.remove("selected_action")
            user_ids.remove("csrfmiddlewaretoken")

            if len(user_ids) > 0:
                for user_id in user_ids:
                    user = User.objects.get(login=user_id)
                    if action == "confirm":
                        user.confirmed = True
                    elif action == "unconfirm":
                        if app_user.login == user_id:
                            message += "Nemůžeš sám sobě zrušit oprávnění!"
                            continue
                        else:
                            user.confirmed = False
                    elif action == "delete":
                        if app_user.login == user_id:
                            message += "Nemůžeš smazat sám sebe!"
                            continue
                        else:
                            coursesOfUser = [str(x) for x in Course.objects.filter(garant=user)]
                            if len(coursesOfUser) > 0:
                                message += " Nelze smazat {}. Určit nového garanta kurzům:" \
                                           " {}.".format(user, ", ".join(coursesOfUser))
                            else:
                                user.delete()
                                message += " Akce byla úspěšně vykonána."
                        continue  # Don't save deleted object!!
                    elif action == "role_student":
                        if app_user.login == user_id:
                            message += "Nemůžeš sám sobě snížit oprávnění!"
                            continue
                        else:
                            user.permission_id = 1
                    elif action == "role_teacher":
                        if app_user.login == user_id:
                            message += "Nemůžeš sám sobě snížit oprávnění!"
                            continue
                        else:
                            user.permission_id = 2
                    elif action == "role_garant":
                        if app_user.login == user_id:
                            message += "Nemůžeš sám sobě snížit oprávnění!"
                            continue
                        else:
                            user.permission_id = 3
                    elif action == "role_manager":
                        if app_user.login == user_id:
                            message += "Nemůžeš sám sobě snížit oprávnění!"
                            continue
                        else:
                            user.permission_id = 4
                    elif action == "role_admin":
                        user.permission_id = 5
                    else:
                        message += "Musíš vybrat jednu z platných akcí."
                        break  # Bad action
                    user.save()
                    message += " Akce byla úspěšně vykonána."

    # Ordered by group (most important first), inside group by login
    userList = User.objects.order_by('-permission', 'login')
    content = {'app_user': app_user, 'userList': userList, 'submit_msg': message}
    return render(request, 'school_app/users.html', content)


def user_detail(request, user_login):
    app_user = get_app_user(request)
    detail_user = User.objects.filter(login=user_login).first()
    editing = None
    save_err = ""
    params = get_params(request)

    if len(params) > 0:
        if "admin_edit" in params:
            editing = True
        elif "save_changes" in params:
            # Validace emailu
            try:
                validate_email(params["email"])
            except ValidationError:
                save_err = "Špatný formát emailu."
                editing = True

            if params["login"] == "" or params["firstName"] == "" or params["lastName"] == "" or params["email"] == "":
                save_err = "Kolonky login, jméno, příjmení a email nesmí být prázdné."
                editing = True

            passhash = detail_user.password
            if "passwd" in params and params["passwd"] != "":
                if params["passwd"] != params["passwdCheck"]:
                    save_err = "Obě hesla se musí shodovat!"
                    editing = True
                else:
                    passhash = str(bc.hashpw(params["passwd"].encode('utf-8'), bc.gensalt()))

            if save_err == "":
                confirmed = (params["confirmed"] == "on") if ("confirmed" in params) else False
                oldPermision = detail_user.permission_id
                newPermision = int(params["permission"])
                if newPermision < oldPermision:
                    # Downgrade to garant or higher doesn't cause any trouble
                    if newPermision <= 2:  # Check for garanting courses
                        troubleCourses = Course.objects.filter(garant=detail_user)
                        if troubleCourses.exists():
                            save_err = "Pravomoce uživatele {} byly sníženy a změny byly uloženy. Uživatel stále " \
                                       "zastává roli garanta v kurzech {}. Prosím přiděl těmto kurzům ručně nového " \
                                       "garanta.".format(detail_user, ", ".join([str(x) for x in troubleCourses]))
                            editing = True
                    if newPermision == 1:  # Check also for lecturing courses
                        lectureCourses = Course.objects.filter(lecturers__in=[detail_user])
                        for course in lectureCourses:
                            course.lecturers.remove(detail_user)
                            course.save()
                if params["login"] != detail_user.login:
                    new_user = User(login=params["login"], firstName=params["firstName"],
                                    lastName=params["lastName"],
                                    email=params["email"], password=passhash, permission_id=newPermision,
                                    phone=params["phone"], confirmed=confirmed)
                    new_user.save()  # This must be done before updating ManyToMany
                    garantOf = Course.objects.filter(garant_id=detail_user.login)
                    for course in garantOf:
                        course.garant_id = new_user.login
                        course.save()
                    lecturerOf = Course.objects.filter(lecturers__in=[detail_user.login])
                    for course in lecturerOf:
                        course.lecturers.remove(detail_user)
                        course.lecturers.add(new_user)
                        course.save()
                    assignedIn = AssignedToCourse.objects.filter(user_id=detail_user.login)
                    for assign in assignedIn:
                        assign.user_id = new_user.login
                        assign.save()
                    evalIn = Evaluation.objects.filter(user_id=detail_user.login)
                    for evaluation in evalIn:
                        evaluation.user_id = new_user.login
                        evaluation.save()
                    detail_user.delete()
                    return redirect("/user/" + new_user.login + "/")
                else:
                    detail_user.firstName = params["firstName"]
                    detail_user.lastName = params["lastName"]
                    detail_user.email = params["email"]
                    detail_user.permission_id = newPermision
                    detail_user.phone = params["phone"]
                    detail_user.confirmed = confirmed
                    detail_user.password = passhash
                    detail_user.save()

    content = {'detail_user': detail_user, 'editing': editing, 'save_err': save_err}
    if app_user is not None:
        content['app_user'] = app_user

    return render(request, 'school_app/user_detail.html', content)


def newCourse(request):
    app_user = get_app_user(request)
    if app_user is None:
        return render(request, 'school_app/newcourse.html')
    typeList = CourseType.objects.order_by("courseType")
    message = ""
    if not CourseType.objects.exists():
        message = 'Neexistuje žádný typ kurzu. Vyrob nejdřív jeden v záložce "Správa typů kurzů" \
            nebo se obrať na vedoucího či administrátora, ať nějaký typ kurzu založí.'
    params = get_params(request)

    if len(params) > 0:
        if "abbrev" not in params or "title" not in params or "type" not in params \
                or params["abbrev"] == "" or params["title"] == "" or params["type"] == "":
            message = "Musíš vyplnit všechny povinné položky."
        elif not re.match('^[a-zA-Z0-9]{3,4}$', params["abbrev"]):
            message = "Zkratka musí mít 3 až 4 znaky a může obsahovat pouze čísla a písmena bez diakritiky."
        else:
            course = Course(abbrev=params["abbrev"], title=params["title"], price=params["price"],
                            description=params["description"], courseType_id=params["type"], garant=app_user)
            course.save()
            message = "Kurz {} vytvořen!".format(course)

    content = {'typeList': typeList, 'submit_err': message}
    if app_user is not None:
        content['app_user'] = app_user

    return render(request, 'school_app/newcourse.html', content)


def courseTypes(request):
    app_user = get_app_user(request)
    message = ""
    params = get_params(request)

    if len(params) > 0:
        if "create_type" in params:
            if params["newtype"] == "":
                message = "Jméno typu kurzu nesmí být prázdné."
            elif CourseType.objects.filter(courseType=params["newtype"]).exists():
                message = "Tento typ kurzu již existuje!"
            else:
                course_type = CourseType(courseType=params["newtype"])
                course_type.save()
        elif "delete_sel" in params:
            types = list(params.keys())
            types.remove("delete_sel")
            types.remove("newtype")
            types.remove("csrfmiddlewaretoken")
            replacementType = CourseType.objects.exclude(courseType__in=types).first()
            notDeletedTypes = []
            replacedCourses = set()
            for type_id in types:
                course_type = CourseType.objects.get(courseType=type_id)
                attachedCourses = Course.objects.filter(courseType=course_type)
                if attachedCourses.exists():
                    if replacementType is None:
                        notDeletedTypes.append(course_type.courseType)
                        continue
                    else:
                        for course in attachedCourses:
                            course.courseType = replacementType
                            course.save()
                            replacedCourses.add(str(course))
                course_type.delete()
            if len(notDeletedTypes) > 0:
                message = "Nelze smazat všechny typy kurzů naráz, pokud existují nějaké kurzy.\n\
                    Tyto typy nebyly smazány: {}".format(', '.join(notDeletedTypes))
            if len(replacedCourses) > 0:
                if message != "":
                    message += "\n"
                message += "Kurzům {} byl nahrazen typ za {}".format(', '.join(replacedCourses), replacementType)
    typeList = CourseType.objects.order_by("courseType")
    content = {'app_user': app_user, 'typeList': typeList, 'submit_msg': message}
    if app_user is None:
        content = {'typeList': typeList, 'submit_msg': message}

    return render(request, 'school_app/course_types.html', content)


def my_courses(request):
    app_user = get_app_user(request)
    if app_user is None:
        return render(request, 'school_app/my_courses.html')

    if app_user.permission.id == 5:
        courseList = Course.objects.order_by('abbrev')
    else:
        courseList = Course.objects.order_by('abbrev').filter(Q(garant=app_user) | Q(lecturers=app_user)).distinct()

    content = {'courseList': list(courseList)}
    if app_user is not None:
        content['app_user'] = app_user

    return render(request, 'school_app/my_courses.html', content)


def course_approval(request):
    app_user = get_app_user(request)
    message = ""
    params = get_params(request)

    if len(params) > 0:
        courses = list(params.keys())
        if "csrfmiddlewaretoken" in courses:
            courses.remove("csrfmiddlewaretoken")
            if len(courses) > 0:
                message += "Kurz(y) "
                for course_id in courses:
                    if message != "Kurz(y) ":
                        message += ","
                    course = Course.objects.get(abbrev=course_id)
                    course.confirmed = True
                    message += course.abbrev
                    course.save()
                message += " byl(y) úspěšně schválen(y)!"
    courseList = Course.objects.order_by('abbrev').filter(confirmed=False)
    content = {'courseList': courseList, 'submit_msg': message}

    if app_user is not None:
        content['app_user'] = app_user

    return render(request, 'school_app/course_approval.html', content)


def course_detail(request):
    app_user = get_app_user(request)
    params = get_params(request)
    editing = False

    if 'predmet' not in params:
        if app_user is None:
            return render(request, 'school_app/course_detail.html')
        else:
            return render(request, 'school_app/course_detail.html', {'app_user': app_user})

    course = Course.objects.filter(abbrev=params['predmet']).first()

    if course is not None:
        message = ""
        message_edit = ""
        assignedStudentCount = User.objects.filter(assignedtocourse__course=course, assignedtocourse__confirmed=True) \
            .count()
        course_terms = Term.objects.filter(course=course).order_by('dateEnd')
        termTypes = TypeOfTerm.objects.all()
        if app_user is None:
            content = {'course': course, 'assignedStudentCount': assignedStudentCount, 'terms': course_terms}
            return render(request, 'school_app/course_detail.html', content)

        if "edit" in params:
            editing = True

        if "save_changes" in params:
            course.title = params['title']
            course.price = params['price']
            course.description = params['description']
            course.garant = User.objects.get(login=params['garant'])
            tmp_lecturer = params['lector_add']
            if tmp_lecturer != '__nikdo__':
                course.lecturers.add(User.objects.get(login=tmp_lecturer))

            tmp_lecturer = params['lector_del']
            if tmp_lecturer != '__nikdo__':
                course.lecturers.remove(User.objects.get(login=tmp_lecturer))

            tmp_student = params['student_add']
            if tmp_student != '__nikdo__':
                newAssign = AssignedToCourse(user_id=params['student_add'], course=course, confirmed=True)
                newAssign.save()
                assignedStudentCount += 1

            tmp_student = params['student_del']
            if tmp_student != '__nikdo__':
                theAssign = AssignedToCourse.objects.filter(user_id=params['student_del'], course=course).first()
                if theAssign is not None:
                    theAssign.delete()
                    assignedStudentCount -= 1

            tmp_type = params['typ_kurzu']
            if tmp_type != '__nic__':
                course.courseType = CourseType.objects.get(courseType=tmp_type)

            tmp_room = params['room_add']
            if tmp_room != '__nikdo__':
                course.rooms.add(Room.objects.get(id=int(tmp_room)))

            tmp_room = params['room_del']
            if tmp_room != '__nikdo__':
                room = Room.objects.get(id=int(tmp_room))
                termsWithThisRoom = [str(x) for x in Term.objects.filter(course=course, room=room).order_by('title')]
                if len(termsWithThisRoom) > 0:
                    message_edit = "Nemůžeš kurzu odebrat místnost {}, protože ji používají termíny {}." \
                        .format(room, ", ".join(termsWithThisRoom))
                    editing = True
                else:
                    course.rooms.remove(room)

            course.save()
        if "deleteTerm" in params:
            termIds = [x[15::] for x in params if "term-to-delete_" in x]
            for termId in termIds:
                term = Term.objects.filter(id=termId).first()
                if term is not None:
                    term.delete()

        if "approveCourse" in params:
            course.confirmed = True
            course.save()

        if "newTerm" in params:
            if params["termTitle"] == "" or "termType" not in params or params["termType"] == "" or \
                    params["termDate"] == "":
                message = "Musíš vyplnit všechny povinné položky."
            else:

                term = Term(title=params["termTitle"], termType_id=params["termType"], points=params["termPoints"],
                            description=params["termDescription"], repeatIn=params["termRepeatIn"], course=course)
                if params["termRoom"] != "":
                    room = Room.objects.filter(id=params["termRoom"]).first()
                    if room is not None and room in course.rooms.all():
                        term.room = room
                try:
                    term.date = params["termDate"]
                    if params["termDateEnd"] != "":
                        term.dateEnd = params["termDateEnd"]
                    else:
                        term.dateEnd = term.date
                    if params["termTime"] != "":
                        term.time = params["termTime"]
                    if params["termDuration"] != "":
                        term.duration = params["termDuration"]
                    # This should force parsing date and time
                    term.save()
                except:
                    message = "Chybně zadané datum či čas."
                term = Term.objects.filter(id=term.id).first()  # This will be None if exception occured
                if term is not None:
                    if term.date > term.dateEnd:
                        message = "Datum ukončení nesmí být dříve než datum zahájení"
                        term.delete()
                    else:
                        collisionFound = False
                        if term.room is not None and term.duration > datetime.time(0):
                            for collision in Term.objects.filter(room=term.room) \
                                    .exclude(duration=datetime.time(0)).exclude(id=term.id):
                                if term.collide(collision):
                                    message = "Nelze přidat termín, protože je v kolizi s termínem {} kurzu {}" \
                                        .format(collision.title, collision.course)
                                    collisionFound = True
                                    break
                        if collisionFound:
                            term.delete()
        content = {'app_user': app_user, 'course': course, 'editing': editing, 'resend': params['predmet'],
                   'assignedStudentCount': assignedStudentCount, 'terms': course_terms, 'message': message,
                   'termTypes': termTypes, 'message_edit': message_edit}

        if editing:
            userList = User.objects.order_by('-permission', 'login')
            content['users'] = userList
            typeList = CourseType.objects.order_by('courseType')
            content['types'] = typeList
            roomList = Room.objects.order_by('address')
            content['rooms'] = roomList
            students = User.objects.filter(assignedtocourse__course=course, assignedtocourse__confirmed=True) \
                .order_by('-permission', 'login')
            content['students'] = students
            # Show first student then faculty members
            notStudents = User.objects.exclude(assignedtocourse__course=course, assignedtocourse__confirmed=True) \
                .exclude(login=course.garant_id).exclude(login__in=course.lecturers.all()) \
                .order_by('permission', 'login')
            content['students_unassigned'] = notStudents

        points = {x.term_id: x for x in Evaluation.objects.filter(user=app_user, term__course=course)}  # TermID:Eval
        if len(points) > 0:
            content['points'] = points

        if "delete_course" in params:
            course.delete()
            return render(request, 'school_app/course_detail.html', {'app_user': app_user, 'deleted': True})

        return render(request, 'school_app/course_detail.html', content)

    return render(request, 'school_app/course_detail.html', {'app_user': app_user})


def room_detail(request):
    app_user = get_app_user(request)
    params = get_params(request)

    if "room" not in params:
        if app_user is None:
            return render(request, 'school_app/room_detail.html')
        return render(request, 'school_app/room_detail.html', {'app_user': app_user})

    try:
        room = Room.objects.get(id=int(params['room']))
    except Room.DoesNotExist:
        if app_user is None:
            return render(request, 'school_app/room_detail.html')
        return render(request, 'school_app/room_detail.html', {'app_user': app_user})

    content = {'room': room, 'resend': params['room'], 'editing': False}

    if "delete" in params:
        course_error = Course.objects.order_by('abbrev').filter(rooms=room).distinct()
        term_error = Term.objects.order_by('title').filter(room=room).distinct()
        if len(course_error) == 0 and len(term_error) == 0:
            room.delete()
        else:
            content['term_err'] = term_error
            content['course_err'] = course_error

    if app_user is not None:
        content['app_user'] = app_user

    if "save_changes" in params:
        room.address = params['address']
        room.doorNumber = int(params['doorNumber'])
        room.capacity = int(params['capacity'])
        room.roomType = RoomType.objects.get(id=int(params['typ_mistnosti']))
        room.save()

        equip = Equipment.objects.get(id=params['equip_change'])
        for x in RoomEquipment.objects.filter(equipment=equip):
            if x.room == room:
                x.delete()
        if params["count"] != "0":
            RoomEquipment(equipment=equip, room=room, count=params["count"]).save()

    if "edit" in params:
        content['editing'] = True
        content['types'] = RoomType.objects.order_by('roomType')

    content['room_equip'] = RoomEquipment.objects.filter(room=params['room'])
    content['equipment'] = Equipment.objects.order_by('name')

    return render(request, 'school_app/room_detail.html', content)


def course_register(request):
    app_user = get_app_user(request)
    if app_user is None:
        return render(request, 'school_app/course_register.html')
    params = get_params(request)

    if len(params) > 0:
        courses = list(params.keys())
        if "csrfmiddlewaretoken" in courses:
            courses.remove("csrfmiddlewaretoken")
            register = None
            if "register" in courses:
                courses.remove("register")
                register = True
            elif "cancel" in courses:
                courses.remove("cancel")
                register = False
            if register is not None:
                for course in courses:
                    assign = AssignedToCourse.objects.filter(course_id=course, user=app_user).first()
                    if register and assign is None:
                        newAssigned = AssignedToCourse(user=app_user, course_id=course)
                        newAssigned.save()
                    elif not register and assign is not None:
                        assign.delete()
    # Don't allow to register already registered courses
    my_registered_courses: set = {x.course.abbrev for x in AssignedToCourse.objects.filter(user=app_user)}
    # or courses when current user is teaching.
    my_registered_courses |= {x.abbrev for x in Course.objects.filter(
        Q(garant=app_user) | Q(lecturers=app_user)).distinct()}
    courseList = Course.objects.order_by('abbrev').filter(confirmed=True).exclude(abbrev__in=my_registered_courses)
    registerList = Course.objects.filter(assignedtocourse__user=app_user, assignedtocourse__confirmed=False)
    content = {'courseList': courseList, 'registerList': registerList}

    if app_user is not None:
        content['app_user'] = app_user

    return render(request, 'school_app/course_register.html', content)


def register_manage(request):
    app_user = get_app_user(request)
    if app_user is None:
        return render(request, 'school_app/register_manage.html')

    params = get_params(request)

    if len(params) > 0:
        registrations = list(params.keys())
        registrations.remove("csrfmiddlewaretoken")
        action = None
        if "btn_approve" in registrations:
            action = "approve"
            registrations.remove("btn_approve")
        elif "btn_delete" in registrations:
            action = "delete"
            registrations.remove("btn_delete")
        if len(registrations) > 0 and action is not None:
            for reg_id in registrations:
                assigned = AssignedToCourse.objects.get(id=reg_id)
                if action == "delete":
                    assigned.delete()
                else:
                    assigned.confirmed = True
                    assigned.save()

    register_list = []
    if app_user.permission_id == 3:
        course_filter = Course.objects.filter(garant=app_user)
        register_list_tmp = AssignedToCourse.objects.filter(confirmed=False)
        for i in register_list_tmp:
            if i.course in course_filter:
                register_list.append(i)
    elif app_user.permission_id >= 4:
        register_list = AssignedToCourse.objects.filter(confirmed=False)

    content = {'app_user': app_user, 'register_list': register_list}
    return render(request, 'school_app/register_manage.html', content)


def term_detail(request, term_id):
    app_user = get_app_user(request)
    term = Term.objects.filter(id=term_id).first()
    if app_user is None:
        if term is not None:
            return render(request, 'school_app/term_detail.html', {'app_user': app_user, 'term': term})
        return render(request, 'school_app/term_detail.html')
    if term is None:
        return render(request, 'school_app/term_detail.html', {'app_user': app_user})
    message = ""
    editing = None
    params = get_params(request)

    if (app_user.permission_id >= 4 or
            (app_user.permission_id == 3 and term.course.garant == app_user) or
            app_user.permission_id == 2 and app_user in term.course.lecturers.all()):
        editing = "admin_edit" in params
    if len(params) > 0:
        if "save_changes" in params:
            try:
                if "termRoom" in params:
                    room = Room.objects.filter(id=params["termRoom"]).first()
                else:
                    room = None
                endDate = params["termDateEnd"] if params["termDateEnd"] != "" else params["termDate"]
                duration = params["termDuration"] if params["termDuration"] != "" else datetime.time(0)
                time = params["termTime"] if params["termTime"] != "" else datetime.time(0)
                repeatIn = params["termRepeatIn"] if params["termRepeatIn"] != "" else 0
                newTerm = Term(date=params["termDate"], time=time, duration=duration,
                               repeatIn=repeatIn, dateEnd=endDate, room=room,
                               title=term.title, termType=term.termType, course=term.course)
                newTerm.save()
                newTerm = Term.objects.get(id=newTerm.id)
                newTerm.delete()
                goodToGo = True
                if newTerm.date > newTerm.dateEnd:
                    message = "Datum ukončení nesmí být dříve než datum zahájení"
                    goodToGo = False
                if newTerm.duration > datetime.time(0) and newTerm.room is not None and \
                        (term.date != newTerm.date or term.time != newTerm.time or term.dateEnd != newTerm.dateEnd or
                         term.duration != newTerm.duration or term.repeatIn != newTerm.repeatIn or
                         term.room != newTerm.room):
                    for collision in Term.objects.filter(room=newTerm.room) \
                            .exclude(duration=datetime.time(0)).exclude(id=term.id):
                        if newTerm.collide(collision):
                            message = "Nelze upravit termín, protože by byl v kolizi s termínem {} kurzu {}" \
                                .format(collision.title, collision.course)
                            goodToGo = False
                            break
                if goodToGo:
                    term.room = room
                    term.title = params["termTitle"]
                    term.termType_id = params["termType"]
                    term.description = params["termDescription"]
                    term.points = params["termPoints"]
                    term.date = newTerm.date
                    term.dateEnd = newTerm.dateEnd
                    term.duration = newTerm.duration
                    term.time = newTerm.time
                    term.repeatIn = newTerm.repeatIn
                    term.save()
                else:
                    editing = True
            except:
                message = "Chybně zadané datum či čas."
                editing = True
        elif "submit_eval" in params:
            if "eval" in params:
                points = int(params["evalPoints"])
                if not 0 <= points <= term.points:
                    message = "Hodnota bodů musí být větší či rovna nule a menší či rovna {}".format(term.points)
                else:
                    evaluation = Evaluation.objects.filter(user_id=params["eval"], term=term).first()
                    if evaluation is not None:
                        evaluation.points = points
                        evaluation.save()
                    else:
                        evalUser = User.objects.filter(login=params["eval"], assignedtocourse__course=term.course,
                                                       assignedtocourse__confirmed=True).first()
                        if evalUser is not None:
                            evaluation = Evaluation(user=evalUser, term=term, points=points)
                            evaluation.save()
                        else:
                            message = "Tento uživatel není studentem tohoto kurzu."
    content = {'term': term, 'editing': editing, 'message': message, 'app_user': app_user}

    if editing:
        termTypes = TypeOfTerm.objects.all()
        content['termTypes'] = termTypes
        content['termDate'] = term.date.strftime('%Y-%m-%d')
        content['termDateEnd'] = term.dateEnd.strftime('%Y-%m-%d')
        content['termTime'] = term.time.strftime('%H:%M')
        content['termDuration'] = term.duration.strftime('%H:%M')
    elif editing is not None and not editing:
        courseUsers = User.objects.filter(assignedtocourse__confirmed=True, assignedtocourse__course=term.course)
        evals = []
        for cUser in courseUsers:
            evaluation = Evaluation.objects.filter(user=cUser, term=term).first()
            if evaluation is None:
                evaluation = Evaluation(user=cUser, term=term, points=None)
            evals.append(evaluation)
        content['evals'] = evals if len(evals) > 0 else None  # To make frontend part easier
    evaluation = Evaluation.objects.filter(user=app_user, term=term).first()
    if evaluation is not None:
        content['points'] = evaluation.points

    content['term_id'] = term_id
    content['course_id'] = term.course.abbrev
    return render(request, 'school_app/term_detail.html', content)


def rooms(request):
    app_user = get_app_user(request)

    if app_user is None:
        return render(request, 'school_app/rooms.html')

    rooms_list = Room.objects.order_by('doorNumber')
    content = {'app_user': app_user, 'rooms_list': rooms_list}
    return render(request, 'school_app/rooms.html', content)


def terms(request):
    app_user = get_app_user(request)
    if app_user is None:
        return render(request, 'school_app/terms.html')
    if app_user.permission_id >= 4:
        term = Term.objects.order_by('date')
    else:
        term = Term.objects.filter(Q(course__assignedtocourse__user=app_user) | Q(course__garant=app_user) |
                                   Q(course__lecturers__in=[app_user])).order_by('date')
    content = {'terms': term, 'app_user': app_user}
    points = {x.term_id: x for x in Evaluation.objects.filter(user=app_user, term__in=term)}  # TermID:Eval
    if len(points) > 0:
        content['points'] = points
    return render(request, 'school_app/terms.html', content)


def error_404(request):
    app_user = get_app_user(request)
    content = {'app_user': app_user}
    return render(request, 'school_app/404.html', content)


def new_room(request):
    app_user = get_app_user(request)
    if app_user is None:
        return render(request, 'school_app/new_room.html')
    typeList = RoomType.objects.order_by("id")
    message = ""
    params = get_params(request)

    if len(params) > 0:
        if "addr" not in params or "door_num" not in params or "cap" not in params or "type" not in params \
                or params["addr"] == "" or params["door_num"] == "" or params["cap"] == "" or params["type"] == "":
            message = "Musíš vyplnit všechny povinné položky."
        else:
            room = Room(address=params["addr"], doorNumber=params["door_num"],
                        capacity=params["cap"], roomType=RoomType.objects.get(id=int(params["type"])))
            room.save()
            message = "Místnost {} vytvořena!".format(room)

    content = {'app_user': app_user, 'typeList': typeList, 'submit_err': message}
    return render(request, 'school_app/new_room.html', content)


def equipment(request):
    app_user = get_app_user(request)
    content = {'equipment': Equipment.objects.order_by("name")}

    if app_user is not None:
        content['app_user'] = app_user

    return render(request, 'school_app/equipment.html', content)


def equip_detail(request):
    app_user = get_app_user(request)
    params = get_params(request)

    if "equip" not in params:
        if app_user is None:
            return render(request, 'school_app/equip_detail.html')
        return render(request, 'school_app/equip_detail.html', {'app_user': app_user})

    try:
        equip = Equipment.objects.get(id=int(params['equip']))
    except Equipment.DoesNotExist:
        if app_user is None:
            return render(request, 'school_app/equip_detail.html')
        return render(request, 'school_app/equip_detail.html', {'app_user': app_user})

    if "delete" in params:
        equip.delete()

    content = {'equip': equip, 'resend': params['equip'], 'editing': False}

    if app_user is not None:
        content['app_user'] = app_user

    if "save_changes" in params:
        equip.name = params['name']
        equip.description = params['description']
        equip.cost = int(params['cost'])
        equip.save()

    if "edit" in params:
        content['editing'] = True

    return render(request, 'school_app/equip_detail.html', content)


def new_equipment(request):
    app_user = get_app_user(request)
    if app_user is None:
        return render(request, 'school_app/new_equipment.html')
    message = ""
    params = get_params(request)

    if len(params) > 0:
        if "description" not in params:
            params["description"] = ""

        if "name" not in params or "cost" not in params \
                or params["name"] == "" or params["cost"] == "":
            message = "Musíš vyplnit všechny povinné položky."
        else:
            equip = Equipment(name=params["name"], description=params["description"], cost=params["cost"])
            equip.save()
            message = "Vybavení {} vytvořeno!".format(equip)

    content = {'app_user': app_user, 'submit_err': message}
    return render(request, 'school_app/new_equipment.html', content)


def upload(request):
    app_user = get_app_user(request)
    if app_user is None:
        return render(request, 'school_app/upload.html')
    message = ""
    params = get_params(request)

    content = {'app_user': app_user}
    if len(params) > 0:
        if "cesta" in params:
            try:
                if 'soubor' in request.FILES:
                    uploaded_file = request.FILES['soubor']
                    fs = FileSystemStorage(location="media/" + params['cesta'])
                    hadToDelete = False
                    if fs.exists(uploaded_file.name):
                        fs.delete(uploaded_file.name)
                        hadToDelete = True
                    filename = fs.save(uploaded_file.name, uploaded_file)
                    content['resend'] = params['cesta']
                    if hadToDelete:
                        message = "Soubor se jménem {} se v tomto termínu již nacházel a byl přepsán.".format(filename)
                    else:
                        message = "Soubor {} úspěšně nahrán.".format(filename)
                else:
                    message = "Soubor nebyl zadán."
                    content['resend'] = params['cesta']
            except:
                content['resend'] = params['cesta']
                message = "Soubor nebyl zadán nebo nastala chyba při nahrávání souboru, zkus to znovu."
        elif 'kurz' in params and 'termin' in params:
            content['resend'] = params['kurz'] + "_" + params['termin']
    content['submit_err'] = message
    return render(request, 'school_app/upload.html', content)


def files(request):
    app_user = get_app_user(request)
    if app_user is None:
        return render(request, 'school_app/upload.html')
    message = ""
    params = get_params(request)

    content = {'app_user': app_user}
    cesta = ""
    deletable = False

    if len(params) > 0:
        if "cesta" in params:
            cesta = params['cesta']
        elif 'kurz' in params and 'termin' in params:
            cesta = params['kurz'] + "_" + params['termin']
        else:
            cesta = "__nezadano__"
        try:
            course = Course.objects.get(abbrev=cesta.split("_")[0])
            course_lecturers = course.lecturers.all()
            if app_user == course.garant:
                deletable = True
            elif app_user in course_lecturers:
                deletable = True
            elif app_user.permission.id >= 4:
                deletable = True
            content['deletable'] = deletable
        except:
            pass

        plna_cesta = "media/" + cesta

        for i in params:
            if i.find("smazat[") == 0:
                target = params[i]
                try:
                    fs = FileSystemStorage(plna_cesta)
                    if fs.exists(target):
                        fs.delete(target)
                except:
                    pass

        try:
            soubory = [f for f in os.listdir(plna_cesta) if os.path.isfile(os.path.join(plna_cesta, f))]
            content['plna_cesta'] = plna_cesta + "/"
            content['cesta'] = cesta
            content['soubory'] = soubory
            if not soubory:
                content['deletable'] = False
        except:
            content['deletable'] = False

    content['resend'] = cesta
    content['submit_err'] = message
    return render(request, 'school_app/files.html', content)


def send_file(request, file_req):
    app_user = get_app_user(request)
    if app_user is None:
        return render(request, 'school_app/upload.html')

    filepath = 'media/' + file_req
    return FileResponse(open(filepath, 'rb'))


def schedule(request):
    app_user = get_app_user(request)
    content = {}

    if app_user is not None:
        content['app_user'] = app_user
        user_terms = Term.objects.filter(Q(course__assignedtocourse__user=app_user) |
                                         Q(course__garant=app_user) |
                                         Q(course__lecturers__in=[app_user]))\
            .exclude(duration=datetime.time(0)).order_by('date').order_by('course').distinct()

        user_terms_weekly = user_terms.filter(repeatIn__gte=1)
        user_terms_once = user_terms.filter(repeatIn=0)
        week_days = ["", "Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek", "Sobota", "Neděle"]
        schedule = ""

        for den in range(0, 8):
            schedule += "<tr><th>" + week_days[den] + "</th>"
            for hod in range(7, 23):
                if den == 0:
                    schedule += "<th>" + datetime.time(hour=hod).strftime("%H:00 - %H:50") + "</th>"
                else:
                    termString = ""
                    for term in user_terms_weekly:
                        if term.date.weekday() == den - 1 \
                                and term.time.hour <= hod < term.time.hour + term.duration.hour:
                            termString += '<a href="/term/{}/">{}</a><br>'.format(term.id, term.course.abbrev + " - " +
                                                                                 term.termType.abbrev)
                    for term in user_terms_once:
                        if term.date.weekday() == den - 1 \
                                and term.time.hour <= hod < term.time.hour + term.duration.hour:
                            termString += '<a href="/term/{}/">{}</a><br>'\
                                .format(term.id, term.course.abbrev + " - " + term.termType.abbrev
                                        + term.date.strftime(" %d. %m."))
                    schedule += "<td class=\"center\">{}</td>".format(termString)

        schedule = "<table class=\"user_table\">{}</table>".format(schedule)
        content['schedule'] = schedule
    return render(request, 'school_app/schedule.html', content)
