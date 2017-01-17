# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-08-23 18:19
from __future__ import unicode_literals

from django.db import migrations


def create_waitlist_orders_from_old_waitlists(apps, schema_editor):
    Session = apps.get_model('coderdojochi', 'Session')
    Order = apps.get_model('coderdojochi', 'Order')
    MentorOrder = apps.get_model('coderdojochi', 'MentorOrder')

    for session in Session.objects.all():
        for student in session.waitlist_students.all():
            order, created = Order.objects.get_or_create(
                guardian=student.guardian,
                student=student,
                session=session
            )
            order.waitlisted = True
            order.waitlist_offer_sent_at = None
            order.waitlisted_at = session.start_date
            order.active = True
            order.save()

        for mentor in session.waitlist_mentors.all():
            mentor_order, created = MentorOrder.objects.get_or_create(
                mentor=mentor,
                session=session
            )
            mentor_order.waitlisted = True
            mentor_order.waitlist_offer_sent_at = None
            mentor_order.waitlisted_at = session.start_date
            mentor_order.active = True
            mentor_order.save()


class Migration(migrations.Migration):
    dependencies = [
        ('coderdojochi', '0011_waitlist_updates'),
    ]

    operations = [
        migrations.RunPython(create_waitlist_orders_from_old_waitlists),
        migrations.RemoveField(
            model_name='session',
            name='waitlist_mentors',
        ),
        migrations.RemoveField(
            model_name='session',
            name='waitlist_students',
        )
    ]
