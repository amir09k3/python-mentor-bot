# src/utils/knowledge_base.py
import re

def understand_and_respond(text: str) -> str:
    """
    درک عبارت طبیعی و تولید پاسخ/کد
    """
    t = text.lower().strip()
    
    # --- الگوهای تولید کد ---
    # معکوس لیست
    if any(phrase in t for phrase in ["معکوس", "ورودی معکوس", "reverse list", "list معکوس"]):
        if "تابع" in t or "function" in t:
            return (
                "'''python\n"
                "def reverse_list(lst):\n"
                "    return lst[::-1]  # روش سریع\n"
                "\n"
                "# یا با حلقه:\n"
                "# def reverse_list(lst):\n"
                "#     result = []\n"
                "#     for i in range(len(lst)-1, -1, -1):\n"
                "#         result.append(lst[i])\n"
                "#     return result\n"
                "'''"

            )
        else:
            return "[::-1] برای معکوس کردن لیست. مثال: [1,2,3][::-1] → [3,2,1]"

    # ادغام دو لیست
    elif any(phrase in t for phrase in ["ادغام", "ترکیب", "merge", "combine", "join list"]):
        return (
            "'''pyton\n"
            "# روش ۱: +\n"
            "list1 = [1, 2]\n"
            "list2 = [3, 4]\n"
            "merged = list1 + list2  # [1, 2, 3, 4]\n"
            "\n"
            "# روش ۲: extend()\n"
            "list1.extend(list2)\n"
            "'''"

        )
    
    # عدد اول
    elif any(phrase in t for phrase in ["عدد اول", "prime", "اول است", "تشخیص اول"]):
        return (
            "'''python\n"
            "def is_prime(n):\n"
            "    if n < 2:\n"
            "        return False\n"
            "    for i in range(2, int(n**0.5)+1):\n"
            "        if n % i == 0:\n"
            "            return False\n"
            "    return True\n"
            "\n"
            "# تست\n"
            "print(is_prime(17))  # True\n"
            "'''"

        )
    
    # جستجو در لیست
    elif any(phrase in t for phrase in ["جستجو", "search", "پیدا کردن", "index"]):
        return (
            "'''python\n"
            "# پیدا کردن اولین اندیس:\n"
            "lst = [10, 20, 30]\n"
            "index = lst.index(20)  # 1\n"
            "\n"
            "# یا با حلقه:\n"
            "def find_index(lst, value):\n"
            "    for i, x in enumerate(lst):\n"
            "        if x == value:\n"
            "            return i\n"
            "    return -1\n"
            "'''"

        )
    
    # --- سوالات مفهومی ---
    elif "تفاوت" in t and ("list" in t or "لیست") and ("tuple" in t or "چندتایی"):
        return "list: قابل تغییر، با []. tuple: غیرقابل تغییر، با ()."
    
    elif "چطور" in t and "تابع" in t and "بنویس" in t:
        return "ساختار تابع:\n`python\ndef اسم_تابع(پارامترها):\n    # بدنه\n    return نتیجه\n```"
    
    # --- پاسخ پیش‌فرض ---
    else:
        return None  # نمی‌دونم → بذار کد رو اجرا کنه
    