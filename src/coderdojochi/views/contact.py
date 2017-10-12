from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import render
from django.views.generic import TemplateView

from coderdojochi.forms import ContactForm


class ContactView(TemplateView):
    template_name = 'contact.html'

    def get_context_data(self, **kwargs):
        return {
            'form': ContactForm()
        }

    def post(self, request, *args, **kwargs):
        form = ContactForm(request.POST)
        human = True

        if form.is_valid():
            if request.POST['human']:
                messages.error(request, 'Bad robot.')
                human = False

            if human:
                msg = EmailMultiAlternatives(
                    subject=u'{} | CoderDojoChi Contact Form'.format(
                        request.POST['name']
                    ),
                    body=request.POST['body'],
                    from_email=u'CoderDojoChi<{}>'.format(
                        settings.DEFAULT_FROM_EMAIL
                    ),
                    reply_to=[
                        u'{}<{}>'.format(
                            request.POST['name'],
                            request.POST['email']
                        )
                    ],
                    to=[settings.CONTACT_EMAIL]
                )

                msg.attach_alternative(
                    request.POST['body'].replace(
                        "\r\n",
                        "<br />"
                    ).replace(
                        "\n",
                        "<br />"
                    ),
                    'text/html'
                )

                msg.send()

                messages.success(
                    request,
                    u'Thank you for contacting us! '
                    u'We will respond as soon as possible.'
                )

            form = ContactForm()
        else:
            messages.error(
                request,
                u'There was an error. Please try again.'
            )

        context = {
            'form': form
        }

        return render(request, self.template_name, context)
