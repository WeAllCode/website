from logging import Formatter

from django.conf import settings
from django.db import models

from simple_salesforce import Salesforce as sf
from simple_salesforce.format import format_soql

from coderdojochi.settings import SALESFORCE_TOKEN


class CommonInfo(models.Model):
    # Auto create/update
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        abstract = True


def salesforce_login():
    return sf(
        username=settings.SALESFORCE_USER,
        password=settings.SALESFORCE_PASSWORD,
        security_token=settings.SALESFORCE_TOKEN,
        domain="cs201",
    )


class Salesforce:
    def __init__(self):
        self.salesforce_obj = sf(
            username=settings.SALESFORCE_USER,
            password=settings.SALESFORCE_PASSWORD,
            security_token=settings.SALESFORCE_TOKEN,
            domain="cs201",
        )

    # create a guardian query fucntion
    def update_contact(
        self,
        first_name,
        last_name,
        birthdate,
        gender,
        race,
        ethnicity,
        role,
        active,
        school_name=None,
        school_type=None,
        medical=None,
        medications=None,
        work_place=None,
        phone=None,
        zip=None,
    ):
        query = "SELECT Id FROM Contact WHERE FirstName = {} and LastName = {} and Birthdate = {}"
        formatted = format_soql(query, first_name, last_name, birthdate)
        results = self.salesforce_obj.query(formatted)
        exists = results["totalSize"]

        if not exists:
            self.salesforce_obj.Contact.create(
                {
                    "FirstName": first_name,
                    "LastName": last_name,
                    # "Birthdate": birthdate,
                    "Gender__c": gender,
                    "hed__Race__c": race,
                    "hed__Ethnicity__c": ethnicity,
                    # "School_Name__c	": school_name,
                    "Role__c": role,
                    "School_Type__c": school_type,
                    "Medical__c": medical,
                    "Medications__c": medications,
                    "Active__c": active,
                    "GW_Volunteers__Volunteer_Organization__c": work_place,
                    "Phone": phone,
                    # "Zip__c": zip,
                },
            )
        else:
            id = results["records"][0]["Id"]
            self.salesforce_obj.Contact.update(
                id,
                {
                    "FirstName": first_name,
                    "LastName": last_name,
                    # "Birthdate": birthdate,
                    "Gender__c": gender,
                    "hed__Race__c": race,
                    "hed__Ethnicity__c": ethnicity,
                    # "School_Name__c	": school_name,
                    "Role__c": role,
                    "School_Type__c": school_type,
                    "Medical__c": medical,
                    "Medications__c": medications,
                    "Active__c": active,
                    "GW_Volunteers__Volunteer_Organization__c": work_place,
                    "Phone": phone,
                    "Zip__c": zip,
                },
            )
        pass

    def upsert_course(self, name, active, course_id, course_type, description, duration, minimum_age, maximum_age):
        query = "SELECT Id FROM hed__Course__c WHERE Name = {} and hed__Course_ID__c = {}"
        formatted = format_soql(query, name, course_id)
        results = self.salesforce_obj.query(formatted)
        exists = results["totalSize"]

        if not exists:
            self.salesforce_obj.hed__Course__c.create(
                {
                    "Name": name,
                    "Active__c": active,
                    "hed__Course_ID__c": course_id,
                    "Course_Type__c": course_type,
                    "hed__Description__c": description,
                    "hed__Account__c": "0017h00000ZfotKAAR",
                    "Duration__c": duration.__str__(),
                    "Minimum_Age__c": minimum_age.__str__(),
                    "Maximum_Age__c": maximum_age.__str__(),
                }
            )

        else:
            id = results["records"][0]["Id"]
            self.salesforce_obj.hed__Course__c.update(
                id,
                {
                    "Name": name,
                    "Active__c": active,
                    "hed__Course_ID__c": course_id,
                    "Course_Type__c": course_type,
                    "hed__Description__c": description,
                    "hed__Account__c": "0017h00000ZfotKAAR",
                    "Duration__c": duration.__str__(),
                    "Minimum_Age__c": minimum_age.__str__(),
                    "Maximum_Age__c": maximum_age.__str__(),
                }
            )

    # create contact("FirstName": self.first_name,
    # "LastName": self.last_name,
    # "Birthdate": self.birthday.__str__(),
    # "Gender__c": self.gender,
    # "hed__Race__c": self.race,
    # "hed__Ethnicity__c": self.ethnicity,
    # # "School_Name__c	": self.school_name,
    # "Role__c":"student",
    # "School_Type__c": self.school_type,
    # "Medical__c": self.medical_conditions,
    # "Medications__c": self.medications,)
    # def create_contact(first_name,last_name,birthdate, gender, race, ethnicity, school_name, )
    # can write your own upsert: check to see if contact exists
