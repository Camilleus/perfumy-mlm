"""
Przystanek Psik-Psik – Bot Telegram
====================================
Uruchomienie:
    python bot.py

Wymagania w .env (lub Railway env vars):
    TELEGRAM_TOKEN=1234567890:ABCdefGhIJKlmNoPQRsTUVwXyZ
    DATABASE_URL=postgresql://...
    DJANGO_SETTINGS_MODULE=perfumy.settings   ← zmień na nazwę swojego projektu
"""

import os
import sys
import django
import logging
import asyncio
from decimal import Decimal

# ── Bootstrapowanie Django (dostęp do bazy danych) ────────────────────────────
# Upewnij się że bot.py leży w katalogu głównym projektu (obok manage.py)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()
# ──────────────────────────────────────────────────────────────────────────────

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, ContextTypes, filters
)
from asgiref.sync import sync_to_async

from products.models import Product
from orders.models import Order, OrderItem
from sellers.models import Seller, Referral

logging.basicConfig(
    format="%(asctime)s – %(name)s – %(levelname)s – %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN", "8777576462:AAFuFhqntm53y_OifXVGBXLH9Chfffifdt4")

# ── Stany ConversationHandler ─────────────────────────────────────────────────
(
    BROWSE_GENDER, BROWSE_BRAND, BROWSE_LIST,
    CHECKOUT_NAME, CHECKOUT_PHONE, CHECKOUT_ADDRESS,
    CHECKOUT_POSTAL, CHECKOUT_CITY, CHECKOUT_REFERRAL,
    CHECKOUT_CONFIRM,
    QUIZ_INTENSITY, QUIZ_CATEGORY, QUIZ_OCCASION, QUIZ_GENDER,
) = range(14)

# ── Pomocnicze ────────────────────────────────────────────────────────────────

def cart_key(user_id):
    return f"cart_{user_id}"

def get_cart(context, user_id):
    return context.bot_data.setdefault(cart_key(user_id), {})

def cart_total(cart_items, products_dict):
    total = Decimal("0")
    for pid, qty in cart_items.items():
        p = products_dict.get(int(pid))
        if p:
            total += p.price * qty
    return total

def shipping_cost(qty):
    return Decimal("0") if qty >= 3 else Decimal("30")

