# CounterStrike-IP

این مخزن آدرس‌های IPv4 رله‌های Counter-Strike 2 را از تنظیمات رسمی Steam استخراج می‌کند و در فایل [`ips.json`](ips.json) نگه می‌دارد.

## به‌روزرسانی خودکار

Workflow بلافاصله پس از merge شدن اسکریپت روی شاخهٔ پیش‌فرض و سپس هر پنج دقیقه اجرا می‌شود. در طول هر اجرا، پنج بار با فاصلهٔ ۶۰ ثانیه API را می‌خواند. اگر خروجی تغییر کرده باشد، فایل JSON را با کاربر `github-actions[bot]` روی شاخهٔ پیش‌فرض commit و push می‌کند. هر درخواست ناموفق تا سه بار retry می‌شود. این روش محدودیت حداقل فاصلهٔ پنج‌دقیقه‌ای cron در GitHub Actions را پوشش می‌دهد؛ با این حال زمان شروع job توسط GitHub تضمین‌شده نیست.
Workflow گیت‌هاب اکشن هر پنج دقیقه اجرا می‌شود و در طول هر اجرا، پنج بار با فاصلهٔ ۶۰ ثانیه API را می‌خواند. اگر خروجی تغییر کرده باشد، فایل JSON را با کاربر `github-actions[bot]` روی شاخهٔ پیش‌فرض commit و push می‌کند. این روش محدودیت حداقل فاصلهٔ پنج‌دقیقه‌ای cron در GitHub Actions را پوشش می‌دهد؛ با این حال زمان شروع job توسط GitHub تضمین‌شده نیست.

برای اجرای دستی:

```bash
python3 scripts/update_ips.py
```

خروجی شامل آدرس منبع، revision پاسخ Steam، تعداد IPها و آرایهٔ یکتای `ips` است. POPهایی که `relays` ندارند به‌صورت امن نادیده گرفته می‌شوند.

> برای push خودکار، در تنظیمات مخزن به مسیر **Settings → Actions → General → Workflow permissions** بروید و دسترسی **Read and write permissions** را فعال کنید. اگر شاخهٔ اصلی branch protection دارد، باید push توسط GitHub Actions نیز مجاز باشد.

> Workflowهای زمان‌بندی‌شده فقط از شاخهٔ پیش‌فرض اجرا می‌شوند. بنابراین ابتدا این تغییرات را merge کنید یا از تب **Actions**، workflow با نام **Update Counter-Strike relay IPs** را به‌صورت دستی روی شاخهٔ پیش‌فرض اجرا کنید. Workflow عمومی Conda فایل `ips.json` را تولید نمی‌کند.
