from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Course)
admin.site.register(User)
admin.site.register(Equipment)
admin.site.register(Room)
admin.site.register(Term)
admin.site.register(Permission)
admin.site.register(Tag)
admin.site.register(RoomType)
admin.site.register(CourseType)
admin.site.register(TypeOfTerm)
admin.site.register(RoomEquipment)
admin.site.register(AssignedToCourse)
