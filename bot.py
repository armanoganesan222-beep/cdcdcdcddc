import asyncio
import json
import urllib.request

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from config import BOT_TOKEN, ADMIN_ID

from database import (
    add_user,
    touch_user,

    get_stars_rate,
    set_stars_rate,
    get_stars_price,

    get_premium_price,
    set_premium_price,

    get_gram_markup,
    set_gram_markup,
    get_gram_balance,
    set_gram_balance,
    get_gram_enabled,
    set_gram_enabled,
    get_gram_payment_wallet,
    set_gram_payment_wallet,

    create_order,
    get_order,
    get_all_orders,
    set_receipt,
    complete_order,
    cancel_order,

    count_users,
    count_active_today,
    count_active_week,
    get_all_users,
    count_orders,
    count_completed_orders,

    is_admin,
    add_admin,
    remove_admin,
    get_admins,

    get_button_style,
    set_button_style
)


# =========================================================
# BOT
# =========================================================

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

dp = Dispatcher()


# =========================================================
# STATES
# =========================================================

class BuyState(StatesGroup):
    receiver = State()
    gram_amount = State()
    gram_wallet = State()
    receipt = State()


class AdminState(StatesGroup):
    stars_rate = State()
    premium_price = State()

    gram_markup = State()
    gram_balance = State()
    gram_wallet = State()

    broadcast = State()
    add_admin = State()
    remove_admin = State()

    button_color = State()


# =========================================================
# ADMIN
# =========================================================

def user_is_admin(user_id: int) -> bool:
    return (
        user_id == ADMIN_ID
        or is_admin(user_id)
    )


# =========================================================
# MAIN REPLY KEYBOARD
# =========================================================

def main_keyboard(user_id: int):
    rows = [
        [
            KeyboardButton(
                text="⭐ Купить Stars",
                style=get_button_style(
                    "stars"
                )
            )
        ],
        [
            KeyboardButton(
                text="💎 Premium",
                style=get_button_style(
                    "premium"
                )
            ),
            KeyboardButton(
                text="🔹 GRAM",
                style=get_button_style(
                    "gram"
                )
            )
        ],
        [
            KeyboardButton(
                text="💬 Наши Отзывы",
                style=get_button_style(
                    "reviews"
                )
            ),
            KeyboardButton(
                text="👤 Профиль",
                style=get_button_style(
                    "profile"
                )
            )
        ]
    ]

    if user_is_admin(user_id):
        rows.append([
            KeyboardButton(
                text="👑 Админ панель",
                style=get_button_style(
                    "admin"
                )
            )
        ])

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        is_persistent=True
    )


# =========================================================
# COLOR ADMIN KEYBOARD
# =========================================================

BUTTON_NAMES = {
    "stars": "⭐ Купить Stars",
    "premium": "💎 Premium",
    "gram": "🔹 GRAM",
    "reviews": "💬 Наши Отзывы",
    "profile": "👤 Профиль",
    "admin": "👑 Админ панель",
}


def color_name(style: str):
    return {
        "primary": "🔵 Синий",
        "success": "🟢 Зелёный",
        "danger": "🔴 Красный"
    }.get(
        style,
        "⚪ Обычный"
    )


def button_color_keyboard():
    rows = []

    for key, name in BUTTON_NAMES.items():
        rows.append([
            InlineKeyboardButton(
                text=f"{name} — {color_name(get_button_style(key))}",
                callback_data=f"color_{key}"
            )
        ])

    rows.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="admin_panel"
        )
    ])

    return InlineKeyboardMarkup(
        inline_keyboard=rows
    )


def color_choice_keyboard(button_key: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔵 Синий",
                    callback_data=f"setcolor_{button_key}_primary"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🟢 Зелёный",
                    callback_data=f"setcolor_{button_key}_success"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔴 Красный",
                    callback_data=f"setcolor_{button_key}_danger"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_colors"
                )
            ]
        ]
    )


# =========================================================
# INLINE KEYBOARDS
# =========================================================

def stars_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"⭐ 50 — {get_stars_price(50)} ₽",
                    callback_data="stars_50"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"⭐ 100 — {get_stars_price(100)} ₽",
                    callback_data="stars_100"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"⭐ 250 — {get_stars_price(250)} ₽",
                    callback_data="stars_250"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"⭐ 500 — {get_stars_price(500)} ₽",
                    callback_data="stars_500"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"⭐ 1000 — {get_stars_price(1000)} ₽",
                    callback_data="stars_1000"
                )
            ]
        ]
    )


def premium_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"💎 3 месяца — {get_premium_price(3)} ₽",
                    callback_data="premium_3"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"💎 6 месяцев — {get_premium_price(6)} ₽",
                    callback_data="premium_6"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"💎 12 месяцев — {get_premium_price(12)} ₽",
                    callback_data="premium_12"
                )
            ]
        ]
    )


def order_keyboard(order_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 Оплатить",
                    callback_data=f"pay_{order_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data="back_main"
                )
            ]
        ]
    )


def admin_order_keyboard(order_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Выполнить заказ",
                    callback_data=f"confirm_{order_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить заказ",
                    callback_data=f"cancel_{order_id}"
                )
            ]
        ]
    )


# =========================================================
# GRAM PRICE
# =========================================================

async def get_live_gram_price_rub():
    url = (
        "https://api.coingecko.com/api/v3/simple/price"
        "?ids=the-open-network"
        "&vs_currencies=rub"
    )

    def request():
        request_obj = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        with urllib.request.urlopen(
            request_obj,
            timeout=10
        ) as response:
            data = json.loads(
                response.read().decode("utf-8")
            )

        return float(
            data["the-open-network"]["rub"]
        )

    try:
        return await asyncio.to_thread(
            request
        )

    except Exception as error:
        print(
            f"Ошибка получения курса GRAM: {error}"
        )

        return None


async def get_gram_sale_price():
    market_price = await get_live_gram_price_rub()

    if market_price is None:
        return None, None

    markup = get_gram_markup()

    sale_price = (
        market_price
        * (1 + markup / 100)
    )

    return market_price, sale_price


# =========================================================
# TEXT
# =========================================================

def welcome_text(first_name: str):
    return f"""
🌟 <b>Добро пожаловать, {first_name}!</b>

━━━━━━━━━━━━━━━━━━

⭐ <b>Stars</b>
💎 <b>Premium</b>
🔹 <b>GRAM</b>

⚡ Быстрая обработка заказов
🔒 Проверка оплаты по чеку

━━━━━━━━━━━━━━━━━━

Выберите нужный товар ниже 👇
"""


def order_title(order):
    product_type = order[7]

    if product_type == "premium":
        return f"💎 Premium {order[8]} мес."

    if product_type == "gram":
        amount = order[10]

        if float(amount).is_integer():
            amount_text = str(int(amount))
        else:
            amount_text = f"{amount:g}"

        return f"🔹 {amount_text} GRAM"

    return f"⭐ {order[3]} Stars"


