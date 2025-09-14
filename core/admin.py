# core/admin.py
import json
from decimal import Decimal
from core.utils.emailing import email_kyc_result, email_deposit_status
from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.db.models import F, Sum
from django.urls import reverse
from django.utils.html import format_html
from django.utils import timezone

try:
    from .emails import email_deposit_status
except Exception:
    email_deposit_status = None

from django.contrib.admin.helpers import ActionForm

# Email
from django.db.models import Count
from core.models import AdminMailout
from core.utils.emailing import send_templated_email
from core.utils.emailing import email_upgrade_status

# OTP
from django.core.exceptions import ValidationError
from django_otp.admin import OTPAdminSite
from django_otp.plugins.otp_totp.models import TOTPDevice

# Broadcast notification
from .models import AdminNotification

# Models
from .models import (
    CustomUser, KYC, WalletSettings,
    Vendor, P2PTrade,
    ActiveTrade,
    AccountDeposit, AccountWithdrawal, LinkedWallet,
    BankInfo,
    ExpertTrader, CopySubscription,
)

# ===============================
# Inlines
# ===============================


class EmailUsersActionForm(ActionForm):
    subject = forms.CharField(max_length=200, required=False, label="Email subject")
    body_html = forms.CharField(widget=forms.Textarea, required=False, label="Email body (HTML)")


class BankInfoInline(admin.StackedInline):
    model = BankInfo
    can_delete = False
    fk_name = 'user'
    extra = 0
    fieldsets = (
        (None, {'fields': (
            'bank_name',
            'account_name',
            'account_number',
            'routing_or_swift',
            'country',
        )}),
        ('US only', {'fields': ('us_account_type', 'us_ssn')}),
    )


class P2PTradeInline(admin.TabularInline):
    model = P2PTrade
    extra = 0
    fields = ('vendor', 'amount', 'status', 'created_at')
    readonly_fields = ('created_at',)


