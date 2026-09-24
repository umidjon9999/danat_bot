import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# ⚠️ O'Z TOKENINGIZNI VA ADMIN IDINGIZNI YOZING
TOKEN = "TELEGRAM_BOT_TOKENINGIZNI_SHU_YERGA_YOZING"
ADMIN_ID = 123456789  # O'zingizning Telegram ID raqamingiz

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- XOTIRA BAZASI (RAM) ---
users_db = {}  # {user_id: {"balance": 0, "nick": None, "ref_by": None, "refs_count": 0}}
servers_status = {
    "UmidliSMP": "🟢 Online",
    "UmidliAnarxiya": "🟢 Online"
}
pending_purchases = {}  # Admin tasdiqi uchun so'rovlar
promo_codes = {"START2026": 5000}  # Misol uchun promokod (Kod: Summa)

# --- NARXLLAR VA MA'LUMOTLAR ---
RANKS = {
    "player_plus": {"name": "Player+", "30": 5000, "forever": 15000},
    "normal": {"name": "Normal", "30": 10000, "forever": 30000},
    "pro": {"name": "Pro", "30": 20000, "forever": 50000},
    "best": {"name": "Best", "30": 35000, "forever": 80000},
    "good": {"name": "Good", "30": 50000, "forever": 120000},
    "gigant": {"name": "Gigant", "30": 75000, "forever": 180000},
    "imperator": {"name": "Imperator", "30": 100000, "forever": 250000},
    "got": {"name": "Got", "30": 150000, "forever": 350000}
}

CASES = {
    "resurs": {"name": "Resurs Case", "price": 5000},
    "token": {"name": "Token Case", "price": 8000},
    "donat": {"name": "Donat Case", "price": 12000},
    "rank": {"name": "Rank Case", "price": 20000}
}

# --- STATES (HOLATLAR) ---
class Form(StatesGroup):
    waiting_for_nick = State()
    waiting_for_balance_amount = State()
    waiting_for_promo = State()