def order_text(order_id, order):
    recipient = order[2] or "Не указан"

    extra = ""

    if order[7] == "gram":
        extra = f"""
🔹 <b>Количество:</b> {order[10]:g} GRAM
💼 <b>Кошелёк:</b>
<code>{order[11]}</code>
"""

    return f"""
📦 <b>ЗАКАЗ #{order_id}</b>

━━━━━━━━━━━━━━━━━━

🛍 <b>Товар:</b> {order_title(order)}
👤 <b>Получатель:</b> {recipient}
💰 <b>К оплате:</b> {order[4]} ₽
{extra}
━━━━━━━━━━━━━━━━━━

💳 Нажмите <b>«Оплатить»</b>, получите реквизиты и после перевода отправьте чек.
"""


# =========================================================
# START
# =========================================================

@dp.message(Command("start"))
async def start_handler(message: Message):
    add_user(
        message.from_user.id,
        message.from_user.username or "",
        message.from_user.first_name or ""
    )

    await message.answer(
        "🔄",
        reply_markup=ReplyKeyboardRemove()
    )

    await message.answer(
        welcome_text(
            message.from_user.first_name
            or "Пользователь"
        ),
        reply_markup=main_keyboard(
            message.from_user.id
        )
    )


# =========================================================
# MAIN MENU
# =========================================================

@dp.message(F.text == "⭐ Купить Stars")
async def menu_stars(message: Message):
    await show_stars(message)


@dp.message(F.text == "💎 Premium")
async def menu_premium(message: Message):
    await show_premium(message)


@dp.message(F.text == "🔹 GRAM")
async def menu_gram(message: Message):
    await show_gram(message)


@dp.message(F.text == "💬 Наши Отзывы")
async def menu_reviews(message: Message):
    await message.answer(
        """
💬 <b>НАШИ ОТЗЫВЫ</b>

Отзывы покупателей можно посмотреть здесь 👇
""",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💬 Открыть отзывы",
                        url="https://t.me/armaaotz"
                    )
                ]
            ]
        )
    )


@dp.message(F.text == "👤 Профиль")
async def menu_profile(message: Message):
    username = (
        f"@{message.from_user.username}"
        if message.from_user.username
        else "Нет username"
    )

    await message.answer(
        f"""
👤 <b>МОЙ ПРОФИЛЬ</b>

━━━━━━━━━━━━━━━━━━

🆔 ID: <code>{message.from_user.id}</code>
👤 Username: {username}
📛 Имя: {message.from_user.first_name or "Не указано"}

━━━━━━━━━━━━━━━━━━
"""
    )


@dp.message(F.text == "👑 Админ панель")
async def menu_admin(message: Message):
    await send_admin_panel(message)


# =========================================================
# STARS
# =========================================================

async def show_stars(message: Message):
    touch_user(message.from_user.id)

    rate = get_stars_rate()

    await message.answer(
        f"""
⭐ <b>TELEGRAM STARS</b>

━━━━━━━━━━━━━━━━━━

💰 <b>Курс:</b> 1 ⭐ = {rate:.2f} ₽

Выберите количество Stars 👇
""",
        reply_markup=stars_keyboard()
    )


@dp.callback_query(F.data == "buy_stars")
async def buy_stars(callback: CallbackQuery):
    await show_stars(callback.message)
    await callback.answer()


@dp.callback_query(F.data.startswith("stars_"))
async def select_stars(
    callback: CallbackQuery,
    state: FSMContext
):
    stars = int(
        callback.data.split("_")[1]
    )

    price = get_stars_price(stars)

    if price <= 0:
        await callback.answer(
            "❌ Этот пакет недоступен.",
            show_alert=True
        )
        return

    await state.update_data(
        product_type="stars",
        stars=stars,
        price=price,
        premium_months=0
    )

    await callback.message.edit_text(
        f"""
⭐ <b>{stars} Stars</b> — <b>{price} ₽</b>

Кому отправить Stars?
""",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="👤 Купить себе",
                        callback_data=f"self_stars_{stars}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🎁 Подарить другому",
                        callback_data=f"gift_stars_{stars}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ Назад",
                        callback_data="buy_stars"
                    )
                ]
            ]
        )
    )

    await callback.answer()


# =========================================================
# PREMIUM
# =========================================================

async def show_premium(message: Message):
    touch_user(message.from_user.id)

    await message.answer(
        """
💎 <b>TELEGRAM PREMIUM</b>

━━━━━━━━━━━━━━━━━━

Выберите срок подписки 👇
""",
        reply_markup=premium_keyboard()
    )


@dp.callback_query(F.data == "buy_premium")
async def buy_premium(callback: CallbackQuery):
    await show_premium(callback.message)
    await callback.answer()


@dp.callback_query(F.data.startswith("premium_"))
async def select_premium(
    callback: CallbackQuery,
    state: FSMContext
):
    months = int(
        callback.data.split("_")[1]
    )

    price = get_premium_price(months)

    if price <= 0:
        await callback.answer(
            "❌ Этот тариф недоступен.",
            show_alert=True
        )
        return

    await state.update_data(
        product_type="premium",
        stars=0,
        price=price,
        premium_months=months
    )

    await callback.message.edit_text(
        f"""
💎 <b>Premium {months} мес.</b> — <b>{price} ₽</b>

Кому оформить Premium?
""",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="👤 Купить себе",
                        callback_data=f"self_premium_{months}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🎁 Подарить другому",
                        callback_data=f"gift_premium_{months}"
                    )
                ]
            ]
        )
    )

    await callback.answer()


# =========================================================
# GRAM
# =========================================================

async def show_gram(message: Message):
    touch_user(message.from_user.id)

    if not get_gram_enabled():
        await message.answer(
            """
🔹 <b>GRAM</b>

━━━━━━━━━━━━━━━━━━

❌ <b>GRAM сейчас закончились.</b>

Попробуйте позже.
"""
        )
        return

    balance = get_gram_balance()

    if balance <= 0:
        await message.answer(
            """
🔹 <b>GRAM</b>

━━━━━━━━━━━━━━━━━━

❌ <b>GRAM сейчас закончились.</b>

Попробуйте позже.
"""
        )
        return

    market_price, sale_price = (
        await get_gram_sale_price()
    )

    if market_price is None:
        await message.answer(
            """
🔹 <b>GRAM</b>

━━━━━━━━━━━━━━━━━━

⚠️ Не удалось получить текущий курс.

Попробуйте через несколько секунд.
"""
        )
        return

    markup = get_gram_markup()

    await message.answer(
        f"""
🔹 <b>GRAM</b>

━━━━━━━━━━━━━━━━━━

📈 Рыночный курс:
<b>1 GRAM ≈ {market_price:.2f} ₽</b>

➕ Наценка:
<b>{markup:.2f}%</b>

💰 Цена для покупки:
<b>1 GRAM ≈ {sale_price:.2f} ₽</b>

📦 В наличии:
<b>{balance:g} GRAM</b>

━━━━━━━━━━━━━━━━━━

Нажмите кнопку ниже, чтобы купить GRAM.
""",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔹 Купить GRAM",
                        callback_data="gram_buy"
                    )
                ]
            ]
        )
    )


