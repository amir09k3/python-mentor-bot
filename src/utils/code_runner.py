# src/utils/code_runner.py
import sys
import io
import re
from types import SimpleNamespace

def is_code_safe(code: str) -> bool:
    """بررسی الگوهای خطرناک در کد"""
    dangerous = [
        r'os\s*\.', r'subprocess\s*\.', r'sys\s*\.', r'import\s+os',
        r'import\s+subprocess', r'import\s*\(', r'open\s*\(',
        r'exec\s*\(', r'eval\s*\(', r'\.system\s*\(', r'\.popen\s*\(',
        r'delete|remove|format|shutil|socket|threading|multiprocessing'
    ]
    code_lower = code.lower()
    for pat in dangerous:
        if re.search(pat, code, re.IGNORECASE):
            return False
    return True

def run_code_safely(code: str, timeout: int = 5) -> dict:
    if not is_code_safe(code):
        return {
            "success": False,
            "output": "",
            "error": "❌ کد حاوی دستورات خطرناک است. فقط کدهای آموزشی ساده مجازند."
        }
     # تولید خروجی برای کدهای تابعی
    if "def " in code and "print(" not in code:
        code += "\n\n# --- تست خودکار ---\n"
        # اضافه کردن تست برای توابع رایج
        if "add(" in code:
            code += "print('تست add(2,3):', add(2, 3))"
        elif "factorial(" in code or "fact(" in code:
            code += "print('تست fact(5):', factorial(5) if 'factorial' in locals() else fact(5))"
        elif "fib(" in code:
            code += "print('تست fib(6):', fib(6))"
        elif "reverse(" in code:
            code += "print('تست reverse(\"abc\"):', reverse('abc'))"
        else:
            # تست عمومی
            code += "# کد شما فقط تابع تعریف کرده — برای دیدن خروجی، از print استفاده کنید."

    # محدود کردن فضای اجرایی
    restricted_globals = {
        "builtins": {
            "print": print,
            "len": len,
            "range": range,
            "str": str,
            "int": int,
            "float": float,
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
            "bool": bool,
            "abs": abs,
            "max": max,
            "min": min,
            "sum": sum,
            "type": type,
            "isinstance": isinstance,
            "ValueError": ValueError,
            "TypeError": TypeError,
            "IndexError": IndexError,
            "KeyError": KeyError,
            "ZeroDivisionError": ZeroDivisionError,
        }
    }
    
    # جلوگیری از حلقه‌های نامتناهی با شمارش خط
    if code.count('\n') > 100:
        return {
            "success": False,
            "output": "",
            "error": "❌ کد بیش از حد طولانی است (حداکثر 100 خط)."
        }
    
    # جلوگیری از حلقه‌های بزرگ
    for pattern in [r'for\s+.*\s+in\s+range\(\s*1000', r'while\s+True']:
        if re.search(pattern, code):
            return {
                "success": False,
                "output": "",
                "error": "❌ حلقه‌های بزرگ یا نامتناهی مجاز نیستند."
            }
    
    # اجرای کد در stdout محدودشده
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = captured_output = io.StringIO()
    sys.stderr = captured_error = io.StringIO()
    
    try:
        exec(code, restricted_globals)
        output = captured_output.getvalue().strip()
        error = captured_error.getvalue().strip()
        success = error == ""
        return {
            "success": success,
            "output": output,
            "error": error if error else ""
        }
    except Exception as e:
        return {
            "success": False,
            "output": captured_output.getvalue().strip(),
            "error": f"{type(e).__name__}: {str(e)}"
        }
    finally:
        sys.stdout = old_stdout

        sys.stderr = old_stderr