# ── /start ────────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # sprawdź czy to link polecający: /start REF_KAMIL-X7K2
    if context.args:
        ref_code = context.args[0].upper()
        context.user_data["referral_code"] = ref_code

    keyboard = ReplyKeyboardMarkup([
        ["🛍️ Przeglądaj perfumy", "🧪 Quiz zapachowy"],
        ["🛒 Koszyk", "📦 Moje zamówienia"],
        ["🔗 Mój panel polecającego", "ℹ️ O sklepie"],
    ], resize_keyboard=True)

    await update.message.reply_text(
        f"👋 Cześć, *{user.first_name}*!\n\n"
        "Witaj w *Przystanek Psik-Psik* 🌸\n"
        "Perfumy znanych marek w super cenach.\n\n"
        "Co chcesz zrobić?",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# ── PRZEGLĄDAJ ────────────────────────────────────────────────────────────────

async def browse_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👨 Dla Niego", callback_data="gender_M"),
         InlineKeyboardButton("👩 Dla Niej", callback_data="gender_K")],
        [InlineKeyboardButton("✨ Unisex", callback_data="gender_U"),
         InlineKeyboardButton("🌍 Wszystkie", callback_data="gender_all")],
    ])
    await update.message.reply_text(
        "🌸 *Przeglądaj kolekcję*\n\nWybierz kategorię:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    return BROWSE_GENDER

async def browse_gender_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    gender = query.data.replace("gender_", "")
    context.user_data["filter_gender"] = gender

    # Pobierz marki z bazy
    @sync_to_async
    def get_brands():
        qs = Product.objects.filter(is_available=True, stock_quantity__gt=0)
        if gender != "all":
            qs = qs.filter(gender=gender)
        return sorted(set(qs.values_list("brand", flat=True)))

    brands = await get_brands()
    context.user_data["brands"] = brands

    # Buduj klawiaturę marek (po 2 w rzędzie)
    rows = []
    for i in range(0, min(len(brands), 20), 2):
        row = [InlineKeyboardButton(brands[i], callback_data=f"brand_{brands[i]}")]
        if i + 1 < len(brands):
            row.append(InlineKeyboardButton(brands[i+1], callback_data=f"brand_{brands[i+1]}"))
        rows.append(row)
    rows.append([InlineKeyboardButton("🌍 Wszystkie marki", callback_data="brand_all")])

    await query.edit_message_text(
        "🏷️ Wybierz markę:",
        reply_markup=InlineKeyboardMarkup(rows)
    )
    return BROWSE_BRAND

async def browse_brand_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    brand = query.data.replace("brand_", "")
    context.user_data["filter_brand"] = brand
    context.user_data["browse_page"] = 0
    await show_product_list(query, context)
    return BROWSE_LIST

async def show_product_list(query, context, page=0):
    gender = context.user_data.get("filter_gender", "all")
    brand = context.user_data.get("filter_brand", "all")
    context.user_data["browse_page"] = page
    PER_PAGE = 5

    @sync_to_async
    def get_products():
        qs = Product.objects.filter(is_available=True, stock_quantity__gt=0)
        if gender != "all":
            qs = qs.filter(gender=gender)
        if brand != "all":
            qs = qs.filter(brand=brand)
        return list(qs.order_by("brand", "name"))

    products = await get_products()
    total = len(products)
    page_products = products[page*PER_PAGE:(page+1)*PER_PAGE]

    if not page_products:
        await query.edit_message_text("😔 Brak produktów dla tych filtrów.")
        return

    context.user_data["current_products"] = {str(p.pk): p for p in products}

    rows = []
    for p in page_products:
        label = f"{p.brand} – {p.name} | {p.price} zł"
        rows.append([InlineKeyboardButton(label, callback_data=f"prod_{p.pk}")])

    # Paginacja
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Wstecz", callback_data=f"page_{page-1}"))
    if (page+1)*PER_PAGE < total:
        nav.append(InlineKeyboardButton("▶️ Dalej", callback_data=f"page_{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("🔙 Zmień filtry", callback_data="change_filters")])

    await query.edit_message_text(
        f"🛍️ Znaleziono *{total}* perfum (strona {page+1}):",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(rows)
    )

async def browse_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("page_"):
        page = int(data.replace("page_", ""))
        await show_product_list(query, context, page)
        return BROWSE_LIST

    if data == "change_filters":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👨 Dla Niego", callback_data="gender_M"),
             InlineKeyboardButton("👩 Dla Niej", callback_data="gender_K")],
            [InlineKeyboardButton("✨ Unisex", callback_data="gender_U"),
             InlineKeyboardButton("🌍 Wszystkie", callback_data="gender_all")],
        ])
        await query.edit_message_text("Wybierz kategorię:", reply_markup=keyboard)
        return BROWSE_GENDER

    if data.startswith("prod_"):
        pid = int(data.replace("prod_", ""))

        @sync_to_async
        def get_product(pk):
            try:
                return Product.objects.get(pk=pk)
            except Product.DoesNotExist:
                return None

        p = await get_product(pid)
        if not p:
            await query.edit_message_text("❌ Produkt nie znaleziony.")
            return BROWSE_LIST

        gender_map = {"M": "Męskie", "K": "Damskie", "U": "Unisex"}
        text = (
            f"*{p.brand} – {p.name}*\n"
            f"_{p.get_concentration_display()}_ | {gender_map.get(p.gender, '')}\n\n"
        )
        if p.scent_notes:
            text += f"🌸 *Nuty:* {p.scent_notes}\n\n"
        if p.description:
            desc = p.description[:300] + ("..." if len(p.description) > 300 else "")
            text += f"{desc}\n\n"
        text += f"💰 *Cena: {p.price} zł*\n"
        text += f"📦 Dostępność: {'✅ ' + str(p.stock_quantity) + ' szt.' if p.stock_quantity > 0 else '❌ Brak'}"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🛒 Dodaj do koszyka", callback_data=f"add_{p.pk}")],
            [InlineKeyboardButton("🔙 Wróć do listy", callback_data=f"page_{context.user_data.get('browse_page', 0)}")],
        ])

        if p.image:
            # Zdjęcie z Cloudinary – pełny URL
            img_url = p.image if isinstance(p.image, str) else p.image.url
            try:
                await query.message.reply_photo(
                    photo=img_url,
                    caption=text,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
                await query.delete_message()
            except Exception:
                await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)

        return BROWSE_LIST

    if data.startswith("add_"):
        pid = data.replace("add_", "")
        cart = get_cart(context, update.effective_user.id)
        cart[pid] = cart.get(pid, 0) + 1

        @sync_to_async
        def get_name(pk):
            try:
                p = Product.objects.get(pk=int(pk))
                return p.name, p.brand
            except Product.DoesNotExist:
                return "Produkt", ""

        name, brand = await get_name(pid)
        total_items = sum(cart.values())

        await query.answer(f"✅ Dodano do koszyka! ({total_items} szt. w koszyku)", show_alert=True)
        return BROWSE_LIST

    return BROWSE_LIST