# --- ASOSIY MENYU ---
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 DONAT CASE", callback_data="menu_cases"), InlineKeyboardButton(text="👑 RANK", callback_data="menu_ranks")],
        [InlineKeyboardButton(text="⚔️ KIT", callback_data="menu_kits"), InlineKeyboardButton(text="🖥 SERVERLAR", callback_data="menu_servers")],
        [InlineKeyboardButton(text="👤 MEN HAQIMDA", callback_data="menu_profile"), InlineKeyboardButton(text="💰 BALANS", callback_data="menu_balance")],
        [InlineKeyboardButton(text="🎁 PROMOKOD", callback_data="menu_promo"), InlineKeyboardButton(text="👥 DO'STLAR", callback_data="menu_referral")],
        [InlineKeyboardButton(text="ℹ️ YORDAM", callback_data="menu_help")]
    ])

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    args = message.text.split()
    
    if user_id not in users_db:
        ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() and int(args[1]) != user_id else None
        users_db[user_id] = {"balance": 0, "nick": None, "ref_by": ref_id, "refs_count": 0}
        
        # Agar referal orqali kirgan bo'lsa
        if ref_id and ref_id in users_db:
            users_db[ref_id]["refs_count"] += 1
            users_db[ref_id]["balance"] += 2000  # Taklif qilganga 2000 so'm bonus
            try:
                await bot.send_message(ref_id, "🎉 Yangi do'stingiz havolangiz orqali qo'shildi! Sizga **2,000 so'm** bonus berildi.", parse_mode="Markdown")
            except:
                pass
    
    await message.answer(
        "👋 Salom! **UmidliCraft** serverining rasmiy donat botiga xush kelibsiz.\n\n"
        "Quyidagi tugmalar yordamida kerakli bo'limni tanlang:",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

# --- NIK TEKSHIRISH ---
@dp.message(Form.waiting_for_nick)
async def save_nick(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    users_db[user_id]["nick"] = message.text.strip()
    await message.answer(f"✅ Nikingiz muvaffaqiyatli saqlandi: `{users_db[user_id]['nick']}`", parse_mode="Markdown", reply_markup=main_menu())
    await state.clear()

# --- SERVERLAR BO'LIMI ---
@dp.callback_query(F.data == "menu_servers")
async def show_servers(callback: types.CallbackQuery):
    text = "🖥 **UmidliCraft Serverlari Holati:**\n\n"
    for srv, status in servers_status.items():
        text += f"🔹 **{srv}**: {status}\n"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_home")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

# --- MEN HAQIMDA ---
@dp.callback_query(F.data == "menu_profile")
async def profile_menu(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    u_data = users_db.get(user_id, {"balance": 0, "nick": "Kiritilmagan", "refs_count": 0})
    
    text = (
        f"👤 **Sizning profilingiz:**\n\n"
        f"🆔 Telegram ID: `{user_id}`\n"
        f"🎮 Minecraft Nik: `{u_data['nick']}`\n"
        f"💰 Balans: `{u_data['balance']} so'm`\n"
        f"👥 Taklif qilingan do'stlar: `{u_data['refs_count']} ta`"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Nikni o'zgartirish", callback_data="change_nick")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_home")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "change_nick")
async def change_nick_flow(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Yangi Minecraft nikingizni kiriting:")
    await state.set_state(Form.waiting_for_nick)
    await callback.answer()

# --- BALANS VA KARTA ORQALI TO'LDIRISH ---
@dp.callback_query(F.data == "menu_balance")
async def balance_menu(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    bal = users_db.get(user_id, {}).get("balance", 0)
    
    text = (
        f"💰 **Sizning balansingiz:** `{bal} so'm`\n\n"
        "💳 **Balansni to'ldirish tartibi:**\n"
        "Quyidagi karta raqamiga kerakli summani o'tkazing:\n\n"
        "💳 Karta: `4545 4545 4545 4545`\n"
        "👤 Egasi: `Umidjon / UmidliCraft`\n\n"
        "Pulni o'tkazib bo'lgach, **'Chekni yuborish'** tugmasini bosing va summa miqdorini kiriting."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Chek yuborish (Summa kiritish)", callback_data="topup_balance")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_home")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "topup_balance")
async def topup_balance(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Karta raqamiga pul o'tkazganingizdan so'ng, qancha summa o'tkazganingizni **faqat raqamda** yozib yuboring (Masalan: `15000`):")
    await state.set_state(Form.waiting_for_balance_amount)
    await callback.answer()

@dp.message(Form.waiting_for_balance_amount)
async def process_topup_amount(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos, faqat raqam kiriting (masalan: 10000):")
        return
    
    amount = int(message.text)
    user_id = message.from_user.id
    req_id = len(pending_purchases) + 1
    
    pending_purchases[req_id] = {
        "type": "balance",
        "user_id": user_id,
        "amount": amount,
        "status": "pending"
    }
    
    await message.answer(f"✅ To'lov so'rovi yuborildi! {amount} so'm admin tomonidan tekshirilib tasdiqlangach balansingizga qo'shiladi.", reply_markup=main_menu())
    
    try:
        await bot.send_message(
            ADMIN_ID,
            f"🔔 **Yangi Karta To'lovi #{req_id}**\n"
            f"Foydalanuvchi: @{message.from_user.username or 'yoq'} (ID: `{user_id}`)\n"
            f"Summa: `{amount} so'm`\n\n"
            f"Tasdiqlash uchun `/admin 9887` paneliga o'ting.",
            parse_mode="Markdown"
        )
    except:
        pass
        
    await state.clear()

# --- PROMOKOD BO'LIMI ---
@dp.callback_query(F.data == "menu_promo")
async def promo_menu(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("🎁 Maxsus promokodingizni kiriting:")
    await state.set_state(Form.waiting_for_promo)
    await callback.answer()

@dp.message(Form.waiting_for_promo)
async def process_promo(message: types.Message, state: FSMContext):
    code = message.text.strip()
    user_id = message.from_user.id
    
    if code in promo_codes:
        bonus = promo_codes[code]
        users_db[user_id]["balance"] += bonus
        await message.answer(f"🎉 Tabriklaymiz! Promokod faollashdi. Balansingizga **{bonus} so'm** qo'shildi!", reply_markup=main_menu(), parse_mode="Markdown")
        del promo_codes[code]  # Bir marta ishlatilgach o'chadi
    else:
        await message.answer("❌ Promokod eskirgan yoki xato kiritildi!", reply_markup=main_menu())
    await state.clear()

# --- REFERAL (DO'STLAR) ---
@dp.callback_query(F.data == "menu_referral")
async def referral_menu(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    
    text = (
        f"👥 **Do'stlaringizni taklif qiling va bonus oling!**\n\n"
        f"Har bir taklif qilgan do'stingiz uchun **2,000 so'm** bonus beriladi.\n\n"
        f"🔗 **Sizning shaxsiy havolangiz:**\n`{ref_link}`"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_home")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

# --- DONAT CASE TANLASH ---
@dp.callback_query(F.data == "menu_cases")
async def cases_server_select(callback: types.CallbackQuery, state: FSMContext):
    if not users_db.get(callback.from_user.id, {}).get("nick"):
        await callback.message.answer("⚠️ Majburiy ravishda avval Minecraftdagi nikingizni kiriting:")
        await state.set_state(Form.waiting_for_nick)
        await callback.answer()
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="UmidliSMP", callback_data="case_srv_SMP"), InlineKeyboardButton(text="UmidliAnarxiya", callback_data="case_srv_Anarxiya")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_home")]
    ])
    await callback.message.edit_text("🎁 Qaysi server uchun Case olmoqchisiz?", reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data.startswith("case_srv_"))
async def cases_list_select(callback: types.CallbackQuery):
    srv = callback.data.split("_")[2]
    kb_rows = []
    for c_key, c_val in CASES.items():
        kb_rows.append([InlineKeyboardButton(text=f"{c_val['name']} - {c_val['price']} so'm", callback_data=f"buycase_{srv}_{c_key}")])
    kb_rows.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="menu_cases")])
    
    await callback.message.edit_text(f"🎁 **{srv}** uchun case tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data.startswith("buycase_"))
async def buy_case_process(callback: types.CallbackQuery):
    _, srv, c_key = callback.data.split("_")
    user_id = callback.from_user.id
    price = CASES[c_key]["price"]
    
    if users_db[user_id]["balance"] < price:
        await callback.answer("❌ Balansingiz yetarli emas! Avval balansni to'ldiring.", show_alert=True)
        return
    
    users_db[user_id]["balance"] -= price
    nick = users_db[user_id]["nick"]
    
    req_id = len(pending_purchases) + 1
    pending_purchases[req_id] = {
        "type": "item",
        "user_id": user_id,
        "desc": f"{CASES[c_key]['name']} ({srv}) - Nik: {nick}",
        "status": "pending"
    }
    
    await callback.message.edit_text(f"✅ Xarid qilindi! Admin serverda berishini tasdiqlamoqda.\nBalansingizdan {price} so'm yechildi.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Bosh sahifa", callback_data="back_home")]]))
    await callback.answer()

# --- RANK TANLASH ---
@dp.callback_query(F.data == "menu_ranks")
async def ranks_server_select(callback: types.CallbackQuery, state: FSMContext):
    if not users_db.get(callback.from_user.id, {}).get("nick"):
        await callback.message.answer("⚠️ Majburiy ravishda avval Minecraftdagi nikingizni kiriting:")
        await state.set_state(Form.waiting_for_nick)
        await callback.answer()
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="UmidliSMP", callback_data="rank_srv_SMP"), InlineKeyboardButton(text="UmidliAnarxiya", callback_data="rank_srv_Anarxiya")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_home")]
    ])
    await callback.message.edit_text("👑 Qaysi server uchun Rank olmoqchisiz?", reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data.startswith("rank_srv_"))
