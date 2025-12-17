# src/utils/exercise_evaluator.py
import json
import re

def evaluate_exercise(code: str, test_cases: str, exercise_id: int) -> dict:
    try:
        test_list = json.loads(test_cases)
    except:
        return {"error": "❌ خطای داخلی: تست‌کیس نامعتبر"}

    # نام تابع مورد انتظار بر اساس شماره تمرین
    expected_funcs = {
        1: "add", 2: "max3", 3: "fact", 4: "reverse",
        5: "fib", 6: "average", 7: "unique",
        8: "bubble_sort", 9: "binary_search", 10: "hanoi"
    }
    func_name = expected_funcs.get(exercise_id, "solution")

    if f"def {func_name}" not in code:
        return {"error": f"❌ تابعی به نام {func_name} تعریف نکرده‌اید."}

    # فضای اجرایی محدود
    restricted_globals = {
        "builtins": {
            "print": print, "len": len, "range": range, "int": int,
            "float": float, "str": str, "list": list, "dict": dict,
            "set": set, "tuple": tuple, "bool": bool, "abs": abs,
            "max": max, "min": min, "sum": sum, "sorted": sorted,
            "ValueError": ValueError, "TypeError": TypeError,
            "IndexError": IndexError
        }
    }

    try:
        exec(code, restricted_globals)
        if func_name not in restricted_globals:
            return {"error": f"❌ تابع {func_name} پس از اجرا یافت نشد."}
        user_func = restricted_globals[func_name]
    except Exception as e:
        return {"error": f"❌ خطا در تعریف تابع: {type(e).name}"}

    # ارزیابی تست‌کیس‌ها
    passed = []
    failed = []
    for i, tc in enumerate(test_list):
        try:
            result = user_func(*tc["input"])
            expected = tc["expected"]
            if result == expected:
                passed.append(i+1)
            else:
                failed.append({
                    "case": i+1, "input": tc["input"],
                    "expected": expected, "got": result
                })
        except Exception as e:
            failed.append({
                "case": i+1, "input": tc["input"],
                "error": f"{type(e).name}"
            })

    return {
        "score": len(passed),
        "total": len(test_list),
        "passed": passed,
        "failed": failed,
        "func_name": func_name
    }