# ── KOSZYK ────────────────────────────────────────────────────────────────────

async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cart = get_cart(context, user_id)

    if not cart:
        await update.message.reply_text(
            "🛒 Koszyk jest pusty!\n\nUżyj *Przeglądaj perfumy* żeby coś dodać.",
            parse_mode="Markdown"
        )
        return

    @sync_to_async
    def get_cart_products(pids):
        return {p.pk: p for p in Product.objects.filter(pk__in=[int(x) for x in pids])}

    products_dict = await get_cart_products(cart.keys())
    total_qty = sum(cart.values())
    total_price = cart_total(cart, products_dict)
    ship = shipping_cost(total_qty)

    lines = []
    for pid, qty in cart.items():
        p = products_dict.get(int(pid))
        if p:
            lines.append(f"• {p.brand} {p.name} ×{qty} = *{p.price * qty} zł*")

    ship_txt = "GRATIS 🎉" if ship == 0 else f"{ship} zł"
    text = (
        "🛒 *Twój koszyk:*\n\n"
        + "\n".join(lines)
        + f"\n\n📦 Dostawa (InPost): *{ship_txt}*"
        + f"\n💰 *Razem: {total_price + ship} zł*"
    )
    if total_qty < 3:
        text += f"\n\n💡 Dodaj {3 - total_qty} perfumy więcej → darmowa dostawa!"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Zamawiam!", callback_data="checkout_start")],
        [InlineKeyboardButton("🗑️ Wyczyść koszyk", callback_data="cart_clear")],
    ])

    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)

async def cart_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if query.data == "cart_clear":
        context.bot_data.pop(cart_key(user_id), None)
        await query.edit_message_text("🗑️ Koszyk wyczyszczony.")

    elif query.data == "checkout_start":
        await query.edit_message_text(
            "📝 *Składamy zamówienie!*\n\n"
            "Podaj swoje *imię i nazwisko*:",
            parse_mode="Markdown"
        )
        return CHECKOUT_NAME

    return ConversationHandler.END

# ── CHECKOUT ──────────────────────────────────────────────────────────────────

async def checkout_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order_name"] = update.message.text.strip()
    await update.message.reply_text("📱 Podaj swój *numer telefonu*:", parse_mode="Markdown")
    return CHECKOUT_PHONE

async def checkout_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order_phone"] = update.message.text.strip()
    await update.message.reply_text("🏠 Podaj *ulicę i numer domu/mieszkania*:", parse_mode="Markdown")
    return CHECKOUT_ADDRESS

