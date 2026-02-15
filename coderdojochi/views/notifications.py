import logging
import re
from datetime import timedelta

import arrow
import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from coderdojochi.models import Session, Guardian, Mentor, MentorOrder, Order
from coderdojochi.util import email

logger = logging.getLogger(__name__)


def replace_template_variables(template_text, session_obj, guardian=None, mentor=None, students=None):
    """
    Replace template variables with actual values
    """
    # Convert session date to proper format
    class_date = arrow.get(session_obj.start_date).to("local").format("dddd, MMMM D")
    class_start_time = arrow.get(session_obj.start_date).to("local").format("h:mm a")
    class_start_time_15_min_before = arrow.get(session_obj.start_date - timedelta(minutes=15)).to("local").format("h:mm a")
    class_location = session_obj.location.name if session_obj.location else "TBD"
    
    # Replace template variables
    result = template_text
    
    # Date and time variables
    result = result.replace("<class date written as Saturday, September 12>", class_date)
    result = result.replace("<15 minutes before class start time>", class_start_time_15_min_before)
    result = result.replace("<class start time>", class_start_time)
    result = result.replace("<class location>", class_location)
    
    # Person-specific variables
    if guardian:
        result = result.replace("{parent_name}", guardian.first_name)
        
    if mentor:
        result = result.replace("{mentor_name}", mentor.first_name)
        
    if students:
        student_names = ", ".join([student.first_name for student in students])
        result = result.replace("{student_names}", student_names)
    
    return result


def send_sms(phone_number, message):
    """
    Send SMS using Dialpad API
    """
    try:
        # Check if API key is configured
        if not hasattr(settings, 'DIALPAD_API_KEY') or not settings.DIALPAD_API_KEY:
            logger.warning("Dialpad API key not configured. SMS not sent.")
            return False, "Dialpad API key not configured"
        
        # Format phone number (remove non-digits, ensure US format)
        clean_phone = re.sub(r'[^\d]', '', phone_number)
        if len(clean_phone) == 10:
            clean_phone = f"+1{clean_phone}"
        elif len(clean_phone) == 11 and clean_phone.startswith('1'):
            clean_phone = f"+{clean_phone}"
        elif not clean_phone.startswith('+'):
            clean_phone = f"+1{clean_phone}"
        
        # Dialpad API endpoint
        endpoint = getattr(settings, 'DIALPAD_SMS_ENDPOINT', 'https://dialpad.com/api/v2/sms')
        
        # API headers
        headers = {
            'Authorization': f'Bearer {settings.DIALPAD_API_KEY}',
            'Content-Type': 'application/json',
        }
        
        # API payload
        payload = {
            'to_number': clean_phone,
            'text': message,
        }
        
        # Make API request
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            logger.info(f"SMS sent successfully to {clean_phone}")
            return True, "SMS sent successfully"
        else:
            logger.error(f"Dialpad API error {response.status_code}: {response.text}")
            return False, f"API error: {response.status_code}"
            
    except requests.RequestException as e:
        logger.error(f"Network error sending SMS to {phone_number}: {str(e)}")
        return False, f"Network error: {str(e)}"
    except Exception as e:
        logger.error(f"Failed to send SMS to {phone_number}: {str(e)}")
        return False, str(e)


