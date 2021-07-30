import json
from datetime import date, datetime, timedelta
from logging import Formatter
from re import S
from pytz import timezone
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


class Salesforce:
    def __init__(self):
        self.salesforce_obj = sf(
            username=settings.SALESFORCE_USER,
            password=settings.SALESFORCE_PASSWORD,
            security_token=settings.SALESFORCE_TOKEN,
            domain="cs201",
        )

    def in_account_list(self, household_name):
        query = "SELECT Id FROM Account WHERE Name = {}"
        formatted = format_soql(query, household_name)
        results = self.salesforce_obj.query(formatted)

        exists = results["totalSize"]

        if exists:
            id = results["records"][0]["Id"]
            return id

        return exists

    def contact_id_query(self, ext_id):
        query = "SELECT Id FROM Contact WHERE External_Id__c = '{}'"

        formatted = format_soql(query, ext_id)

        results = self.salesforce_obj.query(formatted)

        if results["totalSize"]:
            id = results["records"][0]["Id"]

            return id

        return None

    def query_timeblocks(self, start_time, end_time):
        print(start_time)
        print(end_time)

        query = f"SELECT Id FROM hed__Time_Block__c WHERE hed__Start_Time__c >= {start_time} AND hed__End_Time__c < {end_time}"

        results = self.salesforce_obj.query(query)

        if results["totalSize"]:
            return results["records"][0]["Id"]

        return None

    def course_query(self, course_id):
        query = "SELECT Id FROM hed__Course__c WHERE hed__Course_ID__c = {}"
        formatted = format_soql(query, course_id)
        results = self.salesforce_obj.query(formatted)

        exists = results["totalSize"]

        if exists:
            return results["records"][0]["Id"]

        return None

    def offering_query(self, ext_id):

        query = "SELECT Id FROM hed__Course_Offering__c WHERE External_Id__c = '{}'"

        formatted_query = format_soql(
            query,
            ext_id,
        )

        results = self.salesforce_obj.query(formatted_query)

        num_same_offerings = results["totalSize"]

        if num_same_offerings:
            return results["records"][0]["Id"]

        return None

    def order_query(self, ext_id):

        query = "SELECT Id FROM hed__Course_Enrollment__c WHERE External_Id__c = '{}'"

        formatted_query = format_soql(query, ext_id)

        results = self.salesforce_obj.query(formatted_query)

        exists = results["totalSize"]

        if exists:
            return results["records"][0]["Id"]

        return None

    def create_relationship(
        self,
        parent_first_name,
        parent_last_name,
        child_first_name,
        child_last_name,
    ):
        parent_query = format_soql(
            "SELECT Id FROM Contact WHERE FirstName = {} AND LastName = {}",
            parent_first_name,
            parent_last_name,
        )
        parent_result = self.salesforce_obj.query(parent_query)
        parent = parent_result["records"][0]["Id"]

        child_query = format_soql(
            "SELECT Id FROM Contact WHERE FirstName = {} AND LastName = {}",
            child_first_name,
            child_last_name,
        )
        child_result = self.salesforce_obj.query(child_query)
        child = child_result["records"][0]["Id"]

        relationship_query = format_soql(
            "SELECT Id FROM hed__Relationship__c WHERE hed__Contact__c = {} AND hed__RelatedContact__c = {}",
            parent,
            child,
        )
        relationship_results = self.salesforce_obj.query(relationship_query)
        exist = relationship_results["totalSize"]

        if not exist:
            print(f"No relationship btwn {child_first_name} and {parent_first_name}")
            self.salesforce_obj.hed__Relationship__c.create(
                {
                    "hed__Contact__c": parent,
                    "hed__RelatedContact__c": child,
                    "hed__Type__c": "Child",
                    "hed__Status__c": "Current",
                }
            )
        else:
            print(f"Relationship btwn {child_first_name} and {parent_first_name}")

    def upsert_contact(
        self,
        first_name,
        last_name,
        birthdate,
        gender,
        race,
        ethnicity,
        role,
        active,
        ext_id,
        school_name=None,
        school_type=None,
        medical=None,
        medications=None,
        work_place=None,
        phone=None,
        email=None,
        zip_code=None,
        parent=None,
    ):
        exists = self.contact_id_query(ext_id=ext_id)

        household_name = f"{last_name} Household"
        account_created = self.in_account_list(household_name)

        parent_id = self.contact_id_query(ext_id=parent.id) if parent is not None else None

        data = {
            "FirstName": first_name,
            "LastName": last_name,
            "Birthdate": birthdate.__str__(),
            "Gender__c": gender,
            "hed__Race__c": race,
            "hed__Ethnicity__c": ethnicity,
            "School_Name__c": school_name,
            "School_Type__c": school_type,
            "Role__c": role,
            "Parent__c": parent_id,
            "Medical__c": medical,
            "Medications__c": medications,
            "Active__c": active,
            "GW_Volunteers__Volunteer_Organization__c": work_place,
            "Phone": phone,
            "Zip__c": zip_code,
            "External_Id__c": ext_id,
            "Email": email,
        }

        if not exists:
            if account_created:

                data["AccountId"] = account_created

                self.salesforce_obj.Contact.create(
                    data,
                )
            else:

                self.salesforce_obj.Contact.create(
                    data,
                )
        else:

            self.salesforce_obj.Contact.update(
                exists,
                data,
            )

    def upsert_course(
        self,
        name,
        active,
        course_id,
        course_type,
        description,
        duration,
        minimum_age,
        maximum_age,
    ):

        exists = self.course_query(course_id=course_id)

        if not exists:
            self.salesforce_obj.hed__Course__c.create(
                {
                    "Name": name,
                    "Active__c": active,
                    "hed__Course_ID__c": course_id,
                    "Course_Type__c": course_type,
                    "hed__Description__c": description,
                    "hed__Account__c": "0017h00000ZfotKAAR",
                    "Course_Duration__c": duration.__str__(),
                    "Minimum_Age__c": minimum_age.__str__(),
                    "Maximum_Age__c": maximum_age.__str__(),
                }
            )

        else:
            self.salesforce_obj.hed__Course__c.update(
                exists,
                {
                    "Name": name,
                    "Active__c": active,
                    "hed__Course_ID__c": course_id,
                    "Course_Type__c": course_type,
                    "hed__Description__c": description,
                    "hed__Account__c": "0017h00000ZfotKAAR",
                    "Course_Duration__c": duration.__str__(),
                    "Minimum_Age__c": minimum_age.__str__(),
                    "Maximum_Age__c": maximum_age.__str__(),
                },
            )

    def create_session(
        self,
        course,
        title,
        start_datetime,
        location,
        capacity,
        mentor_capacity,
        mentor,
        cost,
        ext_id,
        minimum_cost,
        maximum_cost,
        additional_info,
        assistant=None,
    ):

        exist = self.offering_query(
            ext_id=ext_id,
        )
        course_id = self.course_query(course_id=course.code)
        mentor_id = self.contact_id_query(ext_id=mentor.id)

        # Session times are stored as timeblock objects in Salesforce
        # Need to query the appropriate block to assign to session based on start and end time
        # Timezone issue may vary by user; in this case, 5 hour difference was for Eastern Daylight Savings

        end_date = (start_datetime + course.duration).strftime("%Y-%m-%d")
        start_time = (start_datetime - timedelta(hours=5)).strftime("%H:%M:%S")
        end_time = (start_datetime + course.duration - timedelta(hours=5)).strftime("%H:%M:%S")

        data = {
            "hed__Course__c": course_id,
            "Name": title,
            "hed__Start_Date__c": start_datetime.strftime("%Y-%m-%d"),
            "hed__End_Date__c": end_date,
            "Location_Name__c": location.name,
            "hed__Capacity__c": capacity,
            "Mentor_Capacity__c": mentor_capacity,
            "hed__Faculty__c": mentor_id,
            # "Assistant_Mentor__c": assistant_id,
            "hed__Term__c": "a1O7h000000pwOBEAY",
            "Cost__c": cost,
            "Minimum_Cost__c": minimum_cost,
            "Maximum_Cost__c": maximum_cost,
            "Additional_Information__c": additional_info,
            "Start_Time__c": start_time,
            "End_Time__c": end_time,
            "External_Id__c": ext_id,
        }

        if exist is None:
            self.salesforce_obj.hed__Course_Offering__c.create(
                data,
            )
        else:
            self.salesforce_obj.hed__Course_Offering__c.update(
                exist,
                data,
            )

    def create_order(
        self,
        session,
        main_contact,
        active,
        ip,
        check_in,
        ext_id,
        alternate_guardian=None,
        guardian=None,
        affiliate=None,
    ):
        guardian_id = None

        if guardian:
            guardian_id = self.contact_id_query(
                ext_id=guardian.id,
            )

        contact_id = self.contact_id_query(
            ext_id=main_contact.id,
        )

        session_id = self.offering_query(
            ext_id=session.id,
        )

        order_id = self.order_query(ext_id)

        # Date/time must be in below format for Salesforce to accept it
        temp = check_in.strftime("%Y-%m-%dT%H:%M:%SZ").__str__() if check_in else None

        if order_id is None:
            self.salesforce_obj.hed__Course_Enrollment__c.create(
                {
                    "Parent__c": guardian_id,
                    "hed__Contact__c": contact_id,
                    "hed__Course_Offering__c": session_id,
                    "IP__c": ip,
                    "Check_in__c": temp,
                    "Active__c": active,
                    "Alternate_Guardian__c": alternate_guardian,
                    "External_Id__c": ext_id,
                    "Affiliate__c": affiliate,
                }
            )
        else:
            self.salesforce_obj.hed__Course_Enrollment__c.update(
                id,
                {
                    "Parent__c": guardian_id,
                    "hed__Contact__c": contact_id,
                    "hed__Course_Offering__c": session_id,
                    "IP__c": ip,
                    "Check_in__c": temp,
                    "Active__c": active,
                    "Alternate_Guardian__c": alternate_guardian,
                    "External_Id__c": ext_id,
                    "Affiliate__c": affiliate,
                },
            )

    def add_donation(
        self,
        session,
        amount,
        first_name,
        email,
        is_verified,
        receipt_sent,
        referral_code,
        last_name="",
    ):
        session_id = self.offering_query(ext_id=session.id)

        self.salesforce_obj.Donation__c.create(
            {
                "Name": f"{first_name} {last_name}'s Donation",
                "Amount__c": amount,
                "Course_Offering__c": session_id,
                "First_Name__c": first_name,
                "Last_Name__c": last_name,
                "Email__c": email,
                "Is_Verified__c": is_verified,
                "Receipt_Sent__c": receipt_sent,
                "Referral_Code__c": referral_code,
            }
        )