async def checkout_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order_address"] = update.message.text.strip()
    await update.message.reply_text("📮 Podaj *kod pocztowy* (np. 00-000):", parse_mode="Markdown")
    return CHECKOUT_POSTAL

async def checkout_postal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order_postal"] = update.message.text.strip()
    await update.message.reply_text("🏙️ Podaj *miasto*:", parse_mode="Markdown")
    return CHECKOUT_CITY

async def checkout_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order_city"] = update.message.text.strip()

    # Sprawdź czy jest zapisany kod polecenia z /start
    saved_ref = context.user_data.get("referral_code", "")
    if saved_ref:
        await update.message.reply_text(
            f"🎁 Wykryto kod polecenia: *{saved_ref}*\n"
            "Wpisz go poniżej aby aktywować rabat 20 zł, lub napisz *BRAK* aby pominąć:",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "🎁 Masz *kod polecenia*? Wpisz go i dostaniesz -20 zł!\n"
            "Jeśli nie – napisz *BRAK*:",
            parse_mode="Markdown"
        )
    return CHECKOUT_REFERRAL

async def checkout_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip().upper()
    discount = Decimal("0")
    referral_seller = None

    if code != "BRAK" and code:
        @sync_to_async
        def check_code(c):
            try:
                s = Seller.objects.get(referral_code=c)
                return s
            except Seller.DoesNotExist:
                return None

        referral_seller = await check_code(code)
        if referral_seller:
            discount = Decimal("20")
            context.user_data["referral_code"] = code
            context.user_data["referral_seller_id"] = referral_seller.pk
            await update.message.reply_text("✅ Kod zastosowany! Oszczędzasz *20 zł*.", parse_mode="Markdown")
        else:
            await update.message.reply_text("⚠️ Nieprawidłowy kod. Kontynuuję bez rabatu.")
            context.user_data["referral_code"] = ""

    context.user_data["discount"] = str(discount)

    # Pokaż podsumowanie
    user_id = update.effective_user.id
    cart = get_cart(context, user_id)

    @sync_to_async
    def get_products(pids):
        return {p.pk: p for p in Product.objects.filter(pk__in=[int(x) for x in pids])}

    products_dict = await get_products(cart.keys())
    total_qty = sum(cart.values())
    total_price = cart_total(cart, products_dict)
    ship = shipping_cost(total_qty)
    final = total_price + ship - discount

    lines = []
    for pid, qty in cart.items():
        p = products_dict.get(int(pid))
        if p:
            lines.append(f"• {p.brand} {p.name} ×{qty}")

    name = context.user_data.get("order_name", "")
    phone = context.user_data.get("order_phone", "")
    address = context.user_data.get("order_address", "")
    postal = context.user_data.get("order_postal", "")
    city = context.user_data.get("order_city", "")
    ship_txt = "GRATIS" if ship == 0 else f"{ship} zł"

    summary = (
        "📋 *Podsumowanie zamówienia:*\n\n"
        + "\n".join(lines)
        + f"\n\n👤 {name}\n📱 {phone}\n📍 {address}, {postal} {city}"
        + f"\n\n📦 Dostawa: *{ship_txt}*"
        + (f"\n🎁 Rabat: *-{discount} zł*" if discount > 0 else "")
        + f"\n💰 *Do zapłaty: {final} zł* (za pobraniem)"
        + "\n\n✅ Potwierdzasz zamówienie?"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ TAK, składam zamówienie!", callback_data="confirm_yes")],
        [InlineKeyboardButton("❌ Anuluj", callback_data="confirm_no")],
    ])

    await update.message.reply_text(summary, parse_mode="Markdown", reply_markup=keyboard)
    return CHECKOUT_CONFIRM