async def ranks_list_select(callback: types.CallbackQuery):
    srv = callback.data.split("_")[2]
    kb_rows = []
    for r_key, r_val in RANKS.items():
        kb_rows.append([InlineKeyboardButton(text=f"{r_val['name']} (30k: {r_val['30']}s / Umurbot: {r_val['forever']}s)", callback_data=f"buyrank_{srv}_{r_key}")])
    kb_rows.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="menu_ranks")])
    
    await callback.message.edit_text(f"👑 **{srv}** uchun rank tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data.startswith("buyrank_"))
async def rank_period_select(callback: types.CallbackQuery):
    _, srv, r_key = callback.data.split("_")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"⏳ 30 kunlik ({RANKS[r_key]['30']} so'm)", callback_data=f"payrank_{srv}_{r_key}_30")],
        [InlineKeyboardButton(text=f"♾️ Umurbot ({RANKS[r_key]['forever']} so'm)", callback_data=f"payrank_{srv}_{r_key}_forever")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"rank_srv_{srv}")]
    ])
    await callback.message.edit_text(f"📅 **{RANKS[r_key]['name']}** uchun muddatni tanlang:", reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data.startswith("payrank_"))
async def pay_rank_process(callback: types.CallbackQuery):
    _, srv, r_key, period = callback.data.split("_")
    user_id = callback.from_user.id
    price = RANKS[r_key]["30"] if period == "30" else RANKS[r_key]["forever"]
    
    if users_db[user_id]["balance"] < price:
        await callback.answer("❌ Balansingiz yetarli emas!", show_alert=True)
        return
        
    users_db[user_id]["balance"] -= price
    nick = users_db[user_id]["nick"]
    period_name = "30 kunlik" if period == "30" else "Umurbot"
    
    req_id = len(pending_purchases) + 1
    pending_purchases[req_id] = {
        "type": "item",
        "user_id": user_id,
        "desc": f"Rank: {RANKS[r_key]['name']} ({period_name}) [{srv}] - Nik: {nick}",
        "status": "pending"
    }
    
    await callback.message.edit_text(f"✅ Rank sotib olindi! Admin tasdiqlashi kutilmoqda.\nNik: `{nick}`\nRank: `{RANKS[r_key]['name']}` ({period_name})", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Bosh sahifa", callback_data="back_home")]]), parse_mode="Markdown")
    await callback.answer()

# --- KIT BO'LIMI ---
@dp.callback_query(F.data == "menu_kits")
async def kits_menu(callback: types.CallbackQuery, state: FSMContext):
    if not users_db.get(callback.from_user.id, {}).get("nick"):
        await callback.message.answer("⚠️ Majburiy ravishda avval nikingizni kiriting:")
        await state.set_state(Form.waiting_for_nick)
        await callback.answer()
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="UmidliSMP", callback_data="kit_srv_SMP"), InlineKeyboardButton(text="UmidliAnarxiya", callback_data="kit_srv_Anarxiya")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_home")]
    ])
    await callback.message.edit_text("⚔️ Qaysi server uchun Kit olmoqchisiz?", reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data.startswith("kit_srv_"))