@staff_member_required
def course_notifications(request, session_id):
    """
    Course notification management page
    """
    session_obj = get_object_or_404(Session, pk=session_id)
    
    # Get enrolled students and their guardians
    orders = Order.objects.filter(session=session_obj, is_active=True).select_related('student', 'guardian')
    
    # Get enrolled mentors  
    mentor_orders = MentorOrder.objects.filter(session=session_obj, is_active=True).select_related('mentor')
    
    # Default email template
    default_email_template = """Subject: [We All Code] Must Read information about the in-person coding class <class date written as Saturday, September 12> at <15 minutes before class start time>

Hello {parent_name},

It's Ali from We All Code. I hope your week has been a good one.

I wanted to send you a few notes about tomorrow's class.

1. Please arrive no later than 9:45 am.
2. Class will be held in person at <class location>.
3. Create a free Replit account using the student's Google account. Watch this 50-second video on how to do it: https://youtu.be/gSP-i9iJmrk You can ignore the survey once you register. Once you've created your account, you're ready. No need to do anything else.
4. We will be moving around in this class. Please dress appropriately.
5. Safety is extremely important to us. If you are not feeling well, please stay home. We have classes every other weekend! You can attend our next one once you're feeling better.
6. This class is provided to you for free, however, we do ask for a donation if you enjoyed the class. Please donate via our website.
7. There will be multiple mental and physical breaks. We will be providing lunch (pizza).
8. Parents are more than welcome to stay, but it is not required. We do ask you to arrive 20 minutes before the end of class.

Above all, be ready to have a blast!

Thank you,

Ali Karbassi
Chief Executive Officer
We All Code"""

    # Default SMS templates
    default_sms_parent_template = "👋 Hi {parent_name}. It's Ali from We All Code. We're excited to see {student_names} in-person tomorrow (Saturday) at 9:45am. I just sent an email with more details. Can you confirm you got it and will be attending?"
    
    default_sms_mentor_template = "👋 Hi {mentor_name}. It's Ali from We All Code. We're excited to see you tomorrow (Saturday) at 9am CST. I just sent an email with more details. Can you confirm you got it? Any questions I can help with?"
    
    context = {
        'session': session_obj,
        'orders': orders,
        'mentor_orders': mentor_orders, 
        'student_count': orders.count(),
        'mentor_count': mentor_orders.count(),
        'guardian_count': orders.values('guardian').distinct().count(),
        'default_email_template': default_email_template,
        'default_sms_parent_template': default_sms_parent_template,
        'default_sms_mentor_template': default_sms_mentor_template,
    }
    
    return render(request, 'admin/course_notifications.html', context)


