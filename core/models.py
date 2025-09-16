import json
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from .choices import COUNTRY_CHOICES
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils.html import format_html


CURRENCY_CHOICES = [
    ('GBP', 'British Pound'),
    ('USD', 'US Dollar'),
    ('EUR', 'Euro'),
    ('AUD', 'Australian Dollar'),
    ('CAD', 'Canadian Dollar'),
    ('THB', 'Thai baht'),
    ('HKD', 'Hong Kong Dollar'),
]

GENDER_CHOICES = [
    ('M', 'Male'),
    ('F', 'Female'),
]

COUNTRY_CHOICES = [
    # 🔝 Major Countries (Prioritized)
    ('US', 'United States'),
    ('GB', 'United Kingdom'),
    ('CA', 'Canada'),
    ('CN', 'China'),
    ('DE', 'Germany'),
    ('FR', 'France'),
    ('IT', 'Italy'),
    ('AU', 'Australia'),
    ('IN', 'India'),
    ('BR', 'Brazil'),
    ('TH', 'Thailand'),
    ('ZA', 'South Africa'),
    ('RU', 'Russia'),
    ('JP', 'Japan'),
    ('KR', 'South Korea'),
    ('VN', 'Vietnam'),
    ('AE', 'United Arab Emirates'),

    # 🌍 All Countries (Alphabetical)
    ('AF', 'Afghanistan'),
    ('AL', 'Albania'),
    ('DZ', 'Algeria'),
    ('AS', 'American Samoa'),
    ('AD', 'Andorra'),
    ('AO', 'Angola'),
    ('AI', 'Anguilla'),
    ('AQ', 'Antarctica'),
    ('AG', 'Antigua and Barbuda'),
    ('AR', 'Argentina'),
    ('AM', 'Armenia'),
    ('AW', 'Aruba'),
    ('AT', 'Austria'),
    ('AZ', 'Azerbaijan'),
    ('BS', 'Bahamas'),
    ('BH', 'Bahrain'),
    ('BD', 'Bangladesh'),
    ('BB', 'Barbados'),
    ('BY', 'Belarus'),
    ('BE', 'Belgium'),
    ('BZ', 'Belize'),
    ('BJ', 'Benin'),
    ('BM', 'Bermuda'),
    ('BT', 'Bhutan'),
    ('BO', 'Bolivia'),
    ('BA', 'Bosnia and Herzegovina'),
    ('BW', 'Botswana'),
    ('IO', 'British Indian Ocean Territory'),
    ('BN', 'Brunei'),
    ('BG', 'Bulgaria'),
    ('BF', 'Burkina Faso'),
    ('BI', 'Burundi'),
    ('KH', 'Cambodia'),
    ('CM', 'Cameroon'),
    ('CV', 'Cape Verde'),
    ('KY', 'Cayman Islands'),
    ('CF', 'Central African Republic'),
    ('TD', 'Chad'),
    ('CL', 'Chile'),
    ('CO', 'Colombia'),
    ('KM', 'Comoros'),
    ('CG', 'Congo - Brazzaville'),
    ('CD', 'Congo - Kinshasa'),
    ('CK', 'Cook Islands'),
    ('CR', 'Costa Rica'),
    ('CI', 'Côte d’Ivoire'),
    ('HR', 'Croatia'),
    ('CU', 'Cuba'),
    ('CY', 'Cyprus'),
    ('CZ', 'Czech Republic'),
    ('DK', 'Denmark'),
    ('DJ', 'Djibouti'),
    ('DM', 'Dominica'),
    ('DO', 'Dominican Republic'),
    ('EC', 'Ecuador'),
    ('EG', 'Egypt'),
    ('SV', 'El Salvador'),
    ('GQ', 'Equatorial Guinea'),
    ('ER', 'Eritrea'),
    ('EE', 'Estonia'),
    ('ET', 'Ethiopia'),
    ('FJ', 'Fiji'),
    ('FI', 'Finland'),
    ('GF', 'French Guiana'),
    ('PF', 'French Polynesia'),
    ('GA', 'Gabon'),
    ('GM', 'Gambia'),
    ('GE', 'Georgia'),
    ('GH', 'Ghana'),
    ('GI', 'Gibraltar'),
    ('GR', 'Greece'),
    ('GL', 'Greenland'),
    ('GD', 'Grenada'),
    ('GP', 'Guadeloupe'),
    ('GU', 'Guam'),
    ('GT', 'Guatemala'),
    ('GN', 'Guinea'),
    ('GW', 'Guinea-Bissau'),
    ('GY', 'Guyana'),
    ('HT', 'Haiti'),
    ('HN', 'Honduras'),
    ('HK', 'Hong Kong SAR China'),
    ('HU', 'Hungary'),
    ('IS', 'Iceland'),
    ('ID', 'Indonesia'),
    ('IR', 'Iran'),
    ('IQ', 'Iraq'),
    ('IE', 'Ireland'),
    ('IL', 'Israel'),
    ('JM', 'Jamaica'),
    ('JO', 'Jordan'),
    ('KZ', 'Kazakhstan'),
    ('KE', 'Kenya'),
    ('KI', 'Kiribati'),
    ('KW', 'Kuwait'),
    ('KG', 'Kyrgyzstan'),
    ('LA', 'Laos'),
    ('LV', 'Latvia'),
    ('LB', 'Lebanon'),
    ('LS', 'Lesotho'),
    ('LR', 'Liberia'),
    ('LY', 'Libya'),
    ('LI', 'Liechtenstein'),
    ('LT', 'Lithuania'),
    ('LU', 'Luxembourg'),
    ('MO', 'Macau SAR China'),
    ('MK', 'North Macedonia'),
    ('MG', 'Madagascar'),
    ('MW', 'Malawi'),
    ('MY', 'Malaysia'),
    ('MV', 'Maldives'),
    ('ML', 'Mali'),
    ('MT', 'Malta'),
    ('MH', 'Marshall Islands'),
    ('MQ', 'Martinique'),
    ('MR', 'Mauritania'),
    ('MU', 'Mauritius'),
    ('YT', 'Mayotte'),
    ('MX', 'Mexico'),
    ('FM', 'Micronesia'),
    ('MD', 'Moldova'),
    ('MC', 'Monaco'),
    ('MN', 'Mongolia'),
    ('ME', 'Montenegro'),
    ('MS', 'Montserrat'),
    ('MA', 'Morocco'),
    ('MZ', 'Mozambique'),
    ('MM', 'Myanmar (Burma)'),
    ('NA', 'Namibia'),
    ('NR', 'Nauru'),
    ('NP', 'Nepal'),
    ('NL', 'Netherlands'),
    ('NC', 'New Caledonia'),
    ('NZ', 'New Zealand'),
    ('NI', 'Nicaragua'),
    ('NE', 'Niger'),
    ('NG', 'Nigeria'),
    ('NU', 'Niue'),
    ('NF', 'Norfolk Island'),
    ('KP', 'North Korea'),
    ('NO', 'Norway'),
    ('OM', 'Oman'),
    ('PK', 'Pakistan'),
    ('PW', 'Palau'),
    ('PS', 'Palestinian Territories'),
    ('PA', 'Panama'),
    ('PG', 'Papua New Guinea'),
    ('PY', 'Paraguay'),
    ('PE', 'Peru'),
    ('PH', 'Philippines'),
    ('PL', 'Poland'),
    ('PT', 'Portugal'),
    ('PR', 'Puerto Rico'),
    ('QA', 'Qatar'),
    ('RE', 'Réunion'),
    ('RO', 'Romania'),
    ('RW', 'Rwanda'),
    ('WS', 'Samoa'),
    ('SM', 'San Marino'),
    ('ST', 'São Tomé and Príncipe'),
    ('SA', 'Saudi Arabia'),
    ('SN', 'Senegal'),
    ('RS', 'Serbia'),
    ('SC', 'Seychelles'),
    ('SL', 'Sierra Leone'),
    ('SG', 'Singapore'),
    ('SK', 'Slovakia'),
    ('SI', 'Slovenia'),
    ('SB', 'Solomon Islands'),
    ('SO', 'Somalia'),
    ('SS', 'South Sudan'),
    ('ES', 'Spain'),
    ('LK', 'Sri Lanka'),
    ('SD', 'Sudan'),
    ('SR', 'Suriname'),
    ('SZ', 'Swaziland'),
    ('SE', 'Sweden'),
    ('CH', 'Switzerland'),
    ('SY', 'Syria'),
    ('TW', 'Taiwan'),
    ('TJ', 'Tajikistan'),
    ('TZ', 'Tanzania'),
    ('TL', 'Timor-Leste'),
    ('TG', 'Togo'),
    ('TO', 'Tonga'),
    ('TT', 'Trinidad and Tobago'),
    ('TN', 'Tunisia'),
    ('TR', 'Turkey'),
    ('TM', 'Turkmenistan'),
    ('TC', 'Turks and Caicos Islands'),
    ('TV', 'Tuvalu'),
    ('UG', 'Uganda'),
    ('UA', 'Ukraine'),
    ('UY', 'Uruguay'),
    ('UZ', 'Uzbekistan'),
    ('VU', 'Vanuatu'),
    ('VA', 'Vatican City'),
    ('VE', 'Venezuela'),
    ('VI', 'U.S. Virgin Islands'),
    ('EH', 'Western Sahara'),
    ('YE', 'Yemen'),
    ('ZM', 'Zambia'),
    ('ZW','Zimbabwe'),
]