@dp.callback_query(F.data == "gram_buy")
async def gram_buy(
    callback: CallbackQuery,
    state: FSMContext
):
    if not get_gram_enabled():
        await callback.answer(
            "❌ GRAM закончились.",
            show_alert=True
        )
        return

    balance = get_gram_balance()

    if balance <= 0:
        await callback.answer(
            "❌ GRAM закончились.",
            show_alert=True
        )
        return

    await state.set_state(
        BuyState.gram_amount
    )

    await callback.message.edit_text(
        f"""
🔹 <b>ПОКУПКА GRAM</b>

━━━━━━━━━━━━━━━━━━

📦 Доступно:
<b>{balance:g} GRAM</b>

Введите количество GRAM.

Например:
<code>5</code>
<code>10.5</code>
"""
    )

    await callback.answer()


@dp.message(BuyState.gram_amount)
async def gram_amount(
    message: Message,
    state: FSMContext
):
    if not message.text:
        await message.answer(
            "❌ Введите количество GRAM числом."
        )
        return

    try:
        amount = float(
            message.text.strip().replace(",", ".")
        )

        if amount <= 0:
            raise ValueError

    except Exception:
        await message.answer(
            "❌ Введите корректное количество GRAM.\n\n"
            "Например: <code>10</code> или <code>10.5</code>"
        )
        return

    balance = get_gram_balance()

    if amount > balance:
        await message.answer(
            f"""
❌ <b>Недостаточно GRAM.</b>

📦 Сейчас доступно:
<b>{balance:g} GRAM</b>

Вы не можете купить больше остатка.
"""
        )
        return

    market_price, sale_price = (
        await get_gram_sale_price()
    )

    if sale_price is None:
        await message.answer(
            "⚠️ Не удалось получить текущий курс. Попробуйте ещё раз."
        )
        return

    total = round(
        amount * sale_price
    )

    await state.update_data(
        product_type="gram",
        stars=0,
        premium_months=0,
        gram_amount=amount,
        price=total
    )

    await state.set_state(
        BuyState.gram_wallet
    )

    await message.answer(
        f"""
🔹 <b>ВАШ ЗАКАЗ</b>

━━━━━━━━━━━━━━━━━━

🔹 Количество:
<b>{amount:g} GRAM</b>

💰 Цена:
<b>{total} ₽</b>

📈 Цена за 1 GRAM:
<b>{sale_price:.2f} ₽</b>

━━━━━━━━━━━━━━━━━━

💼 Теперь отправьте <b>адрес кошелька</b>, на который нужно отправить GRAM.
"""
    )


@dp.message(BuyState.gram_wallet)
async def gram_wallet(
    message: Message,
    state: FSMContext
):
    if not message.text:
        await message.answer(
            "❌ Отправьте адрес кошелька текстом."
        )
        return

    wallet = message.text.strip()

    if len(wallet) < 10:
        await message.answer(
            "❌ Адрес кошелька выглядит слишком коротким."
        )
        return

    data = await state.get_data()

    amount = float(
        data["gram_amount"]
    )

    balance = get_gram_balance()

    if amount > balance:
        await state.clear()

        await message.answer(
            """
❌ Пока вы вводили адрес, остаток GRAM изменился.

Пожалуйста, создайте заказ заново.
"""
        )
        return

    order_id = create_order(
        message.from_user.id,
        message.from_user.username or "",
        wallet,
        0,
        data["price"],
        "gram",
        0,
        amount,
        wallet
    )

    if not order_id:
        await state.clear()

        await message.answer(
            """
❌ Не удалось создать заказ.

Возможно, нужное количество GRAM уже купили.
Попробуйте создать заказ заново.
"""
        )
        return

    await state.clear()

    await message.answer(
        order_text(
            order_id,
            get_order(order_id)
        ),
        reply_markup=order_keyboard(order_id)
    )


# =========================================================
# SELF ORDER
# =========================================================

async def create_self_order(
    callback: CallbackQuery,
    state: FSMContext
):
    data = await state.get_data()

    username = (
        callback.from_user.username
        or ""
    )

    receiver = (
        f"@{username}"
        if username
        else f"Telegram ID {callback.from_user.id}"
    )

    order_id = create_order(
        callback.from_user.id,
        username,
        receiver,
        data["stars"],
        data["price"],
        data["product_type"],
        data["premium_months"]
    )

    if not order_id:
        await callback.answer(
            "❌ Не удалось создать заказ.",
            show_alert=True
        )
        return

    await state.clear()

    await callback.message.edit_text(
        order_text(
            order_id,
            get_order(order_id)
        ),
        reply_markup=order_keyboard(order_id)
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("self_stars_"))
async def self_stars(
    callback: CallbackQuery,
    state: FSMContext
):
    stars = int(
        callback.data.split("_")[2]
    )

    await state.update_data(
        product_type="stars",
        stars=stars,
        premium_months=0,
        price=get_stars_price(stars)
    )

    await create_self_order(
        callback,
        state
    )


@dp.callback_query(F.data.startswith("self_premium_"))
async def self_premium(
    callback: CallbackQuery,
    state: FSMContext
):
    months = int(
        callback.data.split("_")[2]
    )

    await state.update_data(
        product_type="premium",
        stars=0,
        premium_months=months,
        price=get_premium_price(months)
    )

    await create_self_order(
        callback,
        state
    )


# =========================================================
# GIFT
# =========================================================

@dp.callback_query(F.data.startswith("gift_stars_"))
async def gift_stars(
    callback: CallbackQuery,
    state: FSMContext
):
    stars = int(
        callback.data.split("_")[2]
    )

    await state.update_data(
        product_type="stars",
        stars=stars,
        premium_months=0,
        price=get_stars_price(stars)
    )

    await state.set_state(
        BuyState.receiver
    )

    await callback.message.edit_text(
        """
🎁 <b>Введите username получателя:</b>

Например:
<code>@username</code>
"""
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("gift_premium_"))
async def gift_premium(
    callback: CallbackQuery,
    state: FSMContext
):
    months = int(
        callback.data.split("_")[2]
    )

    await state.update_data(
        product_type="premium",
        stars=0,
        premium_months=months,
        price=get_premium_price(months)
    )

    await state.set_state(
        BuyState.receiver
    )

    await callback.message.edit_text(
        """
🎁 <b>Введите username получателя:</b>

Например:
<code>@username</code>
"""
    )

    await callback.answer()


@dp.message(BuyState.receiver)
async def receiver(
    message: Message,
    state: FSMContext
):
    if (
        not message.text
        or not message.text.strip().startswith("@")
    ):
        await message.answer(
            """
❌ Username должен начинаться с <b>@</b>.

Пример:
<code>@username</code>
"""
        )
        return

    data = await state.get_data()

    username = (
        message.from_user.username
        or ""
    )

    order_id = create_order(
        message.from_user.id,
        username,
        message.text.strip(),
        data["stars"],
        data["price"],
        data["product_type"],
        data["premium_months"]
    )

    if not order_id:
        await state.clear()

        await message.answer(
            "❌ Не удалось создать заказ."
        )
        return

    await state.clear()

    await message.answer(
        order_text(
            order_id,
            get_order(order_id)
        ),
        reply_markup=order_keyboard(order_id)
    )