# ===============================
# CustomUser (single registration)
# ===============================

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    list_display = (
        'username', 'email', 'full_name',
        'current_plan', 'pending_plan', 'upgrade_progress',
        'gender', 'country', 'currency',
        'wallet_linked', 'account_balance', 'profit_today', 'bonus_amount',
        'is_staff', 'is_active',
    )
    list_filter = UserAdmin.list_filter + ('current_plan', 'pending_plan', 'country', 'currency')
    search_fields = ('username', 'email', 'full_name')
    list_editable = ('pending_plan', 'upgrade_progress')

    fieldsets = UserAdmin.fieldsets + (
        ('Wallet & Balances', {
            'fields': ('wallet_linked', 'account_balance', 'profit_today', 'bonus_amount'),
        }),
        ('Extra Profile', {
            'fields': ('full_name', 'phone_number', 'country', 'currency', 'referral_code', 'is_over_18'),
        }),
        ('Plan & Upgrade', {
            'fields': ('current_plan', 'pending_plan', 'upgrade_progress', 'upgrade_note'),
        }),
    )

    readonly_fields = ('gender',)

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Wallet & Balances', {
            'fields': ('wallet_linked', 'account_balance', 'profit_today', 'bonus_amount'),
        }),
        ('Additional Info', {
            'fields': ('full_name', 'phone_number', 'country', 'currency', 'referral_code', 'is_over_18'),
        }),
    )

    # If you defined this inline earlier in the file, keep it:
    inlines = [BankInfoInline]

    # ---------- Save logic (cleaned) ----------
    def save_model(self, request, obj, form, change):
        """
        Finalize upgrade when progress hits 100 and a pending plan exists.
        If admin clears a pending plan without changing current plan, treat as declined.
        Sends the appropriate email via email_upgrade_status.
        """
        # Snapshot previous state BEFORE saving
        prev_pending  = prev_current = None
        if change and obj.pk:
            prev = CustomUser.objects.only('current_plan', 'pending_plan', 'upgrade_progress').get(pk=obj.pk)
            prev_pending  = prev.pending_plan
            prev_current  = prev.current_plan

        # Save the edits first
        super().save_model(request, obj, form, change)

        # Decide transitions AFTER saving
        plan_choices_map = dict(getattr(CustomUser, 'PLAN_CHOICES', []))

        # APPROVE: pending exists and progress >= 100
        if obj.pending_plan and int(obj.upgrade_progress or 0) >= 100:
            final_code = obj.pending_plan
            # Apply finalization
            CustomUser.objects.filter(pk=obj.pk).update(
                current_plan=final_code,
                pending_plan=None,
                upgrade_progress=0
            )
            # Refresh and compute label
            obj.refresh_from_db(fields=['current_plan', 'pending_plan', 'upgrade_progress'])
            plan_label = plan_choices_map.get(final_code, (final_code or '').title())

            # Notify (safe guard if helper not available)
            try:
                email_upgrade_status(obj, plan_label, approved=True, request=request)
            except Exception:
                pass
            return

        # DECLINE: had a pending before, and now pending is cleared without changing current
        if change and prev_pending and obj.pending_plan is None and obj.current_plan == prev_current:
            declined_code = prev_pending
            plan_label = plan_choices_map.get(declined_code, (declined_code or '').title())
            reason = (getattr(obj, "upgrade_note", "") or "").strip()
            try:
                email_upgrade_status(obj, plan_label, approved=False, reason=reason, request=request)
            except Exception:
                pass

    # ---------- Bulk email action ----------
    actions = ["email_selected"]
    action_form = EmailUsersActionForm

    @admin.action(description="Email selected users (use subject/body below)")
    def email_selected(self, request, queryset):
        subject = request.POST.get("subject")
        body_html = request.POST.get("body_html")

        if not (subject and body_html):
            self.message_user(
                request,
                "Enter a subject & body below the actions menu, then run the action again.",
                level=messages.WARNING,
            )
            return

        sent = 0
        for u in queryset:
            if not u.email:
                continue
            try:
                # Use your utility helper (already imported at the top)
                send_templated_email(
                    to_email=u.email,
                    subject=subject,
                    template_name="broadcast.html",  # create core/templates/email/broadcast.html
                    context={"body_html": body_html, "username": u.username},
                    request=request,
                )
                sent += 1
            except Exception:
                # Best-effort fallback if helper fails
                from django.core.mail import EmailMultiAlternatives
                from django.conf import settings
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=f"Hello {u.username},\n\n(This email has an HTML version.)",
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com"),
                    to=[u.email],
                )
                msg.attach_alternative(body_html.replace("{{ username }}", u.username), "text/html")
                msg.send(fail_silently=True)
                sent += 1

        self.message_user(request, f"Sent {sent} email(s).", level=messages.SUCCESS)




# ===============================
# ActiveTrade Admin
# ===============================

@admin.register(ActiveTrade)
class ActiveTradeAdmin(admin.ModelAdmin):
    list_display  = ('user', 'asset', 'side', 'amount', 'profit', 'status', 'created_by', 'opened_at', 'closed_at')
    list_filter   = ('status', 'side', 'created_by', 'opened_at')
    search_fields = ('user__username', 'asset')
    list_editable = ('profit', 'status')

    def save_model(self, request, obj, form, change):
        """
        Balance and profit_today maintenance around open/close/amount changes.
        """
        creating = obj.pk is None
        prev_status = None
        prev_amount = None

        if not creating:
            prev = ActiveTrade.objects.only('status', 'amount').get(pk=obj.pk)
            prev_status = prev.status
            prev_amount = prev.amount

        super().save_model(request, obj, form, change)

        user_id = obj.user_id

        # CREATE PATH
        if creating:
            if not obj.created_by:
                ActiveTrade.objects.filter(pk=obj.pk).update(created_by='admin')
            if obj.status == 'open':
                CustomUser.objects.filter(pk=user_id).update(
                    account_balance=F('account_balance') - obj.amount
                )

        # EDIT PATH
        else:
            if prev_status != obj.status:
                # open -> closed
                if prev_status == 'open' and obj.status == 'closed':
                    CustomUser.objects.filter(pk=user_id).update(
                        account_balance=F('account_balance') + obj.amount + (obj.profit or Decimal('0'))
                    )
                    if not obj.closed_at:
                        ActiveTrade.objects.filter(pk=obj.pk).update(closed_at=timezone.now())

                # closed -> open
                elif prev_status == 'closed' and obj.status == 'open':
                    CustomUser.objects.filter(pk=user_id).update(
                        account_balance=F('account_balance') - obj.amount
                    )
                    if obj.closed_at:
                        ActiveTrade.objects.filter(pk=obj.pk).update(closed_at=None)

            # amount changed while open
            if prev_status == 'open' and obj.status == 'open' and prev_amount is not None and prev_amount != obj.amount:
                delta = obj.amount - prev_amount
                if delta:
                    CustomUser.objects.filter(pk=user_id).update(
                        account_balance=F('account_balance') - delta
                    )

        # Recompute profit_today from OPEN trades
        agg = ActiveTrade.objects.filter(user_id=user_id, status='open').aggregate(s=Sum('profit'))
        CustomUser.objects.filter(pk=user_id).update(profit_today=agg['s'] or Decimal('0'))


