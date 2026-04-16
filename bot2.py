"""
Przystanek Psik-Psik – Bot Telegram
====================================
Uruchomienie:
    python bot2.py
"""

import os
import sys
import django
import logging
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
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
    format="%(asctime)s – %(levelname)s – %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN", "8777576462:AAFuFhqntm53y_OifXVGBXLH9Chfffifdt4")

# ── Stany ─────────────────────────────────────────────────────────────────────
(
    ST_IDLE,
    ST_BROWSE_GENDER, ST_BROWSE_BRAND, ST_BROWSE_LIST,
    ST_QUIZ_INTENSITY, ST_QUIZ_CATEGORY, ST_QUIZ_OCCASION, ST_QUIZ_GENDER,
    ST_CHECKOUT_NAME, ST_CHECKOUT_PHONE, ST_CHECKOUT_ADDRESS,
    ST_CHECKOUT_POSTAL, ST_CHECKOUT_CITY, ST_CHECKOUT_REFERRAL,
    ST_CHECKOUT_CONFIRM,
) = range(15)

# ── Klawiatura główna ─────────────────────────────────────────────────────────
MAIN_KB = ReplyKeyboardMarkup([
    ["🛍️ Przeglądaj perfumy", "🧪 Quiz zapachowy"],
    ["🛒 Koszyk", "📦 Moje zamówienia"],
    ["🔗 Panel polecającego", "ℹ️ O sklepie"],
], resize_keyboard=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_cart(context, user_id):
    key = f"cart_{user_id}"
    return context.bot_data.setdefault(key, {})

def clear_cart(context, user_id):
    context.bot_data[f"cart_{user_id}"] = {}

def shipping_cost(qty: int) -> Decimal:
    return Decimal("0") if qty >= 3 else Decimal("30")

@sync_to_async
def db_get_products(gender="all", brand="all"):
    qs = Product.objects.filter(is_available=True, stock_quantity__gt=0)
    if gender != "all":
        qs = qs.filter(gender=gender)
    if brand != "all":
        qs = qs.filter(brand=brand)
    return list(qs.order_by("brand", "name"))

@sync_to_async
def db_get_brands(gender="all"):
    qs = Product.objects.filter(is_available=True, stock_quantity__gt=0)
    if gender != "all":
        qs = qs.filter(gender=gender)
    return sorted(set(qs.values_list("brand", flat=True)))

@sync_to_async
def db_get_product(pk):
    try:
        return Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return None

@sync_to_async
def db_get_cart_products(pids):
    return {p.pk: p for p in Product.objects.filter(pk__in=[int(x) for x in pids])}

@sync_to_async
def db_check_referral(code):
    try:
        return Seller.objects.get(referral_code=code)
    except Seller.DoesNotExist:
        return None

@sync_to_async
def db_save_order(cart, user_id, user_data):
    from django.db import transaction
    products_dict = {p.pk: p for p in Product.objects.filter(
        pk__in=[int(x) for x in cart.keys()]
    )}
    total_qty = sum(cart.values())
    total_price = sum(
        products_dict[int(pid)].price * qty
        for pid, qty in cart.items() if int(pid) in products_dict
    )
    ship = shipping_cost(total_qty)
    discount = Decimal(user_data.get("discount", "0"))

    name_parts = user_data.get("order_name", " ").split(" ", 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    with transaction.atomic():
        order = Order.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=f"telegram_{user_id}@psikpsik.bot",
            phone=user_data.get("order_phone", ""),
            address=user_data.get("order_address", ""),
            postal_code=user_data.get("order_postal", ""),
            city=user_data.get("order_city", ""),
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
                    order=order, product=p, quantity=qty, price=p.price * qty
                )

        ref_seller_id = user_data.get("referral_seller_id")
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

# ── /start i menu główne ──────────────────────────────────────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        context.user_data["referral_code"] = context.args[0].upper()

    await update.message.reply_text(
        f"👋 Cześć, *{update.effective_user.first_name}*!\n\n"
        "Witaj w *Przystanek Psik-Psik* 🌸\n"
        "Perfumy znanych marek w super cenach.\n\n"
        "Wybierz co chcesz zrobić:",
        parse_mode="Markdown",
        reply_markup=MAIN_KB
    )
    return ST_IDLE

async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Anulowano.", reply_markup=MAIN_KB)
    return ST_IDLE

# ── O SKLEPIE ─────────────────────────────────────────────────────────────────
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌸 *Przystanek Psik-Psik*\n\n"
        "Perfumy znanych marek bez marży sieci!\n\n"
        "✅ 468 perfum w ofercie\n"
        "✅ Od 199,95 zł\n"
        "✅ InPost – 30 zł (gratis przy 3+ szt.)\n"
        "✅ Płatność za pobraniem\n\n"
        "🌐 przystanekperfumy.pl",
        parse_mode="Markdown",
        reply_markup=MAIN_KB
    )
    return ST_IDLE