# =========================================================
# BACK MAIN
# =========================================================

@dp.callback_query(F.data == "back_main")
async def back_main(
    callback: CallbackQuery,
    state: FSMContext
):
    await state.clear()

    await callback.message.answer(
        welcome_text(
            callback.from_user.first_name
            or "Пользователь"
        ),
        reply_markup=main_keyboard(
            callback.from_user.id
        )
    )

    await callback.answer()


# =========================================================
# PAYMENT
# =========================================================

@dp.callback_query(F.data.startswith("pay_"))
async def payment(callback: CallbackQuery):
    order_id = int(
        callback.data.split("_")[1]
    )

    order = get_order(order_id)

    if (
        not order
        or order[0] != callback.from_user.id
    ):
        await callback.answer(
            "❌ Заказ не найден.",
            show_alert=True
        )
        return

    if order[5] == "completed":
        await callback.answer(
            "✅ Заказ уже выполнен.",
            show_alert=True
        )
        return

    if order[5] == "cancelled":
        await callback.answer(
            "❌ Заказ отменён.",
            show_alert=True
        )
        return

    if order[7] == "gram":
        wallet = get_gram_payment_wallet()

        if not wallet:
            await callback.answer(
                "❌ Адрес для оплаты GRAM ещё не настроен.",
                show_alert=True
            )
            return

        payment_text = f"""
🔹 <b>ОПЛАТА GRAM</b>

━━━━━━━━━━━━━━━━━━

📦 <b>{order[10]:g} GRAM</b>
💰 <b>Сумма: {order[4]} ₽</b>

━━━━━━━━━━━━━━━━━━

💼 <b>РЕКВИЗИТЫ ДЛЯ ОПЛАТЫ</b>

<code>{wallet}</code>

━━━━━━━━━━━━━━━━━━

После перевода нажмите кнопку ниже и отправьте <b>фото чека</b>.

⚠️ GRAM будут отправлены после проверки оплаты.
"""

    else:
        payment_text = f"""
💳 <b>ОПЛАТА ЗАКАЗА #{order_id}</b>

━━━━━━━━━━━━━━━━━━

🛍 <b>{order_title(order)}</b>
💰 <b>Сумма: {order[4]} ₽</b>

━━━━━━━━━━━━━━━━━━

🏦 <b>РЕКВИЗИТЫ</b>

📱 <b>+79385559750</b>
🏦 <b>Сбербанк</b>
👤 <b>Арман А.</b>
💳 <code>2202 2082 7431 6950</code>

━━━━━━━━━━━━━━━━━━

После перевода нажмите кнопку ниже и отправьте <b>фото чека</b>.
"""

    await callback.message.edit_text(
        payment_text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Я оплатил",
                        callback_data=f"paid_{order_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ Назад к заказу",
                        callback_data=f"order_{order_id}"
                    )
                ]
            ]
        )
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("order_"))
async def order_back(callback: CallbackQuery):
    order_id = int(
        callback.data.split("_")[1]
    )

    order = get_order(order_id)

    if (
        not order
        or order[0] != callback.from_user.id
    ):
        await callback.answer(
            "❌ Заказ не найден.",
            show_alert=True
        )
        return

    await callback.message.edit_text(
        order_text(
            order_id,
            order
        ),
        reply_markup=order_keyboard(
            order_id
        )
    )

    await callback.answer()


# =========================================================
# RECEIPT
# =========================================================

@dp.callback_query(F.data.startswith("paid_"))
async def paid(
    callback: CallbackQuery,
    state: FSMContext
):
    order_id = int(
        callback.data.split("_")[1]
    )

    order = get_order(order_id)

    if (
        not order
        or order[0] != callback.from_user.id
    ):
        await callback.answer(
            "❌ Заказ не найден.",
            show_alert=True
        )
        return

    if order[5] == "completed":
        await callback.answer(
            "✅ Заказ уже выполнен.",
            show_alert=True
        )
        return

    if order[5] == "cancelled":
        await callback.answer(
            "❌ Заказ отменён.",
            show_alert=True
        )
        return

    if order[9]:
        await callback.answer(
            "📸 Чек уже отправлен администраторам.",
            show_alert=True
        )
        return

    await state.clear()

    await state.update_data(
        receipt_order_id=order_id
    )

    await state.set_state(
        BuyState.receipt
    )

    await callback.message.edit_text(
        f"""
🧾 <b>ЧЕК ПО ЗАКАЗУ #{order_id}</b>

Отправьте сюда <b>фото или скриншот чека об оплате</b>.

⚠️ Без чека заказ не будет передан на проверку.
"""
    )

    await callback.answer()


@dp.message(BuyState.receipt)
async def receive_receipt(
    message: Message,
    state: FSMContext
):
    data = await state.get_data()

    order_id = data.get(
        "receipt_order_id"
    )

    order = (
        get_order(order_id)
        if order_id
        else None
    )

    if (
        not order
        or order[0] != message.from_user.id
    ):
        await state.clear()

        await message.answer(
            "❌ Заказ не найден."
        )

        return

    if not message.photo:
        await message.answer(
            "❌ Отправьте именно <b>фото или скриншот</b> чека."
        )
        return

    file_id = message.photo[-1].file_id

    set_receipt(
        order_id,
        file_id
    )

    await state.clear()

    buyer = (
        f"@{order[1]}"
        if order[1]
        else "Не указан"
    )

    admin_text = f"""
🚨 <b>НОВЫЙ ЗАКАЗ #{order_id}</b>

━━━━━━━━━━━━━━━━━━

👤 <b>Покупатель:</b> {buyer}
🆔 <b>ID:</b> <code>{order[0]}</code>
🛍 <b>Товар:</b> {order_title(order)}
💰 <b>Сумма:</b> {order[4]} ₽
🎯 <b>Получатель:</b> {order[2]}
"""

    if order[7] == "gram":
        admin_text += f"""
🔹 <b>GRAM:</b> {order[10]:g}
💼 <b>Кошелёк:</b>
<code>{order[11]}</code>
"""

    admin_text += """
━━━━━━━━━━━━━━━━━━

🧾 <b>Чек об оплате прикреплён ниже.</b>

🔎 Проверьте оплату и выберите действие.
"""

    admins = set(
        get_admins()
    )

    admins.add(
        ADMIN_ID
    )

    for admin_id in admins:
        try:
            await bot.send_photo(
                admin_id,
                file_id,
                caption=admin_text,
                reply_markup=admin_order_keyboard(
                    order_id
                )
            )

        except Exception as error:
            print(
                f"Ошибка отправки чека админу "
                f"{admin_id}: {error}"
            )

    await message.answer(
        f"""
✅ <b>ЧЕК ПОЛУЧЕН</b>

Заказ <b>#{order_id}</b> передан администрации.

⏳ Ожидайте проверки оплаты.
""",
        reply_markup=main_keyboard(
            message.from_user.id
        )
    )


# =========================================================
# ADMIN PANEL
# =========================================================