@staff_member_required
@require_http_methods(["POST"])
def send_email_notifications(request, session_id):
    """
    Send email notifications to parents and mentors
    """
    session_obj = get_object_or_404(Session, pk=session_id)
    
    email_template = request.POST.get('email_template', '')
    recipient_type = request.POST.get('recipient_type', 'both')  # 'parents', 'mentors', 'both'
    
    try:
        success_count = 0
        error_count = 0
        
        # Send to parents/guardians
        if recipient_type in ['parents', 'both']:
            orders = Order.objects.filter(session=session_obj, is_active=True).select_related('student', 'guardian')
            
            for order in orders:
                guardian = order.guardian
                student = order.student
                
                # Replace template variables
                personalized_email = replace_template_variables(
                    email_template, 
                    session_obj, 
                    guardian=guardian, 
                    students=[student]
                )
                
                # Extract subject and body
                lines = personalized_email.split('\n')
                subject_line = lines[0].replace('Subject: ', '') if lines[0].startswith('Subject: ') else 'Class Information'
                body = '\n'.join(lines[2:]) if len(lines) > 2 else personalized_email  # Skip subject and empty line
                
                try:
                    # Send email using existing utility
                    email(
                        subject=subject_line,
                        template_name="course_notification_email",
                        merge_global_data={
                            'email_body': body,
                            'guardian_name': guardian.first_name,
                        },
                        recipients=[guardian.email],
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to send email to {guardian.email}: {str(e)}")
                    error_count += 1
        
        # Send to mentors
        if recipient_type in ['mentors', 'both']:
            mentor_orders = MentorOrder.objects.filter(session=session_obj, is_active=True).select_related('mentor')
            
            for mentor_order in mentor_orders:
                mentor = mentor_order.mentor
                
                # Replace template variables
                personalized_email = replace_template_variables(
                    email_template, 
                    session_obj, 
                    mentor=mentor
                )
                
                # Extract subject and body
                lines = personalized_email.split('\n')
                subject_line = lines[0].replace('Subject: ', '') if lines[0].startswith('Subject: ') else 'Class Information'
                body = '\n'.join(lines[2:]) if len(lines) > 2 else personalized_email
                
                try:
                    email(
                        subject=subject_line,
                        template_name="course_notification_email",
                        merge_global_data={
                            'email_body': body,
                            'mentor_name': mentor.first_name,
                        },
                        recipients=[mentor.email],
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to send email to {mentor.email}: {str(e)}")
                    error_count += 1
        
        if success_count > 0:
            messages.success(request, f"Successfully sent {success_count} email notifications.")
        if error_count > 0:
            messages.error(request, f"Failed to send {error_count} email notifications.")
            
    except Exception as e:
        logger.error(f"Error sending email notifications: {str(e)}")
        messages.error(request, f"Error sending notifications: {str(e)}")
    
    return redirect('course_notifications', session_id=session_id)


@staff_member_required  
@require_http_methods(["POST"])
def send_sms_notifications(request, session_id):
    """
    Send SMS notifications to parents and mentors
    """
    session_obj = get_object_or_404(Session, pk=session_id)
    
    sms_template = request.POST.get('sms_template', '')
    recipient_type = request.POST.get('recipient_type', 'both')  # 'parents', 'mentors', 'both'
    
    try:
        success_count = 0
        error_count = 0
        
        # Send to parents/guardians
        if recipient_type in ['parents', 'both']:
            orders = Order.objects.filter(session=session_obj, is_active=True).select_related('student', 'guardian')
            
            for order in orders:
                guardian = order.guardian
                student = order.student
                
                if not guardian.phone:
                    continue  # Skip if no phone number
                
                # Replace template variables
                personalized_sms = replace_template_variables(
                    sms_template, 
                    session_obj, 
                    guardian=guardian, 
                    students=[student]
                )
                
                success, message = send_sms(guardian.phone, personalized_sms)
                if success:
                    success_count += 1
                else:
                    error_count += 1
        
        # Send to mentors
        if recipient_type in ['mentors', 'both']:
            mentor_orders = MentorOrder.objects.filter(session=session_obj, is_active=True).select_related('mentor')
            
            for mentor_order in mentor_orders:
                mentor = mentor_order.mentor
                
                if not hasattr(mentor, 'phone') or not mentor.phone:
                    continue  # Skip if no phone number
                
                # Replace template variables
                personalized_sms = replace_template_variables(
                    sms_template, 
                    session_obj, 
                    mentor=mentor
                )
                
                success, message = send_sms(mentor.phone, personalized_sms)
                if success:
                    success_count += 1
                else:
                    error_count += 1
        
        if success_count > 0:
            messages.success(request, f"Successfully sent {success_count} SMS notifications.")
        if error_count > 0:
            messages.error(request, f"Failed to send {error_count} SMS notifications.")
        
        # Check if Dialpad API is configured
        if not hasattr(settings, 'DIALPAD_API_KEY') or not settings.DIALPAD_API_KEY:
            messages.warning(request, "Note: Dialpad API is not configured. SMS functionality requires API setup.")
            
    except Exception as e:
        logger.error(f"Error sending SMS notifications: {str(e)}")
        messages.error(request, f"Error sending SMS notifications: {str(e)}")
    
    return redirect('course_notifications', session_id=session_id)


@staff_member_required
def preview_notifications(request, session_id):
    """
    Preview notifications before sending
    """
    session_obj = get_object_or_404(Session, pk=session_id)
    
    template_text = request.GET.get('template', '')
    notification_type = request.GET.get('type', 'email')  # 'email' or 'sms'
    recipient_type = request.GET.get('recipient', 'parents')  # 'parents' or 'mentors'
    
    # Get a sample recipient for preview
    if recipient_type == 'parents':
        order = Order.objects.filter(session=session_obj, is_active=True).select_related('student', 'guardian').first()
        if order:
            preview_text = replace_template_variables(
                template_text, 
                session_obj, 
                guardian=order.guardian, 
                students=[order.student]
            )
        else:
            preview_text = "No enrolled students found for preview."
    else:  # mentors
        mentor_order = MentorOrder.objects.filter(session=session_obj, is_active=True).select_related('mentor').first()
        if mentor_order:
            preview_text = replace_template_variables(
                template_text, 
                session_obj, 
                mentor=mentor_order.mentor
            )
        else:
            preview_text = "No enrolled mentors found for preview."
    
    return JsonResponse({
        'preview': preview_text,
        'type': notification_type,
        'recipient': recipient_type
    })