# ===============================
# OTP-enabled Admin Site (optional)
# ===============================

class OTPAdmin(OTPAdminSite):
    pass

admin_site = OTPAdmin(name='OTPAdmin')


# ===============================
# Wallet Settings (with OTP check)
# ===============================

class WalletSettingsAdminForm(forms.ModelForm):
    otp_code = forms.CharField(
        required=False,
        label="OTP Code",
        help_text="Enter the 6-digit code from your authenticator app.",
        widget=forms.TextInput(attrs={"autocomplete": "one-time-code"})
    )

    class Meta:
        model = WalletSettings
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        request = getattr(self, "_request", None)

        # Require OTP whenever anything changed (add or edit).
        if request is not None and self.has_changed():
            code = (cleaned.get("otp_code") or "").strip()
            if not code:
                raise ValidationError("OTP code is required to save changes.")

            device = (
                TOTPDevice.objects
                .filter(user=request.user, confirmed=True)
                .order_by("-id")
                .first()
            )
            if not device:
                raise ValidationError(
                    "No confirmed TOTP device found for your admin account. "
                    "Create one under ‘TOTP devices’, scan the QR, and confirm it."
                )

            # Respect throttling / rate limiting
            allowed, err = device.verify_is_allowed()
            if not allowed:
                raise ValidationError(err or "Too many OTP attempts. Please try again later.")

            # IMPORTANT: your version doesn't accept tolerance/drift kwargs.
            if not device.verify_token(code):
                raise ValidationError("Invalid OTP code.")

        return cleaned