async def checkout_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "confirm_no":
        await query.edit_message_text("❌ Zamówienie anulowane. Koszyk pozostaje.")
        return ConversationHandler.END

    # Zapisz zamówienie do bazy Django
    user_id = update.effective_user.id
    cart = get_cart(context, user_id)

    @sync_to_async
    def save_order():
        from django.db import transaction
        
        products_dict = {p.pk: p for p in Product.objects.filter(
            pk__in=[int(x) for x in cart.keys()]
        )}
        total_qty = sum(cart.values())
        total_price = sum(products_dict[int(pid)].price * qty 
                         for pid, qty in cart.items() if int(pid) in products_dict)
        ship = shipping_cost(total_qty)
        discount = Decimal(context.user_data.get("discount", "0"))

        name_parts = context.user_data.get("order_name", " ").split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        with transaction.atomic():
            order = Order.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=f"telegram_{user_id}@psikpsik.bot",
                phone=context.user_data.get("order_phone", ""),
                address=context.user_data.get("order_address", ""),
                postal_code=context.user_data.get("order_postal", ""),
                city=context.user_data.get("order_city", ""),
                shipping_method="inpost",
                shipping_method_name="InPost Kurier",
                shipping_cost=ship,
                discount=discount,
                total_amount=total_price + ship - discount,
                note=f"Zamówienie przez Telegram (ID: {user_id})",
                status="new",
            )

            for pid, qty in cart.items():
                p = products_dict.get(int(pid))
                if p:
                    OrderItem.objects.create(
                        order=order,
                        product=p,
                        quantity=qty,
                        price=p.price * qty,
                    )

            # Prowizja MLM jeśli był kod polecenia
            ref_seller_id = context.user_data.get("referral_seller_id")
            if ref_seller_id:
                try:
                    ref_seller = Seller.objects.get(pk=ref_seller_id)
                    ref_seller.credit += Decimal("20")
                    ref_seller.save()
                    Referral.objects.create(
                        seller=ref_seller,
                        referred_email=f"telegram_{user_id}@psikpsik.bot",
                    )
                except Seller.DoesNotExist:
                    pass

            return order.pk

    order_pk = await save_order()

    # Wyczyść koszyk
    context.bot_data.pop(cart_key(user_id), None)
    context.user_data.pop("referral_code", None)
    context.user_data.pop("referral_seller_id", None)
    context.user_data.pop("discount", None)

    await query.edit_message_text(
        f"🎉 *Zamówienie #{order_pk} złożone!*\n\n"
        "Dostawa za pobraniem – kurier InPost dostarczy jutro.\n\n"
        "Dziękujemy za zakupy w *Przystanek Psik-Psik*! 🌸\n\n"
        "_Masz pytania? Napisz do nas._",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# ── QUIZ ZAPACHOWY ────────────────────────────────────────────────────────────

async def quiz_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌿 Delikatna i świeża", callback_data="qi_light")],
        [InlineKeyboardButton("🔥 Mocna i wieczorowa", callback_data="qi_strong")],
    ])
    await update.message.reply_text(
        "🧪 *Quiz zapachowy*\n\nJaką intensywność preferujesz?",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    return QUIZ_INTENSITY

async def quiz_intensity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["q_intensity"] = query.data.replace("qi_", "")
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌸 Kwiatowe / Owocowe", callback_data="qc_floral")],
        [InlineKeyboardButton("🪵 Drzewne / Korzenne", callback_data="qc_woody")],
    ])
    await query.edit_message_text("Główne nuty zapachowe?", reply_markup=keyboard)
    return QUIZ_CATEGORY

async def quiz_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["q_category"] = query.data.replace("qc_", "")
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("☀️ Na co dzień", callback_data="qo_daily")],
        [InlineKeyboardButton("✨ Specjalne wyjścia", callback_data="qo_special")],
    ])
    await query.edit_message_text("Na jaką okazję?", reply_markup=keyboard)
    return QUIZ_OCCASION

async def quiz_occasion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["q_occasion"] = query.data.replace("qo_", "")
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👩 Dla niej", callback_data="qg_K"),
         InlineKeyboardButton("👨 Dla niego", callback_data="qg_M")],
        [InlineKeyboardButton("✨ Wszystkie", callback_data="qg_all")],
    ])
    await query.edit_message_text("Dla kogo?", reply_markup=keyboard)
    return QUIZ_GENDER