# ── PRZEGLĄDAJ ────────────────────────────────────────────────────────────────
async def browse_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👨 Dla Niego", callback_data="g_M"),
         InlineKeyboardButton("👩 Dla Niej", callback_data="g_K")],
        [InlineKeyboardButton("✨ Unisex", callback_data="g_U"),
         InlineKeyboardButton("🌍 Wszystkie", callback_data="g_all")],
    ])
    await update.message.reply_text(
        "🌸 *Przeglądaj kolekcję*\n\nWybierz kategorię:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    return ST_BROWSE_GENDER

async def browse_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    gender = query.data[2:]
    context.user_data["filter_gender"] = gender

    brands = await db_get_brands(gender)
    rows = []
    for i in range(0, min(len(brands), 20), 2):
        row = [InlineKeyboardButton(brands[i], callback_data=f"b_{brands[i]}")]
        if i + 1 < len(brands):
            row.append(InlineKeyboardButton(brands[i+1], callback_data=f"b_{brands[i+1]}"))
        rows.append(row)
    rows.append([InlineKeyboardButton("🌍 Wszystkie marki", callback_data="b_all")])

    await query.edit_message_text("🏷️ Wybierz markę:", reply_markup=InlineKeyboardMarkup(rows))
    return ST_BROWSE_BRAND

async def browse_brand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    brand = query.data[2:]
    context.user_data["filter_brand"] = brand
    context.user_data["browse_page"] = 0
    await _show_list(query, context, page=0)
    return ST_BROWSE_LIST

async def _show_list(query, context, page=0):
    PER_PAGE = 5
    gender = context.user_data.get("filter_gender", "all")
    brand = context.user_data.get("filter_brand", "all")

    products = await db_get_products(gender, brand)
    context.user_data["browse_page"] = page
    total = len(products)
    chunk = products[page*PER_PAGE:(page+1)*PER_PAGE]

    if not chunk:
        await query.edit_message_text("😔 Brak produktów dla tych filtrów.")
        return

    rows = []
    for p in chunk:
        rows.append([InlineKeyboardButton(
            f"{p.brand} – {p.name} | {p.price} zł",
            callback_data=f"p_{p.pk}"
        )])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"pg_{page-1}"))
    if (page+1)*PER_PAGE < total:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"pg_{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("🔙 Zmień filtry", callback_data="back_filters")])

    await query.edit_message_text(
        f"🛍️ Znaleziono *{total}* perfum (str. {page+1}):",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(rows)
    )