class CustomUser(AbstractUser):
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    country = models.CharField(max_length=50, choices=COUNTRY_CHOICES)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='GBP')
    referral_code = models.CharField(max_length=50, blank=True, null=True)
    is_over_18 = models.BooleanField(default=False)
    wallet_linked = models.BooleanField(default=False)
    account_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    profit_today    = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bonus_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    #Account Upgrade
    PLAN_CHOICES = [
        ("mini", "Mini"),              # default for all new users
        ("starter", "Starter"),
        ("bronze", "Bronze"),
        ("silver", "Silver"),
        ("diamond", "Diamond"),
        ("gold", "Gold"),
    ]

    upgrade_note = models.TextField(blank=True, help_text="Optional note/reason for upgrade decisions")
    current_plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default="mini")
    pending_plan = models.CharField(max_length=20, choices=PLAN_CHOICES, null=True, blank=True)
    upgrade_progress = models.PositiveSmallIntegerField(default=0)  # 0–100


    REQUIRED_FIELDS = ['email', 'full_name', 'phone_number', 'gender', 'country']


# KYC DUC
# core/models.py

class KYC(models.Model):
    DOCUMENT_CHOICES = [
        ("passport", "Passport"),
        ("id_card", "National ID"),
        ("drivers_license", "Driver’s License"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    full_name = models.CharField(max_length=200)
    document_type = models.CharField(max_length=50, choices=DOCUMENT_CHOICES)
    document_number = models.CharField(max_length=100)

    # New location fields (optional)
    state = models.CharField(max_length=64, blank=True)
    city  = models.CharField(max_length=64, blank=True)

    # New preferred fields (use these going forward)
    # For Passport, store the passport image in id_front and leave id_back empty.
    id_front = models.FileField(upload_to="kyc/front/", blank=True, null=True)
    id_back  = models.FileField(upload_to="kyc/back/",  blank=True, null=True)

    # Keep existing single-file field for older submissions (optional to use now)
    id_document = models.FileField(upload_to="kyc/id_docs/", blank=True, null=True)

    selfie = models.ImageField(upload_to="kyc/selfies/", blank=True, null=True)

    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} ({self.user.username})"

    # --- Helpers & validation ---
    def requires_back(self) -> bool:
        return self.document_type in {"id_card", "drivers_license"}

    def clean(self):
        """
        Validate that:
        - id_front is always present,
        - id_back is present when required (ID/Driver’s License),
        - for Passport, id_back is optional.
        """
        errors = {}

        # Prefer new fields; allow id_document to cover id_front if migrating old flows.
        has_front = bool(self.id_front or self.id_document)
        has_back  = bool(self.id_back)

        if not has_front:
            errors["id_front"] = "Please upload the front image (or passport scan)."

        if self.requires_back() and not has_back:
            errors["id_back"] = "Please upload the back image for this document type."

        if errors:
            raise ValidationError(errors)

# ✅ Wallet Settings for Crypto
class WalletSettings(models.Model):
    btc_address = models.CharField(max_length=255, verbose_name="BTC Address")
    eth_address = models.CharField(max_length=255, verbose_name="ETH Address")
    usdt_address = models.CharField(max_length=255, verbose_name="USDT Address")
    updated_at = models.DateTimeField(auto_now=True)

    # NEW:
    support_email = models.EmailField(blank=True, null=True, help_text="Shown in the deposit popup.")

    class Meta:
        verbose_name = "Wallet Setting"
        verbose_name_plural = "Wallet Settings"

    def __str__(self):
        return f"Wallet Settings (Updated: {self.updated_at})"


# ✅ Vendor Model
class Vendor(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='vendors/', blank=True, null=True)
    verified = models.BooleanField(default=False)
    location = models.CharField(max_length=2, choices=COUNTRY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    STATUS_CHOICES = [
        ("online", "Online"),
        ("away", "Away"),
        ("offline", "Offline"),
    ]

    name = models.CharField(max_length=255)
    # … your other vendor fields …
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="offline",
    )

    def status_icon(self):
        """Return Tailwind color + icon depending on status"""
        if self.status == "online":
            return "bg-green-500"
        elif self.status == "away":
            return "bg-yellow-500"
        return "bg-gray-400"  # offline


# ✅ P2P Trade Model
class P2PTrade(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('paid', 'User Paid'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='p2p_trades')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_proof = models.ImageField(upload_to='payment_proofs/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Trade by {self.user.username} with {self.vendor.name}"


# ✅ Chat Message Model
class ChatMessage(models.Model):
    trade = models.ForeignKey(P2PTrade, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='chat_uploads/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username}: {self.message[:20] if self.message else 'File only'}"
    
# bonus and active trade
class AccountDeposit(models.Model):
    STATUS_CHOICES = [('pending','Pending'), ('approved','Approved'), ('rejected','Rejected')]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='deposits')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    note = models.CharField(max_length=255, blank=True)  # keeps your existing field
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Deposit £{self.amount} by {self.user.username} [{self.status}]"

    # ----- helpers -----
    def _note_dict(self):
        """Safely parse note JSON; returns {} on any error."""
        try:
            return json.loads(self.note or "{}")
        except Exception:
            return {}

    @property
    def proof_url(self):
        """
        If note contains {"file": "<path or url>"} return a URL you can open.
        Works with absolute URLs and MEDIA_URL + relative paths.
        """
        data = self._note_dict()
        f = data.get("file")
        if not f:
            return None

        f = str(f)
        # if already absolute URL, return as-is
        if f.startswith("http://") or f.startswith("https://"):
            return f
        # otherwise join with MEDIA_URL
        return settings.MEDIA_URL.rstrip("/") + "/" + f.lstrip("/")

    @property
    def has_proof(self):
        """Convenience flag for templates."""
        return bool(self.proof_url)

class AccountWithdrawal(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    METHOD_CHOICES = [
        ('btc',        'Bitcoin'),
        ('eth',        'Ethereum'),
        ('usdt_trc20', 'USDT (TRC20)'),
        ('bank',       'Bank Transfer'),
    ]

    user   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='withdrawals')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='btc')

    note   = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    # ---------- Bank details (used if method == 'bank') ----------
    bank_name        = models.CharField(max_length=128, blank=True, null=True)
    account_name     = models.CharField(max_length=128, blank=True, null=True)
    account_number   = models.CharField(max_length=64,  blank=True, null=True)
    routing_or_swift = models.CharField(max_length=64,  blank=True, null=True)
    country          = models.CharField(max_length=64,  blank=True, null=True)

    # ---------- US-only extras ----------
    US_ACCOUNT_TYPES = [
        ('checking', 'Checking'),
        ('savings',  'Savings'),
    ]
    us_account_type = models.CharField(
        max_length=16, choices=US_ACCOUNT_TYPES, blank=True, null=True
    )
    us_ssn = models.CharField(
        max_length=16, blank=True, null=True
    )

    def display_info(self):
        """
        Used in templates (pending withdrawals card).
        Bank:   "Bank Transfer *****1234"
        Crypto: "Ethereum wallet *****bjws"
        """
        # --- Bank ---
        if self.method == "bank":
            if self.account_number:
                last4 = self.account_number[-4:]
                return f"{self.get_method_display()} *****{last4}"
            return self.get_method_display()

        # --- Crypto ---
        if self.method in ["btc", "eth", "usdt_trc20"]:
            wallet_address = None
            try:
                note_data = json.loads(self.note) if self.note else {}
                wallet_address = note_data.get("meta", {}).get("address")
            except Exception:
                pass

            if wallet_address:
                last4 = wallet_address[-4:]
                return f"{self.get_method_display()} wallet *****{last4}"
            return f"{self.get_method_display()} wallet"

        return self.get_method_display()

    def parsed_details(self):
        """
        For Django admin: nicely formatted details instead of raw JSON.
        """
        try:
            note_data = json.loads(self.note) if self.note else {}
        except Exception:
            return "-"

        # --- Bank ---
        if self.method == "bank":
            bank = note_data.get("meta", {}).get("bank", {})
            if bank:
                return format_html(
                    "Bank name: {}<br>"
                    "Account name: {}<br>"
                    "Account number: {}<br>"
                    "Routing/SWIFT: {}<br>"
                    "Country: {}",
                    bank.get("bank_name", "-"),
                    bank.get("account_name", "-"),
                    bank.get("account_number", "-"),
                    bank.get("routing_or_swift", "-"),
                    bank.get("country", "-"),
                )
            return "Bank Transfer (no details)"

        # --- Crypto ---
        if self.method in ["btc", "eth", "usdt_trc20"]:
            address = note_data.get("meta", {}).get("address")
            if address:
                return format_html(
                    "{} wallet<br><code>{}</code>",
                    self.get_method_display(),
                    address,
                )
            return f"{self.get_method_display()} wallet"

        return "-"

    def __str__(self):
        return f"Withdrawal £{self.amount} by {self.user.username} [{self.status}]"

 # Link Wallet
class LinkedWallet(models.Model):
    STATUS_CHOICES = [
        ("linked", "Linked"),
        ("unlinked", "Unlinked"),
    ]

    # Tie wallet to a user
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wallets"
    )

    # Wallet details
    provider = models.CharField(max_length=100)
    wallet_phrase = models.JSONField(default=list)   # always required, defaults to []
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="linked")
    active = models.BooleanField(default=True)

    # Timestamps
    linked_at = models.DateTimeField(default=timezone.now)      # when wallet was linked
    created_at = models.DateTimeField(default=timezone.now)     # avoids migration prompts
    updated_at = models.DateTimeField(auto_now=True)            # auto-updates on save

    # Show phrase in admin (first 12 words)
    def display_wallet_phrase(self):
        return ", ".join(self.wallet_phrase[:12]) if self.wallet_phrase else "—"
    display_wallet_phrase.short_description = "Wallet Seed Phrase"

    class Meta:
        verbose_name = "Linked Wallet"
        verbose_name_plural = "Linked Wallets"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.provider}"