async def quiz_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    gender = query.data.replace("qg_", "")

    intensity = context.user_data.get("q_intensity")
    category = context.user_data.get("q_category")
    occasion = context.user_data.get("q_occasion")

    @sync_to_async
    def find_products():
        qs = Product.objects.filter(is_available=True, stock_quantity__gt=0)
        if intensity:
            qs = qs.filter(intensity=intensity)
        if category:
            qs = qs.filter(category=category)
        if occasion:
            qs = qs.filter(occasion=occasion)
        if gender != "all":
            qs = qs.filter(gender=gender)
        return list(qs[:10])

    results = await find_products()

    if not results:
        await query.edit_message_text(
            "😔 Brak dopasowań dla tych kryteriów.\n"
            "Spróbuj ponownie z innymi opcjami."
        )
        return ConversationHandler.END

    lines = [f"🌸 *Twoje dopasowania ({len(results)}):*\n"]
    for p in results:
        lines.append(f"• *{p.brand} – {p.name}* | {p.price} zł")

    lines.append("\nUżyj *Przeglądaj perfumy* żeby dodać do koszyka!")

    await query.edit_message_text("\n".join(lines), parse_mode="Markdown")
    return ConversationHandler.END

# ── PANEL SPRZEDAWCY ──────────────────────────────────────────────────────────

async def seller_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = user.id

    @sync_to_async
    def get_seller_by_telegram():
        # Szukaj sellera po nazwie użytkownika Telegram lub username
        try:
            return Seller.objects.select_related("user").get(
                user__username=f"tg_{telegram_id}"
            )
        except Seller.DoesNotExist:
            return None

    seller = await get_seller_by_telegram()

    if not seller:
        await update.message.reply_text(
            "ℹ️ Nie masz jeszcze konta sprzedawcy.\n\n"
            "Zarejestruj się na stronie:\n"
            "🌐 https://przystanekperfumy.pl/rejestracja/\n\n"
            "Lub napisz /rejestracja żeby dowiedzieć się więcej.",
            parse_mode="Markdown"
        )
        return

    ref_url = f"https://przystanekperfumy.pl/rejestracja/{seller.referral_code}/"
    bot_link = f"https://t.me/PrzystanekPsikPsikBot?start={seller.referral_code}"

    @sync_to_async
    def get_stats(s):
        from orders.models import Order
        ref_count = Referral.objects.filter(seller=s).count()
        return ref_count

    ref_count = await get_stats(seller)

    text = (
        f"👤 *Panel sprzedawcy*\n\n"
        f"Poziom: *{seller.get_level_display()}*\n"
        f"Kredyt: *{seller.credit} zł*\n"
        f"Polecenia: *{ref_count}*\n\n"
        f"🔗 *Twój link (strona):*\n`{ref_url}`\n\n"
        f"📱 *Twój link (Telegram):*\n`{bot_link}`\n\n"
        f"Twój kod: *{seller.referral_code}*\n\n"
        f"Każdy kto skorzysta z Twojego linku dostaje *-20 zł*, "
        f"a Ty dostajesz *+20 zł kredytu*!"
    )

    await update.message.reply_text(text, parse_mode="Markdown")

# ── MOJE ZAMÓWIENIA ───────────────────────────────────────────────────────────