async def browse_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("pg_"):
        await _show_list(query, context, page=int(data[3:]))
        return ST_BROWSE_LIST

    if data == "back_filters":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👨 Dla Niego", callback_data="g_M"),
             InlineKeyboardButton("👩 Dla Niej", callback_data="g_K")],
            [InlineKeyboardButton("✨ Unisex", callback_data="g_U"),
             InlineKeyboardButton("🌍 Wszystkie", callback_data="g_all")],
        ])
        await query.edit_message_text("Wybierz kategorię:", reply_markup=keyboard)
        return ST_BROWSE_GENDER

    if data.startswith("p_"):
        pid = int(data[2:])
        p = await db_get_product(pid)
        if not p:
            await query.edit_message_text("❌ Produkt nie znaleziony.")
            return ST_BROWSE_LIST

        gender_map = {"M": "Męskie", "K": "Damskie", "U": "Unisex"}
        text = (
            f"*{p.brand} – {p.name}*\n"
            f"_{p.get_concentration_display()}_ | {gender_map.get(p.gender, '')}\n\n"
        )
        if p.scent_notes:
            text += f"🌸 *Nuty:* {p.scent_notes}\n\n"
        if p.description:
            text += p.description[:280] + ("…" if len(p.description) > 280 else "") + "\n\n"
        text += f"💰 *Cena: {p.price} zł*\n"
        text += f"📦 {'✅ Dostępny' if p.stock_quantity > 0 else '❌ Brak'}"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🛒 Dodaj do koszyka", callback_data=f"add_{p.pk}")],
            [InlineKeyboardButton("🔙 Wróć do listy", callback_data=f"pg_{context.user_data.get('browse_page', 0)}")],
        ])

        if p.image:
            img_url = p.image if isinstance(p.image, str) else p.image.url
            try:
                await query.message.reply_photo(photo=img_url, caption=text,
                                                parse_mode="Markdown", reply_markup=keyboard)
                await query.delete_message()
                return ST_BROWSE_LIST
            except Exception:
                pass
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
        return ST_BROWSE_LIST

    if data.startswith("add_"):
        pid = data[4:]
        cart = get_cart(context, update.effective_user.id)
        cart[pid] = cart.get(pid, 0) + 1
        total_items = sum(cart.values())
        await query.answer(f"✅ Dodano! ({total_items} szt. w koszyku)", show_alert=True)
        return ST_BROWSE_LIST

    return ST_BROWSE_LIST

# ── QUIZ ──────────────────────────────────────────────────────────────────────
async def quiz_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌿 Delikatna i świeża", callback_data="qi_light")],
        [InlineKeyboardButton("🔥 Mocna i wieczorowa", callback_data="qi_strong")],
    ])
    await update.message.reply_text(
        "🧪 *Quiz zapachowy*\n\nJaką intensywność preferujesz?",
        parse_mode="Markdown", reply_markup=keyboard
    )
    return ST_QUIZ_INTENSITY

async def quiz_intensity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["q_intensity"] = query.data[3:]
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌸 Kwiatowe / Owocowe", callback_data="qc_floral")],
        [InlineKeyboardButton("🪵 Drzewne / Korzenne", callback_data="qc_woody")],
    ])
    await query.edit_message_text("Główne nuty zapachowe?", reply_markup=keyboard)
    return ST_QUIZ_CATEGORY

async def quiz_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["q_category"] = query.data[3:]
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("☀️ Na co dzień", callback_data="qo_daily")],
        [InlineKeyboardButton("✨ Specjalne wyjścia", callback_data="qo_special")],
    ])
    await query.edit_message_text("Na jaką okazję?", reply_markup=keyboard)
    return ST_QUIZ_OCCASION

async def quiz_occasion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["q_occasion"] = query.data[3:]
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👩 Dla niej", callback_data="qg_K"),
         InlineKeyboardButton("👨 Dla niego", callback_data="qg_M")],
        [InlineKeyboardButton("✨ Wszystkie", callback_data="qg_all")],
    ])
    await query.edit_message_text("Dla kogo?", reply_markup=keyboard)
    return ST_QUIZ_GENDER

async def quiz_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    gender = query.data[3:]

    @sync_to_async
    def find():
        qs = Product.objects.filter(is_available=True, stock_quantity__gt=0)
        if context.user_data.get("q_intensity"):
            qs = qs.filter(intensity=context.user_data["q_intensity"])
        if context.user_data.get("q_category"):
            qs = qs.filter(category=context.user_data["q_category"])
        if context.user_data.get("q_occasion"):
            qs = qs.filter(occasion=context.user_data["q_occasion"])
        if gender != "all":
            qs = qs.filter(gender=gender)
        return list(qs[:10])

    results = await find()

    if not results:
        await query.edit_message_text("😔 Brak dopasowań.\nSpróbuj ponownie z innymi opcjami.")
        return ST_IDLE

    lines = [f"🌸 *Twoje dopasowania ({len(results)}):*\n"]
    for p in results:
        lines.append(f"• *{p.brand} – {p.name}* | {p.price} zł")
    lines.append("\nUżyj *Przeglądaj perfumy* → dodaj do koszyka!")

    await query.edit_message_text("\n".join(lines), parse_mode="Markdown")
    return ST_IDLE