class ActiveTrade(models.Model):
    SIDE_CHOICES = (('buy', 'Buy'), ('sell', 'Sell'))
    STATUS_CHOICES = (('open', 'Open'), ('closed', 'Closed'))
    CREATED_BY_CHOICES = (('user', 'User'), ('admin', 'Admin'))

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='active_trades'
    )
    asset = models.CharField(max_length=20)
    side = models.CharField(max_length=4, choices=SIDE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    leverage = models.CharField(max_length=10, blank=True, null=True)
    duration = models.CharField(max_length=10, blank=True, null=True)

    profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=6, choices=STATUS_CHOICES, default='open')

    created_by = models.CharField(max_length=5, choices=CREATED_BY_CHOICES, default='user')

    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} {self.asset} {self.get_side_display()} ({self.status})"
    

US_ACCOUNT_TYPES = [
        ('checking', 'Checking'),
        ('savings',  'Savings'),
    ]

class BankInfo(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bank_info')
    bank_name = models.CharField(max_length=120, blank=True)
    account_name = models.CharField(max_length=120, blank=True)
    account_number = models.CharField(max_length=120, blank=True)
    routing_or_swift = models.CharField(max_length=120, blank=True)
    country = models.CharField(max_length=60, blank=True)
    us_account_type = models.CharField(max_length=16, choices=US_ACCOUNT_TYPES, blank=True, null=True)
    us_ssn = models.CharField(max_length=16, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} — {self.bank_name}"


# --- Copy Trading ---
class ExpertTrader(models.Model):
    name         = models.CharField(max_length=120)
    avatar       = models.ImageField(upload_to='experts/', blank=True, null=True)
    wins         = models.PositiveIntegerField(default=0)
    losses       = models.PositiveIntegerField(default=0)
    profit_share = models.PositiveIntegerField(
        default=20,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percent share taken by expert (e.g., 20 = 20%)"
    )
    is_active    = models.BooleanField(default=True)
    bio          = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def win_rate(self):
        total = self.wins + self.losses
        return round((self.wins / total) * 100, 1) if total else 0.0


class CopySubscription(models.Model):
    STATUS = (('active', 'Active'), ('cancelled', 'Cancelled'))
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='copy_subs')
    expert     = models.ForeignKey(ExpertTrader, on_delete=models.CASCADE, related_name='subscribers')
    status     = models.CharField(max_length=10, choices=STATUS, default='active')
    active     = models.BooleanField(default=True)  # convenience flag for quick checks
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at   = models.DateTimeField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'expert', 'active']),
        ]

    def __str__(self):
        return f"{self.user.username} → {self.expert.name} ({self.status})"


# Mass/broadcast emails created from Admin
class AdminMailout(models.Model):
    SEGMENT_CHOICES = [
        ("ALL", "All users"),
        ("NO_DEPOSIT", "Users without any deposit"),
        ("SPECIFIC", "Specific users only"),
    ]
    subject = models.CharField(max_length=200)
    body_html = models.TextField(help_text="You can paste basic HTML. This will be wrapped in the standard email template.")
    segment = models.CharField(max_length=20, choices=SEGMENT_CHOICES, default="ALL")
    recipients = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True,
                                        help_text="Used only when segment is 'Specific users'")
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    sent_count = models.PositiveIntegerField(default=0)
    is_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"Mailout: {self.subject} ({self.segment})"



class AdminNotification(models.Model):
    """
    A one-to-one style message from Admin to a specific user.
    Shows on the user's dashboard until marked as read.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="admin_notifications")
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        status = "read" if self.is_read else "unread"
        return f"{self.user} · {self.title} ({status})"