@admin.register(WalletSettings)
class WalletSettingsAdmin(admin.ModelAdmin):
    form = WalletSettingsAdminForm
    list_display    = ["id", "btc_address", "eth_address", "usdt_address", "support_email", "updated_at"]
    search_fields   = ["btc_address", "eth_address", "usdt_address", "support_email"]
    readonly_fields = ("updated_at",)

    fieldsets = (
        ("Wallet Settings", {
            "fields": ("btc_address", "eth_address", "usdt_address", "support_email"),
        }),
        ("Security", {
            "fields": ("otp_code",),
            "description": "Enter the 6-digit OTP from your authenticator app to save any changes.",
        }),
        ("Timestamps", {
            "fields": ("updated_at",),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        """
        Inject request so the form can validate OTP against the current admin user.
        """
        Base = super().get_form(request, obj, **kwargs)

        class BoundForm(Base):
            def __init__(self, *args, **kw):
                super().__init__(*args, **kw)
                self._request = request  # used in clean()

        return BoundForm


# ===============================
# Vendor / KYC / Wallet / Deposits / Withdrawals
# ===============================

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['name', 'verified', 'location', 'name', 'status', 'change_status']
    list_filter  = ['verified', 'location', 'status']
    search_fields = ['name']

    def change_status(self, obj):
        return f"<a href='/admin/core/vendor/{obj.id}/change/'>Edit</a>"
    change_status.allow_tags = True


@admin.register(KYC)
class KYCAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'full_name', 'document_type', 'document_number',
        'verified', 'created_at', 'front_preview', 'back_preview', 'selfie_preview'
    )
    list_filter = ('verified', 'document_type', 'created_at')
    search_fields = ('user__username', 'user__email', 'full_name', 'document_number')
    actions = ['mark_verified', 'mark_unverified']

    @admin.display(description='Front')
    def front_preview(self, obj):
        f = getattr(obj, 'id_front', None)
        if f and getattr(f, 'url', None):
            return format_html('<a href="{0}" target="_blank"><img src="{0}" style="height:40px;border-radius:6px;object-fit:cover"/></a>', f.url)
        return '—'

    @admin.display(description='Back')
    def back_preview(self, obj):
        f = getattr(obj, 'id_back', None)
        if f and getattr(f, 'url', None):
            return format_html('<a href="{0}" target="_blank"><img src="{0}" style="height:40px;border-radius:6px;object-fit:cover"/></a>', f.url)
        return '—'

    @admin.display(description='Selfie')
    def selfie_preview(self, obj):
        selfie = getattr(obj, 'selfie', None)
        if selfie and getattr(selfie, 'url', None):
            return format_html('<img src="{}" style="height:40px;width:40px;border-radius:6px;object-fit:cover;" />', selfie.url)
        return '—'

    @admin.action(description="Mark selected as VERIFIED")
    def mark_verified(self, request, queryset):
        updated = queryset.update(verified=True)
        self.message_user(request, f"{updated} KYC record(s) marked VERIFIED.", level=messages.SUCCESS)

    @admin.action(description="Mark selected as UNVERIFIED")
    def mark_unverified(self, request, queryset):
        updated = queryset.update(verified=False)
        self.message_user(request, f"{updated} KYC record(s) marked UNVERIFIED.", level=messages.WARNING)


@admin.register(LinkedWallet)
class LinkedWalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'provider', 'display_wallet_phrase', 'active', 'linked_at')
    search_fields = ('user__username', 'provider')
    list_filter = ('active', 'linked_at')


@admin.register(AccountDeposit)
class AccountDepositAdmin(admin.ModelAdmin):
    list_display  = ('user', 'amount', 'status', 'created_at', 'decided_at', 'proof_link')
    list_filter   = ('status', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'decided_at', 'proof_link_readonly', 'proof_preview', 'note_pretty')

    fieldsets = (
        ('Deposit', {
            'fields': (
                'user', 'amount', 'status',
                'proof_link_readonly',
                'proof_preview',
                'note_pretty',
            ),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'decided_at'),
        }),
    )

    # helpers
    def _note_dict(self, obj):
        try:
            return json.loads(obj.note or "{}")
        except Exception:
            return {}

    def _proof_url(self, obj):
        data = self._note_dict(obj)
        f = str(data.get('file') or '').strip()
        if not f:
            return None
        if f.startswith('http://') or f.startswith('https://'):
            return f
        return settings.MEDIA_URL.rstrip('/') + '/' + f.lstrip('/')

    # list column
    @admin.display(description="Payment proof")
    def proof_link(self, obj):
        url = self._proof_url(obj)
        return format_html('<a href="{}" target="_blank">View proof</a>', url) if url else '—'

    # detail read-onlys
    @admin.display(description="Payment proof")
    def proof_link_readonly(self, obj):
        return self.proof_link(obj)

    @admin.display(description="Preview")
    def proof_preview(self, obj):
        url = self._proof_url(obj)
        if not url:
            return '—'
        return format_html(
            '<a href="{0}" target="_blank"><img src="{0}" style="max-height:120px; border-radius:6px;" /></a>',
            url
        )

    @admin.display(description='Raw note (JSON)')
    def note_pretty(self, obj):
        data = self._note_dict(obj)
        return format_html(
            '<pre style="white-space:pre-wrap; font-size:12px; margin:0;">{}</pre>',
            json.dumps(data, indent=2, ensure_ascii=False)
        )

    def save_model(self, request, obj, form, change):
        prev_status = None
        if change and obj.pk:
            prev = AccountDeposit.objects.filter(pk=obj.pk).only('status').first()
            prev_status = prev.status if prev else None

        super().save_model(request, obj, form, change)

        # If status changed, stamp decided_at and send email
        if prev_status and prev_status != obj.status:
            if obj.status in ('approved', 'rejected') and not obj.decided_at:
                obj.decided_at = timezone.now()
                obj.save(update_fields=['decided_at'])

            if email_deposit_status:
                try:
                    email_deposit_status(
                        obj.user,
                        obj.amount,
                        approved=(obj.status == 'approved'),
                        request=request
                    )
                except Exception:
                    # Don’t block admin save on email issues
                    pass


        