# ── KOSZYK ────────────────────────────────────────────────────────────────────
async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cart = get_cart(context, user_id)

    if not cart:
        await update.message.reply_text(
            "🛒 Koszyk jest pusty!\nUżyj *Przeglądaj perfumy* żeby coś dodać.",
            parse_mode="Markdown", reply_markup=MAIN_KB
        )
        return ST_IDLE

    products_dict = await db_get_cart_products(cart.keys())
    total_qty = sum(cart.values())
    total_price = sum(products_dict[int(pid)].price * qty
                      for pid, qty in cart.items() if int(pid) in products_dict)
    ship = shipping_cost(total_qty)
    ship_txt = "GRATIS 🎉" if ship == 0 else f"{ship} zł"

    lines = []
    for pid, qty in cart.items():
        p = products_dict.get(int(pid))
        if p:
            lines.append(f"• {p.brand} {p.name} ×{qty} = *{p.price * qty} zł*")

    text = (
        "🛒 *Twój koszyk:*\n\n"
        + "\n".join(lines)
        + f"\n\n📦 Dostawa: *{ship_txt}*"
        + f"\n💰 *Razem: {total_price + ship} zł*"
    )
    if total_qty < 3:
        text += f"\n\n💡 Dodaj jeszcze {3 - total_qty} szt. → darmowa dostawa!"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Zamawiam!", callback_data="do_checkout")],
        [InlineKeyboardButton("🗑️ Wyczyść koszyk", callback_data="do_clear")],
    ])
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)
    return ST_IDLE

async def cart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if query.data == "do_clear":
        clear_cart(context, user_id)
        await query.edit_message_text("🗑️ Koszyk wyczyszczony.")
        return ST_IDLE

    if query.data == "do_checkout":
        await query.edit_message_text(
            "📝 *Składamy zamówienie!*\n\nPodaj swoje *imię i nazwisko*:",
            parse_mode="Markdown"
        )
        return ST_CHECKOUT_NAME

    return ST_IDLE

# ── CHECKOUT ──────────────────────────────────────────────────────────────────
async def checkout_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order_name"] = update.message.text.strip()
    await update.message.reply_text("📱 Podaj *numer telefonu*:", parse_mode="Markdown")
    return ST_CHECKOUT_PHONE

async def checkout_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order_phone"] = update.message.text.strip()
    await update.message.reply_text("🏠 Podaj *ulicę i numer domu*:", parse_mode="Markdown")
    return ST_CHECKOUT_ADDRESS

async def checkout_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order_address"] = update.message.text.strip()
    await update.message.reply_text("📮 Podaj *kod pocztowy* (np. 00-000):", parse_mode="Markdown")
    return ST_CHECKOUT_POSTAL

async def checkout_postal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order_postal"] = update.message.text.strip()
    await update.message.reply_text("🏙️ Podaj *miasto*:", parse_mode="Markdown")
    return ST_CHECKOUT_CITY

