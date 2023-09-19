from django.apps import AppConfig


class SchoolAppConfig(AppConfig):
    name = 'school_app'

    def ready(self):
        from school_app.models import Permission, TypeOfTerm, RoomType
        try:
            if len(Permission.objects.all()) == 0:
                print('Creating basic permission role groups...')
                student = Permission(role="Student", id=1)
                teacher = Permission(role="Lektor", id=2)
                garant = Permission(role="Garant", id=3)
                manager = Permission(role="Vedoucí", id=4)
                admin = Permission(role="Administrátor", id=5)

                student.save()
                teacher.save()
                garant.save()
                manager.save()
                admin.save()

            if len(TypeOfTerm.objects.all()) == 0:
                print('Creating basic types of terms...')
                lecture = TypeOfTerm(termType="Přednáška", id=1)
                lab = TypeOfTerm(termType="Cvičení", id=2)
                test = TypeOfTerm(termType="Test", id=3)
                exam = TypeOfTerm(termType="Zkouška", id=4)
                homework = TypeOfTerm(termType="Domácí úkol", id=5)
                credit = TypeOfTerm(termType="Zápočet", id=6)

                lecture.save()
                lab.save()
                test.save()
                exam.save()
                homework.save()
                credit.save()

            if len(RoomType.objects.all()) == 0:
                print('Creating basic types of rooms...')
                teachingRoom = RoomType(roomType="Učebna", id=1)
                lectureRoom = RoomType(roomType="Přednášková místnost", id=2)
                lab = RoomType(roomType="Laboratoř", id=3)
                office = RoomType(roomType="Kancelář", id=4)
                sittingRoom = RoomType(roomType="Zasedací místnost", id=5)
                studyRoom = RoomType(roomType="Studovna", id=6)
                storage = RoomType(roomType="Sklad", id=7)
                others = RoomType(roomType="Ostatní", id=8)

                teachingRoom.save()
                lectureRoom.save()
                lab.save()
                office.save()
                sittingRoom.save()
                studyRoom.save()
                storage.save()
                others.save()
        except Exception:
            print("WARNING: Database is not set yet.")  # Do nothing yet, database is not set