@admin.register(AccountWithdrawal)
class AccountWithdrawalAdmin(admin.ModelAdmin):
    list_display  = (
        'user', 'amount', 'status', 'created_at', 'decided_at',
        'method_display', 'us_account_type_display', 'us_ssn_display',
    )
    list_filter   = ('status', 'created_at')
    search_fields = ('user__username', 'user__email', 'note')

    # ✅ Only show parsed details in admin
    readonly_fields = ('created_at', 'decided_at', 'parsed_details')
    fields = ('user', 'amount', 'status', 'parsed_details', 'created_at', 'decided_at')

    @admin.display(description="Withdrawal details")
    def parsed_details(self, obj):
        return obj.parsed_details()

    # helpers
    def _parse_note(self, wd):
        try:
            return json.loads(wd.note) if wd.note else {}
        except Exception:
            return {}

    def _set_note(self, wd, data: dict):
        wd.note = json.dumps(data)

    @admin.display(description='Method')
    def method_display(self, obj):
        n = self._parse_note(obj)
        return (n.get('method') or '').upper() or '—'

    @admin.display(description='US Account Type')
    def us_account_type_display(self, obj):
        n    = self._parse_note(obj)
        meta = n.get('meta') or {}
        bank = meta.get('bank') or {}
        return (n.get('us_account_type')
                or meta.get('us_account_type')
                or bank.get('us_account_type')
                or '—')

    @admin.display(description='US SSN')
    def us_ssn_display(self, obj):
        n    = self._parse_note(obj)
        meta = n.get('meta') or {}
        bank = meta.get('bank') or {}
        return (n.get('us_ssn')
                or meta.get('us_ssn')
                or bank.get('us_ssn')
                or '—')

    # status transitions
    def save_model(self, request, obj, form, change):
        prev_status = None
        if obj.pk:
            prev_status = AccountWithdrawal.objects.only('status').get(pk=obj.pk).status

        super().save_model(request, obj, form, change)

        if prev_status and prev_status != obj.status:
            note = self._parse_note(obj)
            hold = bool(note.get('hold'))

            if prev_status == 'pending' and obj.status == 'approved':
                if not hold:
                    CustomUser.objects.filter(pk=obj.user_id).update(
                        account_balance=F('account_balance') - obj.amount
                    )
                obj.decided_at = timezone.now()
                self._set_note(obj, {**note, 'hold': False})
                obj.save(update_fields=['decided_at', 'note'])

            elif prev_status == 'pending' and obj.status == 'rejected':
                if hold:
                    CustomUser.objects.filter(pk=obj.user_id).update(
                        account_balance=F('account_balance') + obj.amount
                    )
                obj.decided_at = timezone.now()
                self._set_note(obj, {**note, 'hold': False, 'refunded': bool(hold)})
                obj.save(update_fields=['decided_at', 'note'])

    # bulk actions
    @admin.action(description="Approve selected (finalize)")
    def approve_selected(self, request, queryset):
        approved = 0
        for wd in queryset.select_for_update():
            if wd.status != 'pending':
                continue
            note = self._parse_note(wd)
            hold = bool(note.get('hold'))
            if not hold:
                CustomUser.objects.filter(pk=wd.user_id).update(
                    account_balance=F('account_balance') - wd.amount
                )
            wd.status = 'approved'
            wd.decided_at = timezone.now()
            self._set_note(wd, {**note, 'hold': False})
            wd.save(update_fields=['status', 'decided_at', 'note'])
            approved += 1
        self.message_user(request, f"Approved {approved} withdrawal(s).", level=messages.SUCCESS)

    @admin.action(description="Reject selected (refund if held)")
    def reject_selected(self, request, queryset):
        rejected = 0
        for wd in queryset.select_for_update():
            if wd.status != 'pending':
                continue
            note = self._parse_note(wd)
            hold = bool(note.get('hold'))
            if hold:
                CustomUser.objects.filter(pk=wd.user_id).update(
                    account_balance=F('account_balance') + wd.amount
                )
            wd.status = 'rejected'
            wd.decided_at = timezone.now()
            self._set_note(wd, {**note, 'hold': False, 'refunded': bool(hold)})
            wd.save(update_fields=['status', 'decided_at', 'note'])
            rejected += 1
        self.message_user(
            request,
            f"Rejected {rejected} withdrawal(s). Refunded held funds when applicable.",
            level=messages.WARNING
        )

    actions = ['approve_selected', 'reject_selected']