async def kit_list_select(callback: types.CallbackQuery):
    srv = callback.data.split("_")[2]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Kit VIP - 4,000 so'm", callback_data=f"buykit_{srv}_VIP_4000")],
        [InlineKeyboardButton(text="Kit Premium - 9,000 so'm", callback_data=f"buykit_{srv}_Premium_9000")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="menu_kits")]
    ])
    await callback.message.edit_text(f"⚔️ **{srv}** uchun Kit tanlang:", reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data.startswith("buykit_"))
async def buy_kit_process(callback: types.CallbackQuery):
    _, srv, kit_name, price_str = callback.data.split("_")
    price = int(price_str)
    user_id = callback.from_user.id
    
    if users_db[user_id]["balance"] < price:
        await callback.answer("❌ Balansingiz yetarli emas!", show_alert=True)
        return
        
    users_db[user_id]["balance"] -= price
    nick = users_db[user_id]["nick"]
    
    req_id = len(pending_purchases) + 1
    pending_purchases[req_id] = {
        "type": "item",
        "user_id": user_id,
        "desc": f"Kit {kit_name} ({srv}) - Nik: {nick}",
        "status": "pending"
    }
    
    await callback.message.edit_text(f"✅ Kit sotib olindi! Admin tasdiqlashi kutilmoqda.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Bosh sahifa", callback_data="back_home")]]))
    await callback.answer()

