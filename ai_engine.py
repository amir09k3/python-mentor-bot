# src/utils/ai_engine.py
import subprocess
import sys

def query_llama3(prompt: str, max_tokens: int = 500) -> str:
    """
    ارسال سوال به Llama 3.1 با پشتیبانی از همه نسخه‌های Ollama
    """
    try:
        # تقویت prompt برای تمرکز روی پایتون
        full_prompt = (
            "شما یک استاد ماهر پایتون هستید. فقط به سوالات مربوط به پایتون پاسخ دهید. "
            "اگر سوال خارج از این حوزه بود، بگویید: «من فقط درباره پایتون کمک می‌کنم.»\n\n"
            f"سوال: {prompt}\n\nپاسخ:"
        )
        
        # استفاده از stdin به جای --prompt (سازگار با همه نسخه‌ها)
        result = subprocess.run(
            ["ollama", "run", "llama3.1:8b-instruct-q4_0"],
            input=full_prompt,
            capture_output=True,
            text=True,
            timeout=30,
            encoding='utf-8',
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            stderr_msg = result.stderr.strip()
            if "model 'llama3.1' not found" in stderr_msg:
                return "❌ مدل llama3.1 دانلود نشده. لطفاً اجرا کنید: ollama pull llama3.1"
            return f"⚠️ خطا: {stderr_msg[:200]}"
            
    except subprocess.TimeoutExpired:
        return "⏰ پاسخ‌دهی زمان‌بر بود. لطفاً سوال ساده‌تری بپرسید."
    except FileNotFoundError:
        return "❌ Ollama نصب نیست. لطفاً از https://ollama.com دانلود و نصب کنید."
    except Exception as e:
        return f"💥 خطا: {type(e).name}: {str(e)}"