# Broadcast Notifoication

@admin.register(AdminNotification)
class AdminNotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("user__username", "user__email", "title", "message")


# ===============================
# P2PTrade, ExpertTrader, CopySubscription
# ===============================

@admin.register(P2PTrade)
class P2PTradeAdmin(admin.ModelAdmin):
    list_display = ['user', 'vendor', 'amount', 'status', 'created_at', 'open_chat', 'proof_link']
    list_filter  = ['status', 'created_at']
    search_fields = ['user__username', 'vendor__name']

    def open_chat(self, obj):
        url = reverse('staff_trade_chat', args=[obj.id])
        return format_html('<a class="button" href="{}" target="_blank">Open chat</a>', url)
    open_chat.short_description = 'Chat'

    def proof_link(self, obj):
        if obj.payment_proof:
            return format_html('<a href="{}" target="_blank">View Proof</a>', obj.payment_proof.url)
        return "—"
    proof_link.short_description = "Payment Proof"


@admin.register(ExpertTrader)
class ExpertTraderAdmin(admin.ModelAdmin):
    list_display  = ('name', 'wins', 'losses', 'win_rate', 'profit_share', 'is_active', 'avatar_thumb')
    list_filter   = ('is_active',)
    search_fields = ('name', 'bio')

    def avatar_thumb(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" style="height:40px;width:40px;border-radius:50%;object-fit:cover" />', obj.avatar.url)
        return '—'
    avatar_thumb.short_description = 'Avatar'


@admin.register(CopySubscription)
class CopySubscriptionAdmin(admin.ModelAdmin):
    list_display  = ('user', 'expert', 'status', 'active', 'started_at', 'ended_at')
    list_filter   = ('status', 'active', 'started_at')
    search_fields = ('user__username', 'expert__name')


@admin.register(AdminMailout)
class AdminMailoutAdmin(admin.ModelAdmin):
    list_display = ("subject", "segment", "is_sent", "sent_count", "created_at", "sent_at")
    list_filter = ("segment", "is_sent", "created_at")
    search_fields = ("subject", "body_html")
    filter_horizontal = ("recipients",)
    readonly_fields = ("sent_at", "sent_count", "is_sent")

    actions = ["send_now"]

    @admin.action(description="Send selected mailouts now")
    def send_now(self, request, queryset):
        sent_total = 0
        for mail in queryset:
            if mail.is_sent:
                continue

            # Build recipient set by segment
            if mail.segment == "ALL":
                qs = CustomUser.objects.filter(is_active=True).only("email", "username")
            elif mail.segment == "NO_DEPOSIT":
                qs = CustomUser.objects.annotate(dep_count=Count("deposits")).filter(is_active=True, dep_count=0)
            else:  # SPECIFIC
                qs = mail.recipients.filter(is_active=True)

            count = 0
            for u in qs:
                if not u.email:
                    continue
                send_templated_email(
                    to_email=u.email,
                    subject=mail.subject,
                    template_name="broadcast.html",
                    context={"body_html": mail.body_html, "username": u.username},
                    request=request,
                )
                count += 1

            mail.sent_count = count
            mail.is_sent = True
            mail.sent_at = timezone.now()
            mail.save(update_fields=["sent_count", "is_sent", "sent_at"])
            sent_total += count

        self.message_user(request, f"Sent {sent_total} emails.", level=messages.SUCCESS)