@dp.callback_query(F.data == "menu_help")
async def help_menu(callback: types.CallbackQuery):
    text = (
        "ℹ️ **UmidliCraft Yordam Bo'limi:**\n\n"
        "1. Botdan foydalanish uchun o'yin nikingizni kiriting.\n"
        "2. Karta orqali balansni to'ldirib, istalgan Case, Rank yoki Kit sotib oling.\n"
        "3. Xaridingiz admin tomonidan tasdiqlangach, serverda beriladi.\n"
        "4. Savollar bo'yicha: @AdminUsername"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_home")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "back_home")
async def back_home(callback: types.CallbackQuery):
    await callback.message.edit_text("👋 Bosh menyu:", reply_markup=main_menu())
    await callback.answer()

# --- ADMIN PANEL: /admin 9887 ---
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    args = message.text.split()
    if len(args) < 2 or args[1] != "9887":
        return
        
    total_users = len(users_db)
    pending_count = len([p for p in pending_purchases.values() if p["status"] == "pending"])
    
    text = (
        f"👑 **ADMIN PANEL (UmidliCraft)**\n\n"
        f"📊 **Jami hisobot:**\n"
        f"• Ro'yxatdan o'tganlar: `{total_users} ta`\n"
        f"• Tasdiqlash kutilayotganlar: `{pending_count} ta`"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Xaridlar va To'lovlar", callback_data="adm_requests")],
        [InlineKeyboardButton(text="🖥 Server Statuslarini Tahrirlash", callback_data="adm_servers_edit")],
        [InlineKeyboardButton(text="❌ Chiqish", callback_data="back_home")]
    ])
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "adm_requests")
async def admin_requests(callback: types.CallbackQuery):
    pending = {k: v for k, v in pending_purchases.items() if v["status"] == "pending"}
    if not pending:
        await callback.message.edit_text("✅ Tasdiqlashni kutayotgan so'rovlar yo'q.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Admin Panel", callback_data="adm_back")]]))
        await callback.answer()
        return
        
    kb_rows = []
    for req_id, p in pending.items():
        if p["type"] == "balance":
            title = f"💰 Karta To'lovi: {p['amount']}s"
        else:
            title = f"🛒 {p['desc'][:22]}..."
        kb_rows.append([InlineKeyboardButton(text=title, callback_data=f"adm_viewreq_{req_id}")])
        
    kb_rows.append([InlineKeyboardButton(text="🔙 Admin Panel", callback_data="adm_back")])
    await callback.message.edit_text("📋 Tasdiqlash kutilayotgan so'rovlar:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows))
    await callback.answer()

@dp.callback_query(F.data.startswith("adm_viewreq_"))
async def admin_view_request(callback: types.CallbackQuery):
    req_id = int(callback.data.split("_")[2])
    p = pending_purchases.get(req_id)
    if not p or p["status"] != "pending":
        await callback.answer("So'rov topilmadi!", show_alert=True)
        return
        
    if p["type"] == "balance":
        info = f"💰 **Karta orqali balans to'ldirish**\nFoydalanuvchi ID: `{p['user_id']}`\nSumma: `{p['amount']} so'm`"
    else:
        info = f"🛒 **Donat Xarid**\nFoydalanuvchi ID: `{p['user_id']}`\nTafsilot: `{p['desc']}`"
        
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"adm_accept_{req_id}"), InlineKeyboardButton(text="❌ Rad etish", callback_data=f"adm_reject_{req_id}")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_requests")]
    ])
    await callback.message.edit_text(info, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data.startswith("adm_accept_"))
