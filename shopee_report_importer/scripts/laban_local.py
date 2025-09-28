import os, re, json, requests, urllib.parse as up
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import datetime as dt
import random
from typing import Optional

# >>> THÊM IMPORT THIẾU
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
# <<<

# >>> LOG TỐI GIẢN
def rec(*args, **kwargs):
    print("[LOG]", *args, kwargs if kwargs else "")
# <<<

# >>> HẰNG SỐ DÙNG CHO HÀM
CLICK_TIMEOUT = 15
# <<<

def export_session_from_driver(driver):
    s = requests.Session()
    s.headers.update({
        "User-Agent": driver.execute_script("return navigator.userAgent"),
        "Referer": driver.current_url
    })
    for c in driver.get_cookies():
        if c.get("name") and c.get("value"):
            s.cookies.set(c["name"], c["value"], domain=c.get("domain"))
    cd = s.cookies.get_dict()
    for k in ("csrftoken","CTOKEN","XSRF-TOKEN"):
        if k in cd:
            for hk in ("X-CSRF-Token","X-CSRFToken","X-XSRF-TOKEN"):
                s.headers.setdefault(hk, cd[k])
            break
    return s

def filename_from_cd(cd, fallback="export.xlsx"):
    if not cd: return fallback
    m = re.search(r"filename\*?=((?:UTF-8'')?[^;]+)", cd, flags=re.I)
    if m:
        name = m.group(1).strip().strip('"')
        if name.lower().startswith("utf-8''"): name = name[7:]
        return os.path.basename(up.unquote(name))
    return fallback

def download_export(driver, export_url, outdir):
    os.makedirs(outdir, exist_ok=True)
    s = export_session_from_driver(driver)
    r = s.get(export_url, stream=True, timeout=180)
    r.raise_for_status()
    fname = filename_from_cd(r.headers.get("Content-Disposition"), "export.xlsx")
    path = os.path.join(outdir, fname)
    with open(path, "wb") as f:
        for chunk in r.iter_content(262_144):
            if chunk: f.write(chunk)
    print("Saved ->", path)
    return path

def load_cookies(driver, cookies_path, base="https://banhang.shopee.vn"):
    driver.get(base)
    with open(cookies_path, "r", encoding="utf-8") as f:
        cookies = json.load(f)
    for c in cookies:
        if c.get("name") and c.get("value"):
            try:
                # LỰA CHỌN 1: bỏ 'domain' để Selenium tự gắn cho domain hiện tại
                driver.add_cookie({
                    "name": c["name"], "value": c["value"],
                    "path": c.get("path", "/"),
                    "secure": c.get("secure", False),
                    "httpOnly": c.get("httpOnly", False)
                })
                # LỰA CHỌN 2 (nếu cần): truyền domain khi chắc chắn khớp
                # driver.add_cookie({
                #     "name": c["name"], "value": c["value"],
                #     "domain": c.get("domain"),
                #     "path": c.get("path", "/"),
                #     "secure": c.get("secure", False),
                #     "httpOnly": c.get("httpOnly", False)
                # })
            except Exception as e:
                rec("add_cookie_failed", name=c.get("name"), err=str(e))
    driver.refresh()

# === THỜI GIAN: hôm nay 00:00 đến (giờ hiện tại - 1h) làm tròn xuống giờ ===
tz = ZoneInfo("Asia/Bangkok")
now = datetime.now(tz)                           # KHÔNG trừ 1 ngày
end_raw = now - timedelta(hours=1)
end_floor = end_raw.replace(minute=0, second=0, microsecond=0)
start = now.replace(hour=0, minute=0, second=0, microsecond=0)
if end_floor < start:
    end_floor = start

start_ts = int(start.timestamp())
end_ts   = int(end_floor.timestamp())

EXPORT_URL = (
    "https://banhang.shopee.vn/datacenter/product/overview"
)
BASE_DIR     = Path.cwd()
COOKIES_JSON = str(BASE_DIR / "cookies_shopee.json")
DOWNLOAD_DIR = str(BASE_DIR / "downloads" / "laban")

# ====== cấu hình ======
HEADLESS = True  # ĐỂ THEO DÕI UI => False; chạy nền => True
WINDOW_SIZE = "1366,768"

