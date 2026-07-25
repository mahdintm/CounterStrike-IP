# CounterStrike-IP

این مخزن IPv4 رله‌های Counter-Strike 2 را از API رسمی Steam استخراج می‌کند. خروجی آماده در فایل [`ips.json`](ips.json) قرار دارد و شامل `revision`، زمان دریافت، تعداد و آرایهٔ IPها است.

## اجرای دستی

```bash
python3 scripts/update_ips.py --output ips.json
```

در اجرای موفق، تعداد IPها و revision در ترمینال چاپ می‌شود. برای تست بدون اینترنت نیز می‌توان پاسخ ذخیره‌شدهٔ Steam را به برنامه داد:

```bash
python3 scripts/update_ips.py --input steam-response.json --output ips.json
```

برای تست integration با API سازگار دیگر می‌توان آدرس را با متغیر محیطی تغییر داد:

```bash
STEAM_API_URL=http://127.0.0.1:8000/config.json python3 scripts/update_ips.py
```

اسکریپت پاسخ و تمام IPها را اعتبارسنجی می‌کند، موارد تکراری را حذف می‌کند، IPها را به‌ترتیب عددی می‌چیند و فایل را به‌شکل atomic می‌نویسد. درخواست ناموفق سه بار با فاصلهٔ افزایشی تکرار می‌شود.

## به‌روزرسانی خودکار

GitHub کمترین فاصلهٔ cron را پنج دقیقه در نظر می‌گیرد. workflow زمان‌بندی‌شده در هر job پنج بار، با فاصلهٔ دقیق ۶۰ ثانیه، API را دریافت می‌کند و هر خروجی را commit و push می‌کند. همچنین تعداد IP، revision و زمان دریافت در log و Job Summary نمایش داده می‌شود.

workflow روی شاخهٔ پیش‌فرض checkout می‌کند و دسترسی `contents: write` مورد نیاز را داخل خود فایل درخواست می‌کند. اگر سازمان یا branch protection اجازهٔ push به `github-actions[bot]` را مسدود کرده باشد، مدیر مخزن باید این bot را مجاز کند.

اجرای تست کامل محلی:

```bash
pytest -q
python3 -m unittest discover -s tests -v
python3 -m compileall -q scripts tests
```
