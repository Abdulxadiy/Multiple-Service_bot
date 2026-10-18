from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_reminder_main_keyboard() -> InlineKeyboardMarkup:
    """Eslatmalar xizmati bosh menyusi"""
    keyboard = [
        [InlineKeyboardButton(text="➕ Yangi eslatma yaratish", callback_data="rem:new")],
        [
            InlineKeyboardButton(text="📌 Faol eslatmalar", callback_data="rem:active"),
            InlineKeyboardButton(text="✅ Bajarilganlar tarixi", callback_data="rem:history")
        ],
        [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="nav:home")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Bekor qilish tugmasi"""
    keyboard = [
        [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="rem:cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_time_presets_keyboard() -> InlineKeyboardMarkup:
    """Vaqtni tezkor tanlash tugmalari"""
    keyboard = [
        [
            InlineKeyboardButton(text="⏱ 15 daqiqadan keyin", callback_data="rem_time:15m"),
            InlineKeyboardButton(text="⏳ 30 daqiqadan keyin", callback_data="rem_time:30m")
        ],
        [
            InlineKeyboardButton(text="🕒 1 soatdan keyin", callback_data="rem_time:1h"),
            InlineKeyboardButton(text="🕓 3 soatdan keyin", callback_data="rem_time:3h")
        ],
        [
            InlineKeyboardButton(text="🌅 Ertaga (09:00)", callback_data="rem_time:tomorrow_morning"),
            InlineKeyboardButton(text="📅 Ertaga shu vaqtda", callback_data="rem_time:tomorrow_same")
        ],
        [
            InlineKeyboardButton(text="✍️ Qo'lda vaqt kiritish", callback_data="rem_time:custom")
        ],
        [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="rem:cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_repeat_keyboard() -> InlineKeyboardMarkup:
    """Takrorlanish turini tanlash tugmalari"""
    keyboard = [
        [InlineKeyboardButton(text="🚫 Bir martalik", callback_data="rem_repeat:none")],
        [InlineKeyboardButton(text="🔄 Har kuni (shu vaqtda)", callback_data="rem_repeat:daily")],
        [
            InlineKeyboardButton(text="📆 Har hafta", callback_data="rem_repeat:weekly"),
            InlineKeyboardButton(text="🗓 Har oy", callback_data="rem_repeat:monthly")
        ],
        [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="rem:cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_notification_keyboard(reminder_id: int) -> InlineKeyboardMarkup:
    """Bildirishnoma xabarining ostidagi asosiy tugmalar"""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Bajarildi", callback_data=f"rem:done:{reminder_id}"),
            InlineKeyboardButton(text="⏰ Keyinroq eslatilsin", callback_data=f"rem:snooze_menu:{reminder_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_snooze_keyboard(reminder_id: int) -> InlineKeyboardMarkup:
    """Keyinroq eslatilsin bosilganda chiqadigan vaqt variantlari"""
    keyboard = [
        [
            InlineKeyboardButton(text="⏱ 15 daqiqadan so'ng", callback_data=f"rem:snooze:{reminder_id}:15m"),
            InlineKeyboardButton(text="⏳ 1 soatdan so'ng", callback_data=f"rem:snooze:{reminder_id}:1h")
        ],
        [
            InlineKeyboardButton(text="🕒 3 soatdan so'ng", callback_data=f"rem:snooze:{reminder_id}:3h"),
            InlineKeyboardButton(text="🌅 Ertaga (09:00)", callback_data=f"rem:snooze:{reminder_id}:tomorrow_morning")
        ],
        [
            InlineKeyboardButton(text="📅 Ertaga shu vaqtda", callback_data=f"rem:snooze:{reminder_id}:tomorrow_same"),
            InlineKeyboardButton(text="✍️ Boshqa vaqt", callback_data=f"rem:snooze_custom:{reminder_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"rem:back_to_notify:{reminder_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_active_reminders_keyboard(reminders: list) -> InlineKeyboardMarkup:
    """Faol eslatmalar ro'yxati tugmalari"""
    keyboard = []
    for r in reminders[:15]:
        # Har bir eslatma uchun qisqa matn va boshqaruv
        preview = (r.text or "Ovozli/Rasm eslatma")[:25]
        keyboard.append([
            InlineKeyboardButton(text=f"📌 {preview}...", callback_data=f"rem:view:{r.id}")
        ])
    
    keyboard.append([
        InlineKeyboardButton(text="➕ Yangi qo'shish", callback_data="rem:new"),
        InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="svc:reminders")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_reminder_detail_keyboard(reminder_id: int, is_completed: bool = False) -> InlineKeyboardMarkup:
    """Alohida bitta eslatmani ko'rish va boshqarish"""
    keyboard = []
    if not is_completed:
        keyboard.append([
            InlineKeyboardButton(text="✅ Bajarildi", callback_data=f"rem:done:{reminder_id}"),
            InlineKeyboardButton(text="⏰ Qoldirish", callback_data=f"rem:snooze_menu:{reminder_id}")
        ])
    keyboard.append([
        InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"rem:delete:{reminder_id}"),
        InlineKeyboardButton(text="🔙 Orqaga", callback_data="rem:active" if not is_completed else "rem:history")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_history_keyboard(has_items: bool) -> InlineKeyboardMarkup:
    """Bajarilganlar tarixi menyusi"""
    keyboard = []
    if has_items:
        keyboard.append([
            InlineKeyboardButton(text="🗑 Barchasini tozalash", callback_data="rem:clear_history")
        ])
    keyboard.append([
        InlineKeyboardButton(text="🔙 Eslatmalar menyusi", callback_data="svc:reminders")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_voice_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Ovoz matnga o'girilganda tasdiqlash tugmalari"""
    keyboard = [
        [InlineKeyboardButton(text="✅ Ha, to'g'ri", callback_data="voice_confirm:yes")],
        [
            InlineKeyboardButton(text="✍️ Matnni tahrirlash", callback_data="voice_confirm:edit"),
            InlineKeyboardButton(text="🔄 Qayta aytish", callback_data="voice_confirm:retry")
        ],
        [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="rem:cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