async def checkout_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order_city"] = update.message.text.strip()
    saved_ref = context.user_data.get("referral_code", "")
    msg = (
        f"🎁 Wykryto kod: *{saved_ref}*\nWpisz go aby aktywować -20 zł, lub napisz *BRAK*:"
        if saved_ref else
        "🎁 Masz *kod polecenia*? Wpisz go (-20 zł)!\nJeśli nie – napisz *BRAK*:"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")
    return ST_CHECKOUT_REFERRAL

async def checkout_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip().upper()
    discount = Decimal("0")

    if code != "BRAK" and code:
        seller = await db_check_referral(code)
        if seller:
            discount = Decimal("20")
            context.user_data["referral_code"] = code
            context.user_data["referral_seller_id"] = seller.pk
            await update.message.reply_text("✅ Kod OK! Oszczędzasz *20 zł*.", parse_mode="Markdown")
        else:
            context.user_data["referral_code"] = ""
            await update.message.reply_text("⚠️ Nieprawidłowy kod. Kontynuuję bez rabatu.")

    context.user_data["discount"] = str(discount)

    user_id = update.effective_user.id
    cart = get_cart(context, user_id)
    products_dict = await db_get_cart_products(cart.keys())
    total_qty = sum(cart.values())
    total_price = sum(products_dict[int(pid)].price * qty
                      for pid, qty in cart.items() if int(pid) in products_dict)
    ship = shipping_cost(total_qty)
    final = total_price + ship - discount
    ship_txt = "GRATIS" if ship == 0 else f"{ship} zł"

    lines = [f"• {products_dict[int(pid)].brand} {products_dict[int(pid)].name} ×{qty}"
             for pid, qty in cart.items() if int(pid) in products_dict]

    summary = (
        "📋 *Podsumowanie zamówienia:*\n\n"
        + "\n".join(lines)
        + f"\n\n👤 {context.user_data.get('order_name', '')}"
        + f"\n📱 {context.user_data.get('order_phone', '')}"
        + f"\n📍 {context.user_data.get('order_address', '')}, "
        + f"{context.user_data.get('order_postal', '')} {context.user_data.get('order_city', '')}"
        + f"\n\n📦 Dostawa: *{ship_txt}*"
        + (f"\n🎁 Rabat: *-{discount} zł*" if discount > 0 else "")
        + f"\n💰 *Do zapłaty: {final} zł* (za pobraniem)"
        + "\n\n✅ Potwierdzasz zamówienie?"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ TAK, składam!", callback_data="confirm_yes")],
        [InlineKeyboardButton("❌ Anuluj", callback_data="confirm_no")],
    ])
    await update.message.reply_text(summary, parse_mode="Markdown", reply_markup=keyboard)
    return ST_CHECKOUT_CONFIRM

async def checkout_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if query.data == "confirm_no":
        await query.edit_message_text("❌ Zamówienie anulowane. Koszyk pozostaje.")
        return ST_IDLE

    cart = get_cart(context, user_id)
    order_pk = await db_save_order(cart, user_id, context.user_data)

    clear_cart(context, user_id)
    context.user_data.pop("referral_code", None)
    context.user_data.pop("referral_seller_id", None)
    context.user_data.pop("discount", None)

    await query.edit_message_text(
        f"🎉 *Zamówienie #{order_pk} złożone!*\n\n"
        "Kurier InPost dostarczy jutro. Płatność za pobraniem.\n\n"
        "Dziękujemy! 🌸 *Przystanek Psik-Psik*",
        parse_mode="Markdown"
    )
    return ST_IDLE