async def admin_accept(callback: types.CallbackQuery):
    req_id = int(callback.data.split("_")[2])
    p = pending_purchases.get(req_id)
    if not p:
        return
        
    p["status"] = "accepted"
    user_id = p["user_id"]
    
    if p["type"] == "balance":
        if user_id not in users_db:
            users_db[user_id] = {"balance": 0, "nick": None}
        users_db[user_id]["balance"] += p["amount"]
        try:
            await bot.send_message(user_id, f"✅ To'lovingiz tasdiqlandi! Balansingizga `{p['amount']} so'm` qo'shildi.", parse_mode="Markdown")
        except:
            pass
    else:
        try:
            await bot.send_message(user_id, f"🎉 Admin xaridingizni tasdiqladi:\n`{p['desc']}`", parse_mode="Markdown")
        except:
            pass
            
    await callback.message.edit_text(f"✅ So'rov #{req_id} tasdiqlandi!", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_requests")]]))
    await callback.answer()

@dp.callback_query(F.data.startswith("adm_reject_"))
async def admin_reject(callback: types.CallbackQuery):
    req_id = int(callback.data.split("_")[2])
    p = pending_purchases.get(req_id)
    if p:
        p["status"] = "rejected"
        try:
            await bot.send_message(p["user_id"], f"❌ Afsuski, #{req_id}-sonli so'rovingiz admin tomonidan rad etildi.")
        except:
            pass
            
    await callback.message.edit_text(f"❌ So'rov rad etildi.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_requests")]]))
    await callback.answer()

@dp.callback_query(F.data == "adm_servers_edit")
async def admin_servers_edit(callback: types.CallbackQuery):
    kb_rows = []
    for srv in servers_status.keys():
        kb_rows.append([
            InlineKeyboardButton(text=f"🟢 {srv}: On", callback_data=f"set_srv_{srv}_online"),
            InlineKeyboardButton(text=f"🔴 {srv}: Off", callback_data=f"set_srv_{srv}_offline")
        ])
    kb_rows.append([InlineKeyboardButton(text="🔙 Admin Panel", callback_data="adm_back")])
    await callback.message.edit_text("🖥 Server statusini o'zgartirish:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows))
    await callback.answer()

@dp.callback_query(F.data.startswith("set_srv_"))
async def set_server_status_action(callback: types.CallbackQuery):
    _, _, srv, status_type = callback.data.split("_")
    servers_status[srv] = "🟢 Online" if status_type == "online" else "🔴 Offline"
    await callback.answer(f"{srv} statusi o'zgartirildi!")
    await admin_servers_edit(callback)

@dp.callback_query(F.data == "adm_back")
async def admin_back(callback: types.CallbackQuery):
    total_users = len(users_db)
    pending_count = len([p for p in pending_purchases.values() if p["status"] == "pending"])
    text = (
        f"👑 **ADMIN PANEL (UmidliCraft)**\n\n"
        f"📊 **Jami hisobot:**\n"
        f"• Ro'yxatdan o'tganlar: `{total_users} ta`\n"
        f"• Tasdiqlash kutilayotganlar: `{pending_count} ta`"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Xaridlar va To'lovlar", callback_data="adm_requests")],
        [InlineKeyboardButton(text="🖥 Server Statuslarini Tahrirlash", callback_data="adm_servers_edit")],
        [InlineKeyboardButton(text="❌ Chiqish", callback_data="back_home")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

# --- ISHGA TUSHIRISH ---
async def main():
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())