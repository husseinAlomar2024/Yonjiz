"""Persistent English/Arabic UI language and translation helpers."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from PySide6.QtCore import QDateTime, QLocale, Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from desktop.paths import data_dir

LANG_FILE = data_dir() / "settings.json"
LANGUAGE = "en"

AR = {
    # Login
    "ACCOUNT ACCESS": "الوصول إلى الحساب",
    "Log in.": "تسجيل الدخول.",
    "Open your local workspace. Everything stays on this PC.": "افتح مساحتك المحلية. كل شيء يبقى على هذا الجهاز.",
    "Username": "اسم المستخدم",
    "Password": "كلمة المرور",
    "your_username": "اسم_المستخدم",
    "Your password": "كلمة المرور",
    "Show": "إظهار",
    "Hide": "إخفاء",
    "Open my workspace  →": "افتح مساحتي  ←",
    "Create a local account": "إنشاء حساب محلي",
    "OFFLINE · NO SERVER · NO INTERNET": "دون اتصال · دون خادم · دون إنترنت",
    "Quiet by design. Built for the work that matters.": "هادئ بالتصميم. مبني للعمل الذي يهم.",
    "A QUIETER WORKSPACE": "مساحة عمل أهدأ",
    "LOCAL TIME": "الوقت المحلي",
    "Local time": "الوقت المحلي",
    "Jordan Standard Time": "توقيت الأردن",
    "●  LIVE": "●  مباشر",
    "ALL TASKS": "كل المهام",
    "OPEN": "مفتوحة",
    "DUE TODAY": "تستحق اليوم",
    "COMPLETED": "المنجزة",
    "The day is yours.": "اليوم لك.",
    "Pick up a thread.": "تابع خيطًا.",
    "Your tasks, deadlines and calendar live on this computer. No internet, no cloud, no server.": "مهامك ومواعيدك وتقويمك على هذا الجهاز. دون إنترنت، دون سحابة، دون خادم.",
    "Your tasks, deadlines and calendar live on this computer.\nNo internet, no cloud, no server.": "مهامك ومواعيدك وتقويمك على هذا الجهاز.\nدون إنترنت، دون سحابة، دون خادم.",
    "A clock that stays present": "ساعة تبقى حاضرة",
    "Analog warmth, digital precision.": "دفء عقاربي ودقة رقمية.",
    "A calendar with only your dates": "تقويم بمواعيدك وحدها",
    "Quiet dots, not crowded grids.": "نقاط هادئة، لا شبكة مزدحمة.",
    "One protected main admin": "مدير رئيسي محمي واحد",
    "Local accounts, clear hierarchy.": "حسابات محلية وهيكل واضح.",
    "Log out": "تسجيل الخروج",
    "Main admin": "المدير الرئيسي",
    "Admin · seat {n}": "مدير · مقعد {n}",
    "Member": "عضو",
    "Signed in locally. No internet connection required.": "تم الدخول محليًا. لا حاجة لاتصال بالإنترنت.",
    "Signed out.": "تم تسجيل الخروج.",
    "YONJIZ desktop · local only": "ينجز سطح المكتب · محلي فقط",
    "Workspace": "المساحة",
    "Admin": "الإدارة",
    "Workspace · YONJIZ · ينجز": "المساحة · ينجز",
    "Admin console · YONJIZ · ينجز": "لوحة الإدارة · ينجز",
    "YONJIZ · ينجز": "ينجز",

    # Workspace
    "Good morning, {name}.": "صباح الخير، {name}.",
    "Good afternoon, {name}.": "مساء الخير، {name}.",
    "Good evening, {name}.": "مساء الخير، {name}.",
    "Here’s the shape of your day. Keep it light, or give something a deadline.": "هذه صورة يومك. اجعله خفيفًا، أو امنح شيئًا موعدًا.",
    "New task": "مهمة جديدة",
    "All tasks": "كل المهام",
    "in your workspace": "في مساحتك",
    "Open": "مفتوحة",
    "still in motion": "قيد العمل",
    "Due today": "تستحق اليوم",
    "on today’s list": "في قائمة اليوم",
    "Overdue": "متأخرة",
    "needs a little care": "تحتاج قليلًا من العناية",
    "Your tasks": "مهامك",
    "Search tasks": "ابحث في المهام",
    "Smart order": "الترتيب الذكي",
    "By deadline": "حسب الموعد",
    "By priority": "حسب الأولوية",
    "Newest first": "الأحدث أولًا",
    "All": "الكل",
    "Done": "منجزة",
    "{n} tasks": "{n} مهام",
    "{n} of {m} shown": "{n} من {m} ظاهرة",
    "Showing  {date}": "عرض  {date}",
    "Deadline calendar": "تقويم المواعيد",
    "DEADLINE CALENDAR": "تقويم المواعيد",
    "Today": "اليوم",
    "Clear date": "مسح التاريخ",
    "● Deadline": "● موعد",
    "● Overdue": "● متأخرة",
    "● Done": "● منجزة",
    "Day progress": "تقدم اليوم",
    "DAY PROGRESS": "تقدم اليوم",
    "A fresh start": "بداية جديدة",
    "Add a task to begin.": "أضف مهمة للبدء.",
    "Everything, done.": "كل شيء منجز.",
    "A clean sweep. Make some room.": "إنجاز كامل. أفسح بعض المساحة.",
    "Well under way": "في الطريق جيدًا",
    "Finding a rhythm": "إيجاد إيقاع",
    "Ready when you are": "جاهز حين تكون جاهزًا",
    "{complete} of {total} tasks complete.": "{complete} من {total} مهام منجزة.",
    "{n} tasks waiting.": "{n} مهام في الانتظار.",
    "A clear page.": "صفحة فارغة.",
    "Nothing matches that view.": "لا شيء يطابق هذا العرض.",
    "Add the first thing you want to make room for. A deadline is optional.": "أضف أول شيء تريد إنجازه. الموعد اختياري.",
    "Try a different filter or date.": "جرّب مرشحًا أو تاريخًا آخر.",
    "Add your first task": "أضف مهمتك الأولى",
    "Tip: deadlines are optional. Turn one on only when a date matters.": "نصيحة: المواعيد اختيارية. فعّلها عندما يهم التاريخ.",
    "No deadline": "دون موعد",
    "Today, {time}": "اليوم، {time}",
    "Tomorrow, {time}": "غدًا، {time}",
    "Edit": "تعديل",
    "Delete": "حذف",
    "TODAY": "اليوم",
    "SOON": "قريبًا",
    "OVERDUE": "متأخرة",
    "DONE": "منجزة",
    "SOON": "قريبًا",
    "High": "عالية",
    "Medium": "متوسطة",
    "Low": "منخفضة",
    "Critical": "حرجة",
    "Very low": "منخفضة جدًا",
    "VERY LOW": "منخفضة جدًا",
    "LOW": "منخفضة",
    "MEDIUM": "متوسطة",
    "HIGH": "عالية",
    "CRITICAL": "حرجة",
    "Show or hide the password": "إظهار كلمة المرور أو إخفاؤها",
    "●  OFFLINE  ·  NO SERVER  ·  NO INTERNET": "●  دون اتصال  ·  دون خادم  ·  دون إنترنت",
    "Task added.": "تمت إضافة المهمة.",
    "Task updated.": "تم تحديث المهمة.",
    "Task deleted.": "تم حذف المهمة.",

    # Composer
    "NEW TASK": "مهمة جديدة",
    "EDIT TASK": "تعديل المهمة",
    "Task title": "عنوان المهمة",
    "What needs doing?": "ما الذي يجب إنجازه؟",
    "Priority": "الأولوية",
    "Deadline": "الموعد",
    "Set a deadline": "تحديد موعد",
    "Notes  ·  optional": "ملاحظات  ·  اختياري",
    "A little context, if it helps.": "سياق صغير، إن كان مفيدًا.",
    "Correct spelling": "تصحيح الإملاء",
    "No obvious spelling issues.": "لا توجد أخطاء إملائية واضحة.",
    "Undo": "تراجع",
    "Add task": "إضافة المهمة",
    "Save changes": "حفظ التغييرات",
    "Cancel": "إلغاء",
    "Give this task a title.": "أعطِ هذه المهمة عنوانًا.",
    "Close without saving": "إغلاق دون حفظ",
    "Corrected: {preview}{more}": "تم التصحيح: {preview}{more}",
    "Spelling changes undone.": "تم التراجع عن تصحيحات الإملاء.",
    "Mark as done": "تحديد كمنجزة",
    "Mark as not done": "تحديد كغير منجزة",
    "Edit task": "تعديل المهمة",
    "Delete task": "حذف المهمة",
    "Delete “{title}”? This cannot be undone.": "حذف «{title}»؟ لا يمكن التراجع عن ذلك.",
    "SLOT {n}": "المقعد {n}",
    "Seat {n}": "المقعد {n}",

    # Admin
    "CONTROL ROOM": "غرفة التحكم",
    "The people and the work.": "الأشخاص والعمل.",
    "The people and<br><i>the work.</i>": "الأشخاص<br><i>والعمل.</i>",
    "A compact view of every account and task. Three seats, one protected main admin.": "عرض مختصر لكل حساب ومهمة. ثلاثة مقاعد، ومدير رئيسي واحد محمي.",
    "Recent tasks": "المهام الأخيرة",
    "Recent activity": "النشاط الأخير",
    "ACROSS ACCOUNTS": "عبر الحسابات",
    "ACCOUNTABILITY": "المساءلة",
    "No tasks have been added yet.": "لم تُضف مهام بعد.",
    "Admin actions will appear here.": "ستظهر إجراءات الإدارة هنا.",
    "USER": "مستخدم",
    "●  Active": "●  نشط",
    "●  Inactive": "●  غير نشط",
    "  YOU": "  أنت",
    "You": "أنت",
    "Make admin": "اجعل مديرًا",
    "Deactivate": "تعطيل",
    "Activate": "تفعيل",
    "Delete account": "حذف الحساب",
    "Admin role updated.": "تم تحديث صلاحية الإدارة.",
    "Account updated.": "تم تحديث الحساب.",
    "Account deleted.": "تم حذف الحساب.",
    "Delete account": "حذف الحساب",
    "Permanently delete @{username} and all of their tasks?": "حذف @{username} وكل مهامه نهائيًا؟",
    "Admin promoted": "تمت ترقية مدير",
    "Admin demoted": "تم تخفيض مدير",
    "Developer access": "وصول المطور",
    "Admin created via CLI": "مدير أُنشئ عبر سطر الأوامر",
    "Main admin established": "تم تثبيت المدير الرئيسي",
    "Account activated": "تم تفعيل الحساب",
    "Account deactivated": "تم تعطيل الحساب",
    "Account deleted": "تم حذف الحساب",
    "Task deleted": "تم حذف المهمة",
    "Seat 1 is reserved for the protected main admin. Seats 2 and 3 can be hired and released — never the main account.": "المقعد 1 مخصص للمدير الرئيسي المحمي. يمكن شغل المقعدين 2 و3 وتحريرهما — لكن ليس الحساب الرئيسي أبدًا.",
    "Delete task": "حذف المهمة",
    "Yes": "نعم",
    "No": "لا",
    "OK": "حسنًا",
    "Seat {n}": "المقعد {n}",
    "MAIN ADMIN": "المدير الرئيسي",
    "OCCUPIED": "مشغول",
    "AVAILABLE": "متاح",
    "An open seat": "مقعد متاح",
    "Promote a member from the directory below.": "رقِّ عضوًا من الدليل أدناه.",
    "Protected main account": "حساب رئيسي محمي",
    "PROTECTED": "محمي",
    "Since {date}": "منذ {date}",
    "Demote": "تخفيض",
    "Promote": "ترقية",
    "SLOT 3": "المقعد 3",
    "PEOPLE": "الأشخاص",
    "ALL TASKS": "كل المهام",
    "COMPLETED": "المنجزة",
    "OVERDUE": "المتأخرة",
    "active accounts": "حسابات نشطة",
    "across every account": "عبر كل الحسابات",
    "finished tasks": "مهام منتهية",
    "past their deadline": "تجاوزت موعدها",
    "DIRECTORY": "الدليل",
    "People": "الأشخاص",
    "Find a person": "ابحث عن شخص",
    "PERSON": "الشخص",
    "ACCESS": "الوصول",
    "STATUS": "الحالة",
    "TASKS": "المهام",
    "JOINED": "الانضمام",
    "ACTIONS": "الإجراءات",
    "ADMIN · {n}": "مدير · {n}",
    "MAIN ADMIN · {n}": "المدير الرئيسي · {n}",
    "Active": "نشط",
    "Untouchable": "لا يمكن المساس به",
    "Why three?": "لماذا ثلاثة؟",
    "Three is enough. Everyone else can still have a clear workspace without an admin badge.": "ثلاثة تكفي. يمكن للجميع الحصول على مساحة واضحة دون شارة إدارة.",
    "The main admin is permanently protected. Other admins can hire or demote admins, but never the main admin.": "المدير الرئيسي محمي دائمًا. يمكن للمدراء الآخرين ترقية أو تخفيض مدراء، لكن ليس المدير الرئيسي.",
    "The main admin is permanently protected. Nobody can demote or remove this account.": "المدير الرئيسي محمي دائمًا. لا يمكن لأحد تخفيض هذا الحساب أو حذفه.",
    "All three admin seats are filled.": "مقاعد الإدارة الثلاثة مشغولة.",
    "The main admin cannot be demoted.": "لا يمكن تخفيض المدير الرئيسي.",
    "The main admin cannot be deleted.": "لا يمكن حذف المدير الرئيسي.",
    "This account is already an admin.": "هذا الحساب مدير بالفعل.",
    "No open admin seat.": "لا يوجد مقعد إدارة متاح.",

    # Registration / errors
    "Create local account": "إنشاء حساب محلي",
    "Create a local account": "إنشاء حساب محلي",
    "Full name": "الاسم الكامل",
    "Email": "البريد الإلكتروني",
    "Password (8+ characters)": "كلمة المرور (8 أحرف أو أكثر)",
    "Regular account. The main admin can grant admin access.": "حساب عادي. يمكن للمدير الرئيسي منح صلاحية الإدارة.",
    "Create account": "إنشاء الحساب",
    "Invalid username or password.": "اسم المستخدم أو كلمة المرور غير صحيحة.",
    "Username already exists.": "اسم المستخدم موجود بالفعل.",
    "Email already registered.": "البريد الإلكتروني مسجل بالفعل.",
    "Password must be at least 8 characters.": "يجب أن تكون كلمة المرور 8 أحرف على الأقل.",
    "Passwords do not match.": "كلمتا المرور غير متطابقتين.",
    "Please sign in again.": "يرجى تسجيل الدخول مرة أخرى.",
    "This account is no longer active.": "هذا الحساب لم يعد نشطًا.",
    "That username and password combination is not correct.": "اسم المستخدم وكلمة المرور غير صحيحين.",
    "This account is deactivated.": "هذا الحساب معطّل.",
    "Give the task a title.": "أعطِ المهمة عنوانًا.",
    "Task title is too long.": "عنوان المهمة طويل جدًا.",
    "Task note is too long.": "ملاحظة المهمة طويلة جدًا.",
    "Choose a valid priority.": "اختر أولوية صالحة.",
    "Task not found.": "المهمة غير موجودة.",
    "Administrator access is required.": "صلاحية الإدارة مطلوبة.",
    "That account no longer exists.": "هذا الحساب لم يعد موجودًا.",
    "Unknown role action.": "إجراء الصلاحية غير معروف.",
    "That task no longer exists.": "هذه المهمة لم تعد موجودة.",
    "Username must be 3–30 lowercase letters, numbers or underscores.": "يجب أن يكون اسم المستخدم من 3 إلى 30 حرفًا صغيرًا أو أرقامًا أو شرطات سفلية.",
    "Enter your name.": "أدخل اسمك.",
    "Enter a valid email.": "أدخل بريدًا إلكترونيًا صالحًا.",
    "Password is too long.": "كلمة المرور طويلة جدًا.",
    "That username or email is already registered.": "اسم المستخدم أو البريد الإلكتروني مسجل بالفعل.",
    "Password is longer than 72 UTF-8 bytes.": "كلمة المرور أطول من 72 بايت.",
    "Could not update that administrator.": "تعذر تحديث هذا المدير.",
    "This account is still referenced by other data.": "هذا الحساب مرتبط ببيانات أخرى.",
    "Full name is required.": "الاسم الكامل مطلوب.",
    "Username is required.": "اسم المستخدم مطلوب.",
}


def load_language() -> str:
    global LANGUAGE
    try:
        raw = json.loads(LANG_FILE.read_text(encoding="utf-8-sig"))
        value = raw.get("language")
        if value in ("en", "ar"):
            LANGUAGE = value
    except (OSError, ValueError):
        pass
    return LANGUAGE


def save_language(value: str) -> None:
    try:
        LANG_FILE.parent.mkdir(parents=True, exist_ok=True)
        LANG_FILE.write_text(
            json.dumps({"language": value}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError:
        pass


def set_language(value: str) -> None:
    global LANGUAGE
    if value not in ("en", "ar"):
        return
    LANGUAGE = value
    save_language(value)


def language() -> str:
    return LANGUAGE


def is_arabic() -> bool:
    return LANGUAGE == "ar"


def switch_label() -> str:
    return "العربية" if not is_arabic() else "English"


def tr(text: str, **kwargs: Any) -> str:
    value = AR.get(text, text) if is_arabic() else text
    if kwargs:
        try:
            value = value.format(**kwargs)
        except (KeyError, ValueError):
            pass
    return value


def error_text(message: str) -> str:
    return tr(message)


def warn(parent, title: str, message: str) -> None:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Warning)
    box.setWindowTitle(tr(title))
    box.setText(message)
    box.addButton(tr("OK"), QMessageBox.ButtonRole.AcceptRole)
    box.exec()


def confirm(parent, title: str, message: str) -> bool:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Question)
    box.setWindowTitle(tr(title))
    box.setText(message)
    yes = box.addButton(tr("Yes"), QMessageBox.ButtonRole.AcceptRole)
    no = box.addButton(tr("No"), QMessageBox.ButtonRole.RejectRole)
    box.setDefaultButton(no)
    box.exec()
    return box.clickedButton() is yes


def qt_locale() -> QLocale:
    if is_arabic():
        return QLocale(QLocale.Language.Arabic, QLocale.Country.Jordan)
    return QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)


def format_date(dt: datetime, pattern: str = "dddd, MMMM d, yyyy") -> str:
    return qt_locale().toString(QDateTime(dt), pattern)


def format_deadline(dt: datetime) -> str:
    pattern = "dddd، d MMMM، h:mm AP" if is_arabic() else "MMM d, h:mm AP"
    return qt_locale().toString(QDateTime(dt), pattern)


def format_month(value: str) -> str:
    try:
        dt = datetime.strptime(value[:7], "%Y-%m")
    except (TypeError, ValueError):
        return value
    return qt_locale().toString(QDateTime(dt), "MMMM yyyy")


def format_short_date(value: str) -> str:
    try:
        dt = datetime.strptime(value[:10], "%Y-%m-%d")
    except (TypeError, ValueError):
        return value
    return qt_locale().toString(QDateTime(dt), "d MMM yyyy")


def apply_direction() -> None:
    app = QApplication.instance()
    if app is not None:
        app.setLayoutDirection(Qt.RightToLeft if is_arabic() else Qt.LeftToRight)


load_language()