def admin_panel_keyboard(user_id: int):
    buttons = [
        [
            InlineKeyboardButton(
                text="📦 Заказы",
                callback_data="admin_orders"
            ),
            InlineKeyboardButton(
                text="📊 Статистика",
                callback_data="admin_stats"
            )
        ],
        [
            InlineKeyboardButton(
                text="⭐ Stars",
                callback_data="admin_stars_rate"
            ),
            InlineKeyboardButton(
                text="💎 Premium",
                callback_data="admin_premium_prices"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔹 GRAM",
                callback_data="admin_gram"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎨 Цвета кнопок",
                callback_data="admin_colors"
            )
        ],
        [
            InlineKeyboardButton(
                text="👥 Пользователи",
                callback_data="admin_users"
            )
        ],
        [
            InlineKeyboardButton(
                text="📢 Рассылка",
                callback_data="admin_broadcast"
            )
        ]
    ]

    if user_id == ADMIN_ID:
        buttons.append([
            InlineKeyboardButton(
                text="🛡 Администраторы",
                callback_data="admin_manage"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="back_main"
        )
    ])

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


async def send_admin_panel(message: Message):
    if not user_is_admin(
        message.from_user.id
    ):
        await message.answer(
            "❌ У вас нет доступа."
        )
        return

    rate = get_stars_rate()

    gram_status = (
        "🟢 Включён"
        if get_gram_enabled()
        else "🔴 Выключен"
    )

    await message.answer(
        f"""
👑 <b>АДМИН ПАНЕЛЬ</b>

━━━━━━━━━━━━━━━━━━

⭐ Stars:
<b>1 ⭐ = {rate:.2f} ₽</b>

🔹 GRAM:
<b>{gram_status}</b>

📦 Остаток:
<b>{get_gram_balance():g} GRAM</b>

➕ Наценка:
<b>{get_gram_markup():.2f}%</b>

━━━━━━━━━━━━━━━━━━

Выберите раздел:
""",
        reply_markup=admin_panel_keyboard(
            message.from_user.id
        )
    )


@dp.callback_query(F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery):
    if not user_is_admin(
        callback.from_user.id
    ):
        await callback.answer(
            "❌ У вас нет доступа.",
            show_alert=True
        )
        return

    rate = get_stars_rate()

    gram_status = (
        "🟢 Включён"
        if get_gram_enabled()
        else "🔴 Выключен"
    )

    await callback.message.edit_text(
        f"""
👑 <b>АДМИН ПАНЕЛЬ</b>

━━━━━━━━━━━━━━━━━━

⭐ Stars:
<b>1 ⭐ = {rate:.2f} ₽</b>

🔹 GRAM:
<b>{gram_status}</b>

📦 Остаток:
<b>{get_gram_balance():g} GRAM</b>

➕ Наценка:
<b>{get_gram_markup():.2f}%</b>

━━━━━━━━━━━━━━━━━━
""",
        reply_markup=admin_panel_keyboard(
            callback.from_user.id
        )
    )

    await callback.answer()


# =========================================================
# BUTTON COLORS
# =========================================================

@dp.callback_query(F.data == "admin_colors")
async def admin_colors(
    callback: CallbackQuery
):
    if not user_is_admin(
        callback.from_user.id
    ):
        await callback.answer(
            "❌ У вас нет доступа.",
            show_alert=True
        )
        return

    await callback.message.edit_text(
        """
🎨 <b>ЦВЕТА КНОПОК</b>

Здесь можно изменить цвет каждой кнопки
главного меню отдельно.

🔵 Синий
🟢 Зелёный
🔴 Красный

Выберите кнопку:
""",
        reply_markup=button_color_keyboard()
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("color_"))
async def select_button_color(
    callback: CallbackQuery
):
    if not user_is_admin(
        callback.from_user.id
    ):
        await callback.answer(
            "❌ У вас нет доступа.",
            show_alert=True
        )
        return

    button_key = callback.data.split(
        "_",
        1
    )[1]

    if button_key not in BUTTON_NAMES:
        await callback.answer(
            "❌ Кнопка не найдена.",
            show_alert=True
        )
        return

    current = get_button_style(
        button_key
    )

    await callback.message.edit_text(
        f"""
🎨 <b>ЦВЕТ КНОПКИ</b>

Кнопка:
<b>{BUTTON_NAMES[button_key]}</b>

Сейчас:
<b>{color_name(current)}</b>

Выберите новый цвет:
""",
        reply_markup=color_choice_keyboard(
            button_key
        )
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("setcolor_"))
async def set_button_color(
    callback: CallbackQuery
):
    if not user_is_admin(
        callback.from_user.id
    ):
        await callback.answer(
            "❌ У вас нет доступа.",
            show_alert=True
        )
        return

    parts = callback.data.split("_")

    if len(parts) != 3:
        await callback.answer(
            "❌ Ошибка.",
            show_alert=True
        )
        return

    button_key = parts[1]
    style = parts[2]

    if button_key not in BUTTON_NAMES:
        await callback.answer(
            "❌ Кнопка не найдена.",
            show_alert=True
        )
        return

    if style not in (
        "primary",
        "success",
        "danger"
    ):
        await callback.answer(
            "❌ Цвет недоступен.",
            show_alert=True
        )
        return

    set_button_style(
        button_key,
        style
    )

    await callback.answer(
        f"✅ Цвет изменён: {color_name(style)}"
    )

    await admin_colors(
        callback
    )


# =========================================================
# STARS RATE
# =========================================================

@dp.callback_query(F.data == "admin_stars_rate")
async def admin_stars_rate(
    callback: CallbackQuery,
    state: FSMContext
):
    if not user_is_admin(
        callback.from_user.id
    ):
        return

    rate = get_stars_rate()

    await state.set_state(
        AdminState.stars_rate
    )

    await callback.message.edit_text(
        f"""
💰 <b>КУРС TELEGRAM STARS</b>

━━━━━━━━━━━━━━━━━━

⭐ <b>1 Star = {rate:.2f} ₽</b>

Введите новый курс:

Например:
<code>1.25</code>
"""
    )

    await callback.answer()


@dp.message(AdminState.stars_rate)
async def save_stars_rate(
    message: Message,
    state: FSMContext
):
    if not user_is_admin(
        message.from_user.id
    ):
        return

    try:
        rate = float(
            message.text.strip().replace(
                ",",
                "."
            )
        )

        if rate <= 0:
            raise ValueError

    except Exception:
        await message.answer(
            "❌ Введите положительный курс.\n\n"
            "Пример: <code>1.25</code>"
        )
        return

    set_stars_rate(
        rate
    )

    await state.clear()

    await message.answer(
        f"""
✅ <b>КУРС STARS ИЗМЕНЁН</b>

⭐ 1 Star = <b>{rate:.2f} ₽</b>

50 ⭐ = {get_stars_price(50)} ₽
100 ⭐ = {get_stars_price(100)} ₽
250 ⭐ = {get_stars_price(250)} ₽
500 ⭐ = {get_stars_price(500)} ₽
1000 ⭐ = {get_stars_price(1000)} ₽
""",
        reply_markup=admin_panel_keyboard(
            message.from_user.id
        )
    )


