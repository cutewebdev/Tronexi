# core/emails.py

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings

def email_deposit_status(user, amount, approved, request=None):
    subject = "Deposit Approved" if approved else "Deposit Rejected"
    msg = (
        f"Hello {user.username},\n\n"
        f"Your deposit of {amount} has been "
        f"{'approved' if approved else 'rejected'}.\n\n"
        "Thank you."
    )
    send_mail(
        subject,
        msg,
        getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com"),
        [user.email],
        fail_silently=True,
    )


def send_templated_email(to_email, subject, template_name, context, request=None):
    # optional brand bits
    context = dict({
        "site_name": getattr(settings, "SITE_NAME", "Tronexi"),
        "site_logo_url": getattr(settings, "SITE_LOGO_URL", ""),  # set in settings if you want
    }, **(context or {}))

    html = render_to_string(f"email/{template_name}", context)
    text = "This message is best viewed in HTML."

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com"),
        to=[to_email],
    )
    msg.attach_alternative(html, "text/html")
    msg.send(fail_silently=True)