opts = EdgeOptions()
if HEADLESS:
    opts.add_argument("--headless=new")
opts.add_argument("--window-size=" + WINDOW_SIZE)
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
# DevTools hữu ích khi debug UI
if not HEADLESS:
    opts.add_argument("--auto-open-devtools-for-tabs")

opts.add_experimental_option("prefs", {
    "download.default_directory": DOWNLOAD_DIR,
    "download.prompt_for_download": False,
    "safebrowsing.enabled": True,
})
driver = webdriver.Edge(options=opts)

# ------------------ PAUSE (jitter) ------------------
def human_pause(min_s: float = 0.4, max_s: float = 1.1, label: Optional[str] = None) -> float:
    try:
        t = random.uniform(min_s, max_s)
    except Exception:
        t = (min_s + max_s) / 2.0
    if label:
        rec("human_pause", label=label, seconds=round(t, 2))
    time.sleep(t)
    return t

# alias theo yêu cầu
def human_space(min_s: float = 0.4, max_s: float = 1.1, label: Optional[str] = None) -> float:
    return human_pause(min_s, max_s, label)

def click_css_stable(d, selector, label, timeout=CLICK_TIMEOUT, attempts=12):
    end = time.time() + timeout
    tries = 0
    last_err = None
    while time.time() < end and tries < attempts:
        tries += 1
        # JS-first
        try:
            clicked = d.execute_script("""
                const sel = arguments[0];
                const el = document.querySelector(sel);
                if (!el) return false;
                el.scrollIntoView({block:'center'});
                el.click();
                return true;
            """, selector)
            if clicked:
                rec("click_css_js", label=label, selector=selector, attempt=tries)
                return True
        except Exception as e:
            last_err = e
        # Fresh element
        try:
            el = WebDriverWait(d, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            WebDriverWait(d, 2).until(lambda drv: el.is_displayed())
            try: d.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            except Exception: pass
            try:
                el.click(); m = "native"
            except (StaleElementReferenceException, Exception):
                d.execute_script("arguments[0].click();", el); m = "js"
            rec("click_css_fresh", label=label, selector=selector, method=m, attempt=tries)
            return True
        except Exception as e:
            last_err = e
            time.sleep(0.25)
    raise TimeoutError(f"Không click được: {selector}. LastErr={last_err}")

def tmp_download_started(dirp):
    try:
        return any(n.endswith((".crdownload", ".tmp")) for n in os.listdir(dirp))
    except Exception:
        return False

def wait_for_downloads(download_dir, min_seconds=2, max_wait=240):
    os.makedirs(download_dir, exist_ok=True)
    time.sleep(min_seconds)
    waited = min_seconds
    while waited < max_wait:
        if not tmp_download_started(download_dir):
            break
        time.sleep(1); waited += 1
    files = [f for f in os.listdir(download_dir) if os.path.isfile(os.path.join(download_dir, f))]
    rec("downloads_done", waited_seconds=waited, files=files)
    return files

# ==== Luồng chính ====
load_cookies(driver, COOKIES_JSON, base="https://banhang.shopee.vn")
driver.get("https://banhang.shopee.vn/datacenter/product/overview")

# (A) GỌI API TRỰC TIẾP (bền hơn UI-click) — thử trước
human_space(0.6, 1.6, "before_click_first_download")
click_css_stable(driver, "div.bi-date-input.track-click-open-time-selector", "input date", timeout=15, attempts=8)
time.sleep(5)
human_space(0.6, 1.6, "before_click_first_download")
click_css_stable(driver, "div.eds-popper.eds-popover__popper.eds-popover__popper--light.bi-date-picker.datacenter-popper > div > div > ul > li.eds-date-shortcut-item.track-click-time-selector.edu-date-picker-option.active:first-child", "choose date", timeout=15, attempts=8)
time.sleep(5)
human_space(0.6, 1.6, "before_click_first_download")
click_css_stable(driver, "div.page-filters.sticky > div > div.page-filters__export-btn > button", "click download", timeout=20, attempts=10)

for _ in range(30):
        if tmp_download_started(DOWNLOAD_DIR):
            rec("download_appeared", note="temp file detected")
            break
        time.sleep(0.5)
wait_for_downloads(DOWNLOAD_DIR, min_seconds=2, max_wait=240)

driver.quit()