# =========================================================
# PREMIUM ADMIN
# =========================================================

@dp.callback_query(F.data == "admin_premium_prices")
async def admin_premium_prices(
    callback: CallbackQuery
):
    if not user_is_admin(
        callback.from_user.id
    ):
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"💎 3 месяца — {get_premium_price(3)} ₽",
                    callback_data="editpremium_3"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"💎 6 месяцев — {get_premium_price(6)} ₽",
                    callback_data="editpremium_6"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"💎 12 месяцев — {get_premium_price(12)} ₽",
                    callback_data="editpremium_12"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_panel"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        """
💎 <b>ЦЕНЫ TELEGRAM PREMIUM</b>

Выберите срок для изменения цены:
""",
        reply_markup=keyboard
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("editpremium_"))
async def edit_premium_price(
    callback: CallbackQuery,
    state: FSMContext
):
    if not user_is_admin(
        callback.from_user.id
    ):
        return

    months = int(
        callback.data.split("_")[1]
    )

    await state.update_data(
        months=months
    )

    await state.set_state(
        AdminState.premium_price
    )

    await callback.message.edit_text(
        f"""
💎 <b>Premium {months} месяцев</b>

Сейчас:
<b>{get_premium_price(months)} ₽</b>

Введите новую цену числом:
"""
    )

    await callback.answer()


@dp.message(AdminState.premium_price)
async def save_premium_price(
    message: Message,
    state: FSMContext
):
    if not user_is_admin(
        message.from_user.id
    ):
        return

    try:
        price = int(
            message.text.strip()
        )

        if price <= 0:
            raise ValueError

    except Exception:
        await message.answer(
            "❌ Введите положительную цену числом."
        )
        return

    data = await state.get_data()

    set_premium_price(
        data["months"],
        price
    )

    await state.clear()

    await message.answer(
        f"""
✅ Цена Premium {data["months"]} мес.
изменена на <b>{price} ₽</b>.
""",
        reply_markup=admin_panel_keyboard(
            message.from_user.id
        )
    )


# =========================================================
# GRAM ADMIN
# =========================================================

def gram_admin_keyboard():
    status_text = (
        "🟢 GRAM включён"
        if get_gram_enabled()
        else "🔴 GRAM выключен"
    )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📈 Наценка",
                    callback_data="gram_markup"
                ),
                InlineKeyboardButton(
                    text="📦 Остаток",
                    callback_data="gram_balance"
                )
            ],
            [
                InlineKeyboardButton(
                    text=status_text,
                    callback_data="gram_toggle"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💼 Кошелёк оплаты",
                    callback_data="gram_wallet"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_panel"
                )
            ]
        ]
    )


@dp.callback_query(F.data == "admin_gram")
async def admin_gram(
    callback: CallbackQuery
):
    if not user_is_admin(
        callback.from_user.id
    ):
        return

    market_price, sale_price = (
        await get_gram_sale_price()
    )

    if market_price is None:
        price_text = "⚠️ Курс сейчас недоступен"
    else:
        price_text = (
            f"📈 Рыночный курс: "
            f"<b>{market_price:.2f} ₽</b>\n"
            f"💰 Цена продажи: "
            f"<b>{sale_price:.2f} ₽</b>"
        )

    await callback.message.edit_text(
        f"""
🔹 <b>УПРАВЛЕНИЕ GRAM</b>

━━━━━━━━━━━━━━━━━━

{price_text}

➕ Наценка:
<b>{get_gram_markup():.2f}%</b>

📦 Остаток:
<b>{get_gram_balance():g} GRAM</b>

💼 Кошелёк оплаты:
<code>{get_gram_payment_wallet() or "Не указан"}</code>

━━━━━━━━━━━━━━━━━━
""",
        reply_markup=gram_admin_keyboard()
    )

    await callback.answer()


@dp.callback_query(F.data == "gram_toggle")
async def gram_toggle(
    callback: CallbackQuery
):
    if not user_is_admin(
        callback.from_user.id
    ):
        return

    new_status = not get_gram_enabled()

    set_gram_enabled(
        new_status
    )

    await callback.answer(
        "🟢 GRAM включён"
        if new_status
        else "🔴 GRAM выключен"
    )

    await admin_gram(
        callback
    )


@dp.callback_query(F.data == "gram_markup")
async def gram_markup(
    callback: CallbackQuery,
    state: FSMContext
):
    if not user_is_admin(
        callback.from_user.id
    ):
        return

    await state.set_state(
        AdminState.gram_markup
    )

    await callback.message.edit_text(
        f"""
📈 <b>НАЦЕНКА GRAM</b>

Сейчас:
<b>{get_gram_markup():.2f}%</b>

Введите процент наценки.

Например:
<code>5</code>
<code>7.5</code>
<code>10</code>
"""
    )

    await callback.answer()


@dp.message(AdminState.gram_markup)
async def save_gram_markup(
    message: Message,
    state: FSMContext
):
    if not user_is_admin(
        message.from_user.id
    ):
        return

    try:
        markup = float(
            message.text.strip().replace(
                ",",
                "."
            )
        )

        if markup < 0:
            raise ValueError

    except Exception:
        await message.answer(
            "❌ Введите число 0 или больше.\n"
            "Например: <code>7.5</code>"
        )
        return

    set_gram_markup(
        markup
    )

    await state.clear()

    await message.answer(
        f"""
✅ <b>НАЦЕНКА ИЗМЕНЕНА</b>

Теперь наценка:
<b>{markup:.2f}%</b>
""",
        reply_markup=admin_panel_keyboard(
            message.from_user.id
        )
    )


@dp.callback_query(F.data == "gram_balance")
async def gram_balance(
    callback: CallbackQuery,
    state: FSMContext
):
    if not user_is_admin(
        callback.from_user.id
    ):
        return

    await state.set_state(
        AdminState.gram_balance
    )

    await callback.message.edit_text(
        f"""
📦 <b>ОСТАТОК GRAM</b>

Сейчас:
<b>{get_gram_balance():g} GRAM</b>

Введите новое количество GRAM.

Например:
<code>100</code>
<code>250.5</code>

Если поставить <code>0</code>,
покупка GRAM автоматически будет недоступна.
"""
    )

    await callback.answer()


@dp.message(AdminState.gram_balance)
async def save_gram_balance(
    message: Message,
    state: FSMContext
):
    if not user_is_admin(
        message.from_user.id
    ):
        return

    try:
        balance = float(
            message.text.strip().replace(
                ",",
                "."
            )
        )

        if balance < 0:
            raise ValueError

    except Exception:
        await message.answer(
            "❌ Введите число 0 или больше."
        )
        return

    set_gram_balance(
        balance
    )

    if balance > 0:
        set_gram_enabled(True)
    else:
        set_gram_enabled(False)

    await state.clear()

    await message.answer(
        f"""
✅ <b>ОСТАТОК GRAM ИЗМЕНЁН</b>

📦 Сейчас:
<b>{balance:g} GRAM</b>

