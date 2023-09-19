from django.db import models
import datetime


class CourseType(models.Model):
    # typ kurzu
    courseType = models.CharField(max_length=255)

    def __str__(self):
        return self.courseType


class Tag(models.Model):
    # Tagy
    tag = models.CharField(max_length=32)
    description = models.CharField(max_length=512, default="", blank=True)

    def __str__(self):
        return self.tag


class TypeOfTerm(models.Model):
    # Typ termínu
    termType = models.CharField(max_length=255)

    def __str__(self):
        return self.termType

    @property
    def abbrev(self):
        return self.termType[0:1]


class RoomType(models.Model):
    # Typ místnosti
    roomType = models.CharField(max_length=255)

    def __str__(self):
        return self.roomType


class Room(models.Model):
    # Místnost
    address = models.CharField(max_length=255, default="", blank=True)
    doorNumber = models.IntegerField()
    capacity = models.IntegerField(default=30, blank=True)  # because capacity 0 person doesn't make sense
    roomType = models.ForeignKey(RoomType, on_delete=models.DO_NOTHING)

    def __str__(self):
        return "Místnost č.{}, Budova {}".format(self.doorNumber, self.address)


class Permission(models.Model):
    # Úroveň uživatele
    role: str = models.CharField(max_length=255)

    def __str__(self):
        return self.role


class User(models.Model):
    # Uživatel
    login = models.CharField(primary_key=True, max_length=8)
    firstName = models.CharField(max_length=255)
    lastName = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    phone = models.CharField(max_length=255, default="", blank=True)
    password = models.CharField(max_length=255)
    permission = models.ForeignKey(Permission, on_delete=models.DO_NOTHING)
    confirmed = models.BooleanField(default=False)

    def __str__(self):
        return self.login


class Course(models.Model):
    # Výukový Kurz
    abbrev = models.CharField(primary_key=True, max_length=4)
    title = models.CharField(max_length=255, default="")
    description = models.CharField(max_length=512, default="", blank=True)
    courseType = models.ForeignKey(CourseType, on_delete=models.DO_NOTHING)
    price = models.IntegerField(default=0, blank=True)
    garant = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='garant')
    tags = models.ManyToManyField(Tag, blank=True)
    confirmed = models.BooleanField(default=False)
    lecturers = models.ManyToManyField(User, blank=True, related_name='lecturers')
    rooms = models.ManyToManyField(Room, blank=True, related_name='course_room')

    def __str__(self):
        return "[" + self.abbrev+"] " + self.title


class Term(models.Model):
    # Termín kurzu
    title = models.CharField(max_length=255)
    termType = models.ForeignKey(TypeOfTerm, on_delete=models.DO_NOTHING)
    description = models.CharField(max_length=512, default="", blank=True)
    points = models.IntegerField(default=0, blank=True)
    date = models.DateField(null=True, blank=True)
    dateEnd = models.DateField(null=True, blank=True)
    duration = models.TimeField(default=datetime.time(0), blank=True)
    time = models.TimeField(default=datetime.time(0), blank=True)
    repeatIn = models.IntegerField(default=0, blank=True)  # 0 = no repeat
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.DO_NOTHING, null=True, blank=True)

    def __str__(self):
        return self.title

    @staticmethod
    def datetimeFromDateAndTime(date, time):
        return datetime.datetime(date.year, date.month, date.day, time.hour, time.minute, time.second, time.microsecond)

    @staticmethod
    def timeToDelta(time):
        return datetime.timedelta(hours=time.hour, minutes=time.minute, seconds=time.second,
                                  microseconds=time.microsecond)

    def collide(self, other):
        if type(other) != Term:
            raise TypeError
        if self.duration == datetime.time(0) or other.duration == datetime.time(0) or self.room is None or\
                other.room is None or self.room != other.room:
            return False
        start = Term.datetimeFromDateAndTime(self.date, self.time)
        end = start + Term.timeToDelta(self.duration)
        if self.repeatIn == 0 and other.repeatIn == 0:
            otherStart = Term.datetimeFromDateAndTime(other.date, other.time)
            otherEnd = otherStart + Term.timeToDelta(other.duration)
            return start <= otherStart < end or otherStart <= start < otherEnd

        return Term.compare_tarray(Term.timearray(self), Term.timearray(other))

    @staticmethod
    def timearray(other):
        ret = []
        start = Term.datetimeFromDateAndTime(other.date, other.time)
        end = start + Term.timeToDelta(other.duration)
        repeatIn = other.repeatIn
        finish = Term.datetimeFromDateAndTime(other.dateEnd, other.time)
        tmp = [start, end]
        ret.append(tmp[:])
        while True:
            start += datetime.timedelta(weeks=repeatIn)
            end = start + Term.timeToDelta(other.duration)
            if start > finish:
                break
            tmp = [start, end]
            ret.append(tmp[:])
            if start >= finish:
                break
        return ret

    @staticmethod
    def compare_tarray(this, other):
        for i in this:
            for j in other:
                if (i[0] <= j[0] < i[1]) or (i[0] < j[1] <= i[1]):
                    return True
        return False


class Equipment(models.Model):
    # Vybavení
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=512, default="", blank=True)
    cost = models.IntegerField(default=0, blank=True)

    def __str__(self):
        return self.name


class RoomEquipment(models.Model):
    # Vybavení místností
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    count = models.IntegerField(default=1, blank=True)

    def __str__(self):
        return str(self.equipment) + ", " + str(self.count) + "ks"


class AssignedToCourse(models.Model):
    # Zapsáni na kurz
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    confirmed = models.BooleanField(default=False)

    def __str__(self):
        return "AssignedTo(" + str(self.user) + "->" + str(self.course) + ")"


class Evaluation(models.Model):
    # Hodnocení
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    points = models.IntegerField(default=0)

    def __str__(self):
        return "AssignedTo(" + str(self.user) + "->" + str(self.term) + ":" + str(self.points) + ")"
