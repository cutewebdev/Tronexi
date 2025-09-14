# core/utils/emailing.py
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.templatetags.static import static

def _abs_logo(request=None):
    """
    Returns an absolute URL to the brand logo so it renders in email clients.
    Prefers request.build_absolute_uri; falls back to SITE_URL.
    """
    rel = static(getattr(settings, "BRAND_LOGO_STATIC_PATH", "image/logo-horizontal.png"))
    if request:
        return request.build_absolute_uri(rel)
    base = getattr(settings, "SITE_URL", "")
    if base and rel.startswith("/"):
        return base.rstrip("/") + rel
    return rel  # if already absolute

def send_templated_email(to_email, subject, template_name, context, request=None):
    """
    Renders HTML email from template and sends it.
    Templates live in core/templates/email/*.html
    """
    ctx = {
        "site_name": getattr(settings, "SITE_NAME", "Tronexi"),
        "site_url": getattr(settings, "SITE_URL", ""),
        "brand_logo": _abs_logo(request),
    }
    ctx.update(context or {})

    html = render_to_string(f"email/{template_name}", ctx)
    text = strip_tags(html)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com"),
        to=[to_email],
    )
    msg.attach_alternative(html, "text/html")
    msg.send()

# Convenience wrappers
def email_kyc_result(user, approved, request=None):
    tmpl = "kyc_approved.html" if approved else "kyc_declined.html"
    subject = f"{getattr(settings,'SITE_NAME','Tronexi')} — KYC {'Approved' if approved else 'Declined'}"
    send_templated_email(
        user.email, subject, tmpl,
        {"username": user.username},
        request=request,
    )

def email_deposit_status(user, amount, approved, request=None):
    tmpl = "deposit_approved.html" if approved else "deposit_declined.html"
    subject = f"{getattr(settings,'SITE_NAME','Tronexi')} — Deposit {'Approved' if approved else 'Declined'}"
    send_templated_email(
        user.email, subject, tmpl,
        {"username": user.username, "amount": amount},
        request=request,
    )

def email_upgrade_status(user, plan_label, approved, reason=None, request=None):
    """
    plan_label: human readable, e.g. 'Starter', 'Gold'
    approved:   True/False
    reason:     optional plain text shown on decline email
    """
    tmpl = "upgrade_approved.html" if approved else "upgrade_declined.html"
    subject = f"{getattr(settings,'SITE_NAME','Tronexi')} — Account Upgrade {'Approved' if approved else 'Declined'}"
    ctx = {
        "username": user.username,
        "plan_label": plan_label,
        "reason": reason or "",
    }
    send_templated_email(user.email, subject, tmpl, ctx, request=request)