{"🟢 Продажа включена." if balance > 0 else "🔴 Продажа выключена."}
""",
        reply_markup=admin_panel_keyboard(
            message.from_user.id
        )
    )


@dp.callback_query(F.data == "gram_wallet")
async def gram_wallet_admin(
    callback: CallbackQuery,
    state: FSMContext
):
    if not user_is_admin(
        callback.from_user.id
    ):
        return

    await state.set_state(
        AdminState.gram_wallet
    )

    await callback.message.edit_text(
        f"""
💼 <b>КОШЕЛЁК GRAM</b>

Текущий:

<code>{get_gram_payment_wallet() or "Не указан"}</code>

Отправьте новый адрес кошелька.
"""
    )

    await callback.answer()


@dp.message(AdminState.gram_wallet)
async def save_gram_wallet(
    message: Message,
    state: FSMContext
):
    if not user_is_admin(
        message.from_user.id
    ):
        return

    wallet = (
        message.text.strip()
        if message.text
        else ""
    )

    if len(wallet) < 10:
        await message.answer(
            "❌ Адрес кошелька выглядит слишком коротким."
        )
        return

    set_gram_payment_wallet(
        wallet
    )

    await state.clear()

    await message.answer(
        """
✅ <b>КОШЕЛЁК GRAM СОХРАНЁН</b>
""",
        reply_markup=admin_panel_keyboard(
            message.from_user.id
        )
    )


# =========================================================
# ORDERS
# =========================================================

@dp.callback_query(F.data == "admin_orders")
async def admin_orders(
    callback: CallbackQuery
):
    if not user_is_admin(
        callback.from_user.id
    ):
        return

    orders = get_all_orders()[:15]

    if not orders:
        text = """
📦 <b>ЗАКАЗЫ</b>

📭 Заказов пока нет.
"""
    else:
        text = (
            "📦 <b>ПОСЛЕДНИЕ ЗАКАЗЫ</b>\n\n"
        )

        for order in orders:
            status = {
                "waiting": "⏳ Ожидает",
                "completed": "✅ Выполнен",
                "cancelled": "❌ Отменён"
            }.get(
                order[6],
                order[6]
            )

            receipt = (
                "🧾 Чек есть"
                if order[10]
                else "Без чека"
            )

            text += (
                f"🆔 <b>#{order[0]}</b>\n"
                f"🛍 {order_title(order)}\n"
                f"💰 {order[5]} ₽\n"
                f"🎯 {order[3]}\n"
                f"📌 {status} · {receipt}\n\n"
                f"━━━━━━━━━━━━\n\n"
            )

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⬅️ Назад",
                        callback_data="admin_panel"
                    )
                ]
            ]
        )
    )

    await callback.answer()


# =========================================================
# STATISTICS
# =========================================================

@dp.callback_query(F.data == "admin_stats")
async def admin_stats(
    callback: CallbackQuery
):
    if not user_is_admin(
        callback.from_user.id
    ):
        return

    await callback.message.edit_text(
        f"""
📊 <b>СТАТИСТИКА</b>

━━━━━━━━━━━━━━━━━━

👥 Пользователей:
<b>{count_users()}</b>

🟢 Активных сегодня:
<b>{count_active_today()}</b>

📅 Активных за 7 дней:
<b>{count_active_week()}</b>

📦 Всего заказов:
<b>{count_orders()}</b>

✅ Выполнено:
<b>{count_completed_orders()}</b>

⏳ В обработке:
<b>{max(0, count_orders() - count_completed_orders())}</b>
""",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⬅️ Назад",
                        callback_data="admin_panel"
                    )
                ]
            ]
        )
    )

    await callback.answer()


# =========================================================
# USERS
# =========================================================

@dp.callback_query(F.data == "admin_users")
async def admin_users(
    callback: CallbackQuery
):
    if not user_is_admin(
        callback.from_user.id
    ):
        return

    users = get_all_users()

    text = (
        f"👥 <b>ПОЛЬЗОВАТЕЛИ</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 Всего: <b>{len(users)}</b>\n"
        f"🟢 Сегодня: <b>{count_active_today()}</b>\n"
        f"📅 За 7 дней: <b>{count_active_week()}</b>\n\n"
        f"<b>Последние активные:</b>\n"
    )

    for (
        user_id,
        username,
        first_name,
        last_activity
    ) in users[:30]:

        name = (
            f"@{username}"
            if username
            else f"{first_name or 'Без username'}"
        )

        text += (
            f"• {name} — "
            f"<code>{user_id}</code>\n"
        )

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⬅️ Назад",
                        callback_data="admin_panel"
                    )
                ]
            ]
        )
    )

    await callback.answer()


# =========================================================
# BROADCAST
# =========================================================

@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(
    callback: CallbackQuery,
    state: FSMContext
):
    if not user_is_admin(
        callback.from_user.id
    ):
        return

    await state.set_state(
        AdminState.broadcast
    )

    await callback.message.edit_text(
        """
📢 <b>РАССЫЛКА</b>

Отправьте текст рассылки.

Для отмены:
<code>отмена</code>
"""
    )

    await callback.answer()


@dp.message(AdminState.broadcast)
async def send_broadcast(
    message: Message,
    state: FSMContext
):
    if not user_is_admin(
        message.from_user.id
    ):
        return

    if (
        message.text
        and message.text.lower() == "отмена"
    ):
        await state.clear()

        await message.answer(
            "❌ Рассылка отменена.",
            reply_markup=admin_panel_keyboard(
                message.from_user.id
            )
        )

        return

    users = get_all_users()

    sent = 0
    failed = 0

    for user in users:
        try:
            await bot.send_message(
                user[0],
                message.text or " "
            )

            sent += 1

            await asyncio.sleep(
                0.05
            )

        except Exception:
            failed += 1

    await state.clear()

    await message.answer(
        f"""
📢 <b>РАССЫЛКА ЗАВЕРШЕНА</b>

✅ Отправлено: {sent}
❌ Не доставлено: {failed}
""",
        reply_markup=admin_panel_keyboard(
            message.from_user.id
        )
    )


# =========================================================
# ADMIN MANAGEMENT
# =========================================================

@dp.callback_query(F.data == "admin_manage")
async def admin_manage(
    callback: CallbackQuery
):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "❌ Только владелец.",
            show_alert=True
        )
        return

    await callback.message.edit_text(
        """
🛡 <b>АДМИНИСТРАТОРЫ</b>

Управление доступом к админ-панели.
""",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="➕ Добавить админа",
                        callback_data="admin_add"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="➖ Удалить админа",
                        callback_data="admin_remove"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📋 Список админов",
                        callback_data="admin_list"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ Назад",
                        callback_data="admin_panel"
                    )
                ]
            ]
        )
    )

    await callback.answer()


@dp.callback_query(F.data == "admin_add")
async def admin_add(
    callback: CallbackQuery,
    state: FSMContext
):
    if callback.from_user.id != ADMIN_ID:
        return

    await state.set_state(
        AdminState.add_admin
    )

    await callback.message.edit_text(
        """
➕ <b>ДОБАВЛЕНИЕ АДМИНА</b>