# ── MOJE ZAMÓWIENIA ───────────────────────────────────────────────────────────
async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    @sync_to_async
    def get_orders():
        return list(
            Order.objects.filter(note__contains=f"Telegram (ID: {user_id})")
            .prefetch_related("items__product")
            .order_by("-created_at")[:5]
        )

    orders = await get_orders()
    if not orders:
        await update.message.reply_text(
            "📭 Brak zamówień z Telegrama.\nZłóż pierwsze przez *Przeglądaj perfumy*!",
            parse_mode="Markdown", reply_markup=MAIN_KB
        )
        return ST_IDLE

    status_map = {"new": "🕐 Nowe", "confirmed": "✅ Potwierdzone",
                  "shipped": "📦 Wysłane", "delivered": "🎉 Dostarczone",
                  "cancelled": "❌ Anulowane"}

    lines = ["📦 *Twoje zamówienia:*\n"]
    for o in orders:
        items_txt = ", ".join(f"{i.product.name} ×{i.quantity}" for i in o.items.all())
        lines.append(
            f"*#{o.pk}* – {status_map.get(o.status, o.status)}\n"
            f"   {items_txt}\n"
            f"   💰 {o.total_amount} zł\n"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown", reply_markup=MAIN_KB)
    return ST_IDLE

# ── PANEL POLECAJĄCEGO ────────────────────────────────────────────────────────
async def seller_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    @sync_to_async
    def get_seller():
        try:
            return Seller.objects.select_related("user").get(
                user__username=f"tg_{user_id}"
            )
        except Seller.DoesNotExist:
            return None

    @sync_to_async
    def get_ref_count(s):
        return Referral.objects.filter(seller=s).count()

    seller = await get_seller()
    if not seller:
        await update.message.reply_text(
            "ℹ️ Nie masz konta sprzedawcy.\n\n"
            "Zarejestruj się na:\n"
            "🌐 https://przystanekperfumy.pl/rejestracja/",
            reply_markup=MAIN_KB
        )
        return ST_IDLE

    ref_count = await get_ref_count(seller)
    ref_url = f"https://przystanekperfumy.pl/rejestracja/{seller.referral_code}/"
    bot_link = f"https://t.me/PrzystanekPsikPsikBot?start={seller.referral_code}"

    await update.message.reply_text(
        f"👤 *Panel polecającego*\n\n"
        f"Poziom: *{seller.get_level_display()}*\n"
        f"Kredyt: *{seller.credit} zł*\n"
        f"Polecenia: *{ref_count}*\n\n"
        f"🔗 *Link (strona):*\n`{ref_url}`\n\n"
        f"📱 *Link (Telegram):*\n`{bot_link}`\n\n"
        f"Kod: *{seller.referral_code}*\n\n"
        f"Za każde polecenie dostajesz *+20 zł kredytu*!",
        parse_mode="Markdown", reply_markup=MAIN_KB
    )
    return ST_IDLE

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(TOKEN).build()

    # Jeden ConversationHandler dla całego bota
    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", cmd_start),
            MessageHandler(filters.Regex("^🛍️ Przeglądaj perfumy$"), browse_start),
            MessageHandler(filters.Regex("^🧪 Quiz zapachowy$"), quiz_start),
            MessageHandler(filters.Regex("^🛒 Koszyk$"), show_cart),
            MessageHandler(filters.Regex("^📦 Moje zamówienia$"), my_orders),
            MessageHandler(filters.Regex("^🔗 Panel polecającego$"), seller_panel),
            MessageHandler(filters.Regex("^ℹ️ O sklepie$"), about),
        ],
        states={
            ST_IDLE: [
                MessageHandler(filters.Regex("^🛍️ Przeglądaj perfumy$"), browse_start),
                MessageHandler(filters.Regex("^🧪 Quiz zapachowy$"), quiz_start),
                MessageHandler(filters.Regex("^🛒 Koszyk$"), show_cart),
                MessageHandler(filters.Regex("^📦 Moje zamówienia$"), my_orders),
                MessageHandler(filters.Regex("^🔗 Panel polecającego$"), seller_panel),
                MessageHandler(filters.Regex("^ℹ️ O sklepie$"), about),
                CallbackQueryHandler(cart_callback, pattern="^do_(checkout|clear)$"),
            ],
            ST_BROWSE_GENDER: [
                CallbackQueryHandler(browse_gender, pattern="^g_"),
            ],
            ST_BROWSE_BRAND: [
                CallbackQueryHandler(browse_brand, pattern="^b_"),
            ],
            ST_BROWSE_LIST: [
                CallbackQueryHandler(browse_list),
            ],
            ST_QUIZ_INTENSITY: [
                CallbackQueryHandler(quiz_intensity, pattern="^qi_"),
            ],
            ST_QUIZ_CATEGORY: [
                CallbackQueryHandler(quiz_category, pattern="^qc_"),
            ],
            ST_QUIZ_OCCASION: [
                CallbackQueryHandler(quiz_occasion, pattern="^qo_"),
            ],
            ST_QUIZ_GENDER: [
                CallbackQueryHandler(quiz_gender, pattern="^qg_"),
            ],
            ST_CHECKOUT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, checkout_name),
            ],
            ST_CHECKOUT_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, checkout_phone),
            ],
            ST_CHECKOUT_ADDRESS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, checkout_address),
            ],
            ST_CHECKOUT_POSTAL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, checkout_postal),
            ],
            ST_CHECKOUT_CITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, checkout_city),
            ],
            ST_CHECKOUT_REFERRAL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, checkout_referral),
            ],
            ST_CHECKOUT_CONFIRM: [
                CallbackQueryHandler(checkout_confirm, pattern="^confirm_"),
                MessageHandler(filters.Regex("^(🛒|🛍️|🧪|📦|🔗|ℹ️)"), cmd_cancel),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cmd_cancel),
            CommandHandler("start", cmd_start),
        ],
        allow_reentry=True,
        per_message=False,
    )

    app.add_handler(conv)

    logger.info("🤖 Bot PsikPsik uruchomiony!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()