# CounterStrike-IP

Automatically fetches Counter-Strike 2 relay IPv4 addresses from Steam's SDR API. The repository publishes two ready-to-use outputs:

- [`ips.json`](ips.json): structured JSON with the Steam revision, update time, count, and sorted IP addresses.
- [`list.rsc`](list.rsc): a MikroTik RouterOS import script that refreshes the `CounterStrike` firewall address list.

## MikroTik automatic update

Paste this into a RouterOS terminal. Replace `<OWNER>` and `<REPOSITORY>` if this repository is forked or renamed:

```routeros
/tool fetch url="https://raw.githubusercontent.com/mahdintm/CounterStrike-IP/main/list.rsc" dst-path="list.rsc"
/import file-name="list.rsc"
/file remove "list.rsc"
```

To refresh automatically every 15 minutes, add a scheduler entry:

```routeros
/system scheduler add name="Update-CS2-IPs" interval=15m start-time=startup on-event="/tool fetch url=\"https://raw.githubusercontent.com/mahdintm/CounterStrike-IP/main/list.rsc\" dst-path=\"list.rsc\"; /import file-name=\"list.rsc\"; /file remove \"list.rsc\""
```

Each import first removes the old `CounterStrike` entries and then adds the current Steam relay IPs. Other firewall address lists are not modified.

## Run locally

```bash
python3 scripts/update_ips.py --output ips.json --mikrotik-output list.rsc
```

The updater validates all addresses, removes duplicates, sorts them numerically, and writes both files atomically. Failed requests are retried three times. A saved API response can be used without internet:

```bash
python3 scripts/update_ips.py --input steam-response.json
```

## Automation

The GitHub Actions workflow runs on the default branch, fetches Steam every 60 seconds while the job is active, generates both output files, commits changes, and pushes them using `GITHUB_TOKEN`. GitHub Actions only permits scheduled triggers every five minutes, so one job performs five updates separated by 60 seconds.

Repository **Settings → Actions → General → Workflow permissions** must allow **Read and write permissions**. Branch protection must also permit `github-actions[bot]` to push.

## Tests

```bash
pytest -q
python3 -m unittest discover -s tests -v
python3 -m compileall -q scripts tests
```

---

## فارسی

این مخزن IPهای رله Counter-Strike 2 را از API استیم دریافت می‌کند و دو خروجی آماده می‌سازد: فایل JSON در [`ips.json`](ips.json) و اسکریپت قابل import میکروتیک در [`list.rsc`](list.rsc).

### به‌روزرسانی خودکار میکروتیک

دستور زیر را در ترمینال RouterOS اجرا کنید و `<OWNER>` و `<REPOSITORY>` را با نام صاحب و مخزن جایگزین کنید:

```routeros
/tool fetch url="https://raw.githubusercontent.com/mahdintm/CounterStrike-IP/main/list.rsc" dst-path="list.rsc"
/import file-name="list.rsc"
/file remove "list.rsc"
```

برای اجرای خودکار هر ۱۵ دقیقه از دستور scheduler بخش انگلیسی بالا استفاده کنید. هنگام import فقط رکوردهای لیست `CounterStrike` پاک و با IPهای جدید جایگزین می‌شوند و لیست‌های دیگر تغییری نمی‌کنند.

workflow گیت‌هاب هر دو فایل `ips.json` و `list.rsc` را می‌سازد، commit می‌کند و روی شاخه اصلی push می‌کند. در تنظیمات Actions باید دسترسی **Read and write permissions** فعال باشد و branch protection نیز push ربات GitHub Actions را مسدود نکند.