async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    @sync_to_async
    def get_orders():
        return list(
            Order.objects.filter(
                note__contains=f"Telegram (ID: {user_id})"
            ).prefetch_related("items__product").order_by("-created_at")[:5]
        )

    orders = await get_orders()

    if not orders:
        await update.message.reply_text(
            "📭 Nie masz jeszcze żadnych zamówień z Telegrama.\n\n"
            "Skorzystaj z *Przeglądaj perfumy* żeby złożyć pierwsze zamówienie!",
            parse_mode="Markdown"
        )
        return

    status_map = {
        "new": "🕐 Nowe",
        "confirmed": "✅ Potwierdzone",
        "shipped": "📦 Wysłane",
        "delivered": "🎉 Dostarczone",
        "cancelled": "❌ Anulowane",
    }

    lines = ["📦 *Twoje ostatnie zamówienia:*\n"]
    for o in orders:
        items_txt = ", ".join(
            f"{i.product.name} ×{i.quantity}"
            for i in o.items.all()
        )
        lines.append(
            f"*#{o.pk}* – {status_map.get(o.status, o.status)}\n"
            f"   {items_txt}\n"
            f"   💰 {o.total_amount} zł\n"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

# ── O SKLEPIE ─────────────────────────────────────────────────────────────────

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌸 *Przystanek Psik-Psik*\n\n"
        "Perfumy znanych marek w cenach hurtowych.\n"
        "Bez marży sieci – płacisz tylko za zapach!\n\n"
        "✅ 468 perfum w ofercie\n"
        "✅ Od 199,95 zł\n"
        "✅ Dostawa InPost – 30 zł (gratis przy 3+ szt.)\n"
        "✅ Płatność za pobraniem\n\n"
        "🌐 przystanekperfumy.pl",
        parse_mode="Markdown"
    )

# ── FALLBACK ──────────────────────────────────────────────────────────────────

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = ReplyKeyboardMarkup([
        ["🛍️ Przeglądaj perfumy", "🧪 Quiz zapachowy"],
        ["🛒 Koszyk", "📦 Moje zamówienia"],
        ["🔗 Mój panel polecającego", "ℹ️ O sklepie"],
    ], resize_keyboard=True)
    await update.message.reply_text(
        "Nie rozumiem tej komendy. Użyj przycisków poniżej 👇",
        reply_markup=keyboard
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Anulowano.")
    return ConversationHandler.END

# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(TOKEN).build()

    # ConversationHandler: przeglądanie
    browse_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🛍️ Przeglądaj perfumy$"), browse_start)],
        states={
            BROWSE_GENDER: [CallbackQueryHandler(browse_gender_chosen, pattern="^gender_")],
            BROWSE_BRAND: [CallbackQueryHandler(browse_brand_chosen, pattern="^brand_")],
            BROWSE_LIST: [CallbackQueryHandler(browse_callbacks)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    # ConversationHandler: quiz
    quiz_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🧪 Quiz zapachowy$"), quiz_start)],
        states={
            QUIZ_INTENSITY: [CallbackQueryHandler(quiz_intensity, pattern="^qi_")],
            QUIZ_CATEGORY: [CallbackQueryHandler(quiz_category, pattern="^qc_")],
            QUIZ_OCCASION: [CallbackQueryHandler(quiz_occasion, pattern="^qo_")],
            QUIZ_GENDER: [CallbackQueryHandler(quiz_gender, pattern="^qg_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # ConversationHandler: checkout (startowany z callbacka koszyka)
    checkout_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(cart_callbacks, pattern="^(checkout_start|cart_clear)$")],
        states={
            CHECKOUT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, checkout_name)],
            CHECKOUT_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, checkout_phone)],
            CHECKOUT_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, checkout_address)],
            CHECKOUT_POSTAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, checkout_postal)],
            CHECKOUT_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, checkout_city)],
            CHECKOUT_REFERRAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, checkout_referral)],
            CHECKOUT_CONFIRM: [CallbackQueryHandler(checkout_confirm, pattern="^confirm_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(browse_conv)
    app.add_handler(quiz_conv)
    app.add_handler(checkout_conv)
    app.add_handler(MessageHandler(filters.Regex("^🛒 Koszyk$"), show_cart))
    app.add_handler(MessageHandler(filters.Regex("^📦 Moje zamówienia$"), my_orders))
    app.add_handler(MessageHandler(filters.Regex("^🔗 Mój panel polecającego$"), seller_panel))
    app.add_handler(MessageHandler(filters.Regex("^ℹ️ O sklepie$"), about))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))

    logger.info("🤖 Bot uruchomiony!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()