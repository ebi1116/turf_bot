from django.db import models


class Area(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Turf(models.Model):
    name = models.CharField(max_length=100)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    owner_phone = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.name} ({self.area.name})"


class Booking(models.Model):
    area = models.CharField(max_length=100)
    turf = models.CharField(max_length=100)
    date = models.DateField()
    slot = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.turf} - {self.date} - {self.slot}"


class UserSession(models.Model):
    phone_number = models.CharField(max_length=20, unique=True)
    step = models.CharField(max_length=50, null=True, blank=True)

    selected_area = models.CharField(max_length=100, null=True, blank=True)
    selected_turf = models.CharField(max_length=100, null=True, blank=True)
    selected_date = models.DateField(null=True, blank=True)
    selected_slot = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.phone_number