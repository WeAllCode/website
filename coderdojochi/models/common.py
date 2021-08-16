import json
from datetime import date, datetime, timedelta
from logging import Formatter
from re import S

from django.conf import settings
from django.db import models

from pytz import timezone
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
            domain=settings.SALESFORCE_DOMAIN,
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

    def course_query(self, course_id):
        query = "SELECT Id FROM hed__Course__c WHERE hed__Course_ID__c = {}"
        formatted = format_soql(query, course_id)
        results = self.salesforce_obj.query(formatted)

        exists = results["totalSize"]

        if exists:
            return results["records"][0]["Id"]

        return None

    def general_query(self, ext_id, object):
        query = (
            f"SELECT Id FROM {object} WHERE " + "External_Id__c = '{}'"
            if isinstance(ext_id, int)
            else f"SELECT Id FROM {object} WHERE " + "External_Id__c = {}"
        )
        formatted_query = format_soql(query, ext_id)
        print(formatted_query)

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
        parent = parent_result["records"][0]["Id"] if parent_result["totalSize"] > 0 else None

        child_query = format_soql(
            "SELECT Id FROM Contact WHERE FirstName = {} AND LastName = {}",
            child_first_name,
            child_last_name,
        )
        child_result = self.salesforce_obj.query(child_query)
        child = child_result["records"][0]["Id"] if child_result["totalSize"] > 0 else None

        relationship_query = format_soql(
            "SELECT Id FROM hed__Relationship__c WHERE hed__Contact__c = {} AND hed__RelatedContact__c = {}",
            parent,
            child,
        )
        relationship_results = self.salesforce_obj.query(relationship_query)
        exist = relationship_results["totalSize"]

        if not exist and parent and child:
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
        exists = self.general_query(ext_id=ext_id, object="Contact")

        household_name = f"{last_name} Household"
        account_created = self.in_account_list(household_name)

        parent_id = (
            self.general_query(ext_id=parent.id, object="Contact")
            if (parent is not None and parent != ext_id)
            else None
        )

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
            "Medical_Conditions__c": medical,
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
                    "hed__Account__c": "0012f00000ffAGVAA2",  # hardcoded
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
                    "hed__Account__c": "0012f00000ffAGVAA2",  # hardcoded
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
        ext_id,
        online_link,
        video_meeting_id,
        meeting_password,
        cost,
        minimum_cost,
        maximum_cost,
        additional_info,
        assistant=None,
    ):

        exist = self.general_query(ext_id=ext_id, object="hed__Course_Offering__c")
        course_id = self.course_query(course_id=course.code)
        mentor_id = self.general_query(
            ext_id=mentor.id,
            object="Contact",
        )

        # Session times are stored as timeblock objects in Salesforce
        # Need to query the appropriate block to assign to session based on start and end time
        # Timezone issue may vary by user; in this case, 5 hour difference was for Eastern Daylight Savings

        end_date = (start_datetime + course.duration).strftime("%Y-%m-%d")
        start_time = (start_datetime - timedelta(hours=5)).strftime("%H:%M:%S")
        end_time = (start_datetime + course.duration - timedelta(hours=5)).strftime("%H:%M:%S")

        minimum_cost_converted = int(minimum_cost) if minimum_cost else None
        maximum_cost_converted = int(maximum_cost) if maximum_cost else None
        cost_converted = int(cost) if cost else None

        data = {
            "hed__Course__c": course_id,
            "Name": title,
            "hed__Start_Date__c": start_datetime.strftime("%Y-%m-%d"),
            "hed__End_Date__c": end_date,
            "Location_Name__c": location.name,
            "hed__Capacity__c": capacity,
            "Mentor_Capacity__c": mentor_capacity,
            "hed__Faculty__c": mentor_id,
            "hed__Term__c": "a1P2f0000003vaEEAQ",  # hardcoded
            "Cost__c": cost_converted,
            "Minimum_Cost__c": minimum_cost_converted,
            "Maximum_Cost__c": maximum_cost_converted,
            "Additional_Information__c": additional_info,
            "Online_Video_Link__c": online_link,
            "Online_Video_Meeting_Id__c": video_meeting_id,
            "Password__c": meeting_password,
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
        is_mentor=False,
    ):
        guardian_id = None

        if guardian:
            guardian_id = self.general_query(
                ext_id=guardian.id,
                object="Contact",
            )

        contact_id = self.general_query(
            ext_id=main_contact.id,
            object="Contact",
        )

        session_id = self.general_query(
            ext_id=session.id,
            object="hed__Course_Offering__c",
        )

        order_id = self.general_query(
            ext_id=ext_id,
            object="hed__Course_Enrollment__c",
        )

        print(order_id)
        print(ext_id)

        # Date/time must be in below format for Salesforce to accept it
        converted = (check_in - timedelta(hours=5)) if check_in else None
        temp = converted.strftime("%Y-%m-%dT%H:%M:%SZ").__str__() if check_in else None

        data = {
            "Parent__c": guardian_id,
            "hed__Contact__c": contact_id,
            "hed__Course_Offering__c": session_id,
            "IP__c": ip,
            "Check_in__c": temp,
            "Active__c": active,
            "Alternate_Guardian__c": alternate_guardian,
            "External_Id__c": ext_id,
            "Affiliate__c": affiliate,
            "Is_Mentor__c": is_mentor,
        }

        # print(ext_id)
        # print(self.salesforce_obj.hed__Course_Enrollment__c.get('a192f000000i2Gx'))

        if order_id is None:
            self.salesforce_obj.hed__Course_Enrollment__c.create(
                data,
            )
        else:
            self.salesforce_obj.hed__Course_Enrollment__c.update(
                order_id,
                data,
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
        ext_id,
        last_name="",
    ):
        session_id = (
            self.general_query(
                ext_id=session.id,
                object="hed__Course_Offering__c",
            )
            if session
            else None
        )
        donation_id = self.general_query(
            ext_id=ext_id,
            object="Donation__c",
        )

        data = {
            "Name": f"{first_name} {last_name}'s Donation",
            "Amount__c": amount,
            "Course_Offering__c": session_id,
            "First_Name__c": first_name,
            "Last_Name__c": last_name,
            "Email__c": email,
            "Is_Verified__c": is_verified,
            "Receipt_Sent__c": receipt_sent,
            "Referral_Code__c": referral_code,
            "External_Id__c": ext_id,
        }

        if not donation_id:
            self.salesforce_obj.Donation__c.create(
                data,
            )
        else:
            self.salesforce_obj.Donation__c.update(
                donation_id,
                data,
            )

    def add_email_content(
        self,
        nickname,
        subject,
        body,
        is_active,
    ):

        self.salesforce_obj.Email_Content__c.create(
            {
                "Nickname__c": nickname,
                "Subject__c": subject,
                "Body__c": body,
                "Active__c": is_active,
            }
        )

    def add_equipment_type(self, name, ext_id):

        type_id = self.general_query(
            ext_id=ext_id,
            object="Equipment_Type__c",
        )

        if not type_id:
            self.salesforce_obj.Equipment_Type__c.create(
                {
                    "Name": name,
                    "External_Id__c": ext_id,
                }
            )
        else:
            self.salesforce_obj.Equipment_Type__c.update(
                type_id,
                {
                    "Name": name,
                    "External_Id__c": ext_id,
                },
            )

    def add_equipment(
        self,
        uuid,
        equipment_type,
        make,
        model,
        asset_tag,
        acquisition_date,
        condition,
        notes,
        last_system_update_check_in,
        last_system_update,
        force_update_on_next_boot,
        ext_id,
    ):

        equipment_type_id = self.general_query(
            ext_id=equipment_type.id,
            object="Equipment_Type__c",
        )
        formatted_time = acquisition_date.strftime("%Y-%m-%dT%H:%M:%SZ").__str__() if acquisition_date else None
        equipment_id = self.general_query(ext_id=ext_id, object="Equipment__c")

        data = {
            "uuid__c": uuid,
            "Type__c": equipment_type_id,
            "Make__c": make,
            "Model__c": model,
            "Asset_Tag__c": asset_tag,
            "Acquisition_Date__c": formatted_time,
            "Condition__c": condition,
            "Notes__c": notes,
            "Last_System_Update__c": last_system_update,
            "Last_System_Update_Checkin__c": last_system_update_check_in,
            "Force_Update_On_Next_Boot__c": force_update_on_next_boot,
            "External_Id__c": ext_id,
        }

        if not equipment_id:
            self.salesforce_obj.Equipment__c.create(
                data,
            )
        else:
            self.salesforce_obj.Equipment__c.update(
                equipment_id,
                data,
            )

    def add_location(
        self,
        name,
        address,
        city,
        state,
        zip,
        is_active,
        ext_id,
    ):

        location_id = self.general_query(ext_id=ext_id, object="CLocation__c")

        if not location_id:

            self.salesforce_obj.CLocation__c.create(
                {
                    "Active__c": is_active,
                    "Address__c": address,
                    "City__c": city,
                    "External_Id__c": ext_id,
                    "Name__c": name,
                    "State__c": state,
                    "Zip__c": zip,
                }
            )

        else:
            self.salesforce_obj.CLocation__c.update(
                location_id,
                {
                    "Active__c": is_active,
                    "Address__c": address,
                    "City__c": city,
                    "External_Id__c": ext_id,
                    "Name__c": name,
                    "State__c": state,
                    "Zip__c": zip,
                },
            )

    def add_meeting_type(
        self,
        code,
        title,
        slug,
        description,
        ext_id,
    ):
        type_id = self.meeting_type_query(ext_id=ext_id, object="Meeting_Type__c")

        if not type_id:
            self.salesforce_obj.Meeting_Type__c.create(
                {
                    "Code__c": code,
                    "Description__c": description,
                    "Title__c": title,
                    "Slug__c": slug,
                    "External_Id__c": ext_id,
                }
            )
        else:
            self.salesforce_obj.Meeting_Type__c.update(
                type_id,
                {
                    "Code__c": code,
                    "Description__c": description,
                    "Title__c": title,
                    "Slug__c": slug,
                    "External_Id__c": ext_id,
                },
            )

    def add_meeting(
        self,
        meeting_type,
        additional_info,
        start_date,
        end_date,
        location,
        external_enrollment_url,
        is_public,
        is_active,
        ext_id,
        announced_date,
    ):

        meeting_type_id = self.general_query(ext_id=meeting_type.id, object="Meeting_Type__c")
        location_id = self.general_query(
            ext_id=location.id,
            object="CLocation__c",
        )
        meeting_id = self.general_query(ext_id=ext_id, object="Meeting__c")

        formatted_start = start_date.strftime("%Y-%m-%dT%H:%M:%SZ").__str__() if start_date else None
        formatted_end = end_date.strftime("%Y-%m-%dT%H:%M:%SZ").__str__() if end_date else None
        formatted_announced = announced_date.strftime("%Y-%m-%dT%H:%M:%SZ").__str__() if announced_date else None

        data = {
            "Location__c": location_id,
            "Meeting_Type__c": meeting_type_id,
            "Additional_Information__c": additional_info,
            "Start_Date__c": formatted_start,
            "End_Date__c": formatted_end,
            "External_Enrollment_URL__c": external_enrollment_url,
            "Is_Public__c": is_public,
            "Is_Active__c": is_active,
            "Announced_Date__c": formatted_announced,
        }

        if not meeting_id:
            self.salesforce_obj.Meeting__c.create(
                data,
            )
        else:
            self.salesforce_obj.Meeting__c.update(
                meeting_id,
                data,
            )