Отправьте Telegram ID пользователя.
"""
    )

    await callback.answer()


@dp.message(AdminState.add_admin)
async def save_admin(
    message: Message,
    state: FSMContext
):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        user_id = int(
            message.text.strip()
        )

    except Exception:
        await message.answer(
            "❌ ID должен состоять только из цифр."
        )
        return

    if user_id == ADMIN_ID:
        await message.answer(
            "👑 Это уже владелец."
        )

        await state.clear()
        return

    add_admin(
        user_id
    )

    await state.clear()

    await message.answer(
        f"✅ Админ <code>{user_id}</code> добавлен.",
        reply_markup=admin_panel_keyboard(
            message.from_user.id
        )
    )


@dp.callback_query(F.data == "admin_remove")
async def admin_remove(
    callback: CallbackQuery,
    state: FSMContext
):
    if callback.from_user.id != ADMIN_ID:
        return

    await state.set_state(
        AdminState.remove_admin
    )

    await callback.message.edit_text(
        """
➖ <b>УДАЛЕНИЕ АДМИНА</b>

Отправьте Telegram ID администратора.
"""
    )

    await callback.answer()


@dp.message(AdminState.remove_admin)
async def save_remove_admin(
    message: Message,
    state: FSMContext
):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        user_id = int(
            message.text.strip()
        )

    except Exception:
        await message.answer(
            "❌ ID должен состоять только из цифр."
        )
        return

    if user_id == ADMIN_ID:
        await message.answer(
            "❌ Владельца удалить нельзя."
        )

        await state.clear()
        return

    remove_admin(
        user_id
    )

    await state.clear()

    await message.answer(
        f"✅ Админ <code>{user_id}</code> удалён.",
        reply_markup=admin_panel_keyboard(
            message.from_user.id
        )
    )


@dp.callback_query(F.data == "admin_list")
async def admin_list(
    callback: CallbackQuery
):
    if callback.from_user.id != ADMIN_ID:
        return

    admins = set(
        get_admins()
    )

    admins.add(
        ADMIN_ID
    )

    text = (
        "📋 <b>АДМИНИСТРАТОРЫ</b>\n\n"
    )

    for admin_id in sorted(admins):
        role = (
            "👑 Владелец"
            if admin_id == ADMIN_ID
            else "🛡 Администратор"
        )

        text += (
            f"{role}: "
            f"<code>{admin_id}</code>\n"
        )

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⬅️ Назад",
                        callback_data="admin_manage"
                    )
                ]
            ]
        )
    )

    await callback.answer()


# =========================================================
# CONFIRM / CANCEL
# =========================================================

@dp.callback_query(F.data.startswith("confirm_"))
async def confirm_order(
    callback: CallbackQuery
):
    if not user_is_admin(
        callback.from_user.id
    ):
        await callback.answer(
            "❌ Нет доступа.",
            show_alert=True
        )
        return

    order_id = int(
        callback.data.split("_")[1]
    )

    order = get_order(
        order_id
    )

    if (
        not order
        or order[5] != "waiting"
    ):
        await callback.answer(
            "⚠️ Заказ уже обработан или не найден.",
            show_alert=True
        )
        return

    if not order[9]:
        await callback.answer(
            "❌ У заказа нет чека.",
            show_alert=True
        )
        return

    # GRAM уже был зарезервирован
    # при создании заказа.
    complete_order(
        order_id
    )

    try:
        if order[7] == "gram":
            message_text = f"""
🎉 <b>ЗАКАЗ #{order_id} ВЫПОЛНЕН</b>

━━━━━━━━━━━━━━━━━━

🔹 <b>{order[10]:g} GRAM</b>

💼 Кошелёк:
<code>{order[11]}</code>

━━━━━━━━━━━━━━━━━━

✅ Заказ подтверждён администрацией.
"""

        else:
            message_text = f"""
🎉 <b>ЗАКАЗ #{order_id} ВЫПОЛНЕН</b>

━━━━━━━━━━━━━━━━━━

🛍 <b>{order_title(order)}</b>
🎯 <b>{order[2]}</b>

━━━━━━━━━━━━━━━━━━

✅ Заказ подтверждён администрацией.
"""

        await bot.send_message(
            order[0],
            message_text
        )

    except Exception:
        pass

    try:
        await callback.message.edit_caption(
            caption=(
                f"✅ <b>ЗАКАЗ #{order_id} ВЫПОЛНЕН</b>\n\n"
                f"Администратор: "
                f"@{callback.from_user.username or callback.from_user.id}"
            ),
            reply_markup=None
        )

    except Exception:
        pass

    await callback.answer(
        "✅ Заказ выполнен"
    )


@dp.callback_query(F.data.startswith("cancel_"))
async def cancel_order_handler(
    callback: CallbackQuery
):
    if not user_is_admin(
        callback.from_user.id
    ):
        await callback.answer(
            "❌ Нет доступа.",
            show_alert=True
        )
        return

    order_id = int(
        callback.data.split("_")[1]
    )

    order = get_order(
        order_id
    )

    if (
        not order
        or order[5] != "waiting"
    ):
        await callback.answer(
            "⚠️ Заказ уже обработан или не найден.",
            show_alert=True
        )
        return

    # Если это GRAM — database.py
    # автоматически вернёт резерв в остаток.
    cancel_order(
        order_id
    )

    try:
        await bot.send_message(
            order[0],
            f"""
❌ <b>ЗАКАЗ #{order_id} ОТМЕНЁН</b>

Ваш заказ был отменён администратором.

Если произошла ошибка, обратитесь к администрации.
"""
        )

    except Exception:
        pass

    try:
        await callback.message.edit_caption(
            caption=(
                f"❌ <b>ЗАКАЗ #{order_id} ОТМЕНЁН</b>\n\n"
                f"Покупатель уведомлён."
            ),
            reply_markup=None
        )

    except Exception:
        pass

    await callback.answer(
        "❌ Заказ отменён"
    )


# =========================================================
# ACTIVITY
# =========================================================

async def activity_middleware(
    handler,
    event,
    data
):
    user = getattr(
        event,
        "from_user",
        None
    )

    if user:
        try:
            touch_user(
                user.id
            )
        except Exception:
            pass

    return await handler(
        event,
        data
    )


# =========================================================
# MAIN
# =========================================================

async def main():
    print(
        "🚀 Запуск бота..."
    )

    try:
        me = await bot.get_me()

        print(
            f"✅ Бот: @{me.username}"
        )

        print(
            f"👑 ADMIN_ID: {ADMIN_ID}"
        )

        print(
            f"⭐ Курс Stars: "
            f"{get_stars_rate():.2f} ₽"
        )

        print(
            f"🔹 GRAM: "
            f"{get_gram_balance():g}"
        )

        print(
            f"📈 Наценка GRAM: "
            f"{get_gram_markup():.2f}%"
        )

        print(
            "🎨 Цвета ReplyKeyboard загружены"
        )

        await bot.delete_webhook(
            drop_pending_updates=True
        )

        print(
            "🧹 Webhook очищен"
        )

        print(
            "🟢 Бот работает!"
        )

        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
        )

    except Exception as error:
        print(
            "❌ ОШИБКА:"
        )
        print(
            error
        )


asyncio.run(main())