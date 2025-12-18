# src/utils/code_quality.py
import subprocess
import sys
import tempfile
import os
import re

def analyze_code_quality(code: str) -> dict:
    """
    تحلیل کیفیت کد با pylint
    Returns: {
        "score": float (0-10),
        "warnings": list,
        "conventions": list,
        "refactor": list,
        "error_count": int
    }
    """
    # ایجاد فایل موقت
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        # اضافه کردن تنظیمات pylint برای کاهش noise
        config_comment = "# pylint: disable=missing-module-docstring,missing-function-docstring\n"
        f.write(config_comment + code)
        temp_path = f.name

    try:
        # اجرای pylint با تنظیمات سفارشی
        result = subprocess.run([
            sys.executable, '-m', 'pylint',
            '--output-format=text',
            '--reports=no',
            '--disable=invalid-name,missing-module-docstring,missing-function-docstring',
            '--enable=bad-indentation,unnecessary-semicolon,unused-variable',
            '--max-line-length=100',
            temp_path
        ], capture_output=True, text=True, timeout=10)

        return _parse_pylint_output(result.stdout, result.stderr)
    except subprocess.TimeoutExpired:
        return {"error": "⏰ تحلیل کیفیت زمان‌بر بود."}
    except Exception as e:
        return {"error": f"💥 خطا در تحلیل: {type(e).name}"}
    finally:
        try:
            os.unlink(temp_path)
        except:
            pass

def _parse_pylint_output(stdout: str, stderr: str) -> dict:
    """پردازش خروجی pylint به ساختار قابل نمایش"""
    if stderr and "error" in stderr.lower():
        return {"error": f"pylint error: {stderr[:200]}"}

    # استخراج نمره (مثلاً "Your code has been rated at 8.50/10")
    score_match = re.search(r"rated at (\d+\.\d+)/10", stdout)
    score = float(score_match.group(1)) if score_match else 10.0

    # دسته‌بندی پیام‌ها
    warnings = []
    conventions = []
    refactor = []
    error_count = 0

    for line in stdout.splitlines():
        if ": W" in line:  # Warning
            msg = _extract_message(line)
            if msg: warnings.append(f"⚠️ {msg}")
        elif ": C" in line:  # Convention
            msg = _extract_message(line)
            if msg: conventions.append(f"📝 {msg}")
        elif ": R" in line:  # Refactor
            msg = _extract_message(line)
            if msg: refactor.append(f"🔧 {msg}")
        elif "syntax error" in line.lower():
            error_count += 1

    return {
        "score": score,
        "warnings": warnings,
        "conventions": conventions,
        "refactor": refactor,
        "error_count": error_count
    }

def _extract_message(line: str) -> str:
    """استخراج متن پیام از خط pylint"""
    parts = line.split(":", 3)
    if len(parts) >= 4:
        return parts[3].strip()
    return line.strip()
