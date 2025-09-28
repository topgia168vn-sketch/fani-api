# === LẤY DỮ LIỆU QUẢNG CÁO LIVE — Edge only, no screenshots, no log files ===
import os, json, time, platform
from pathlib import Path
import random
from typing import Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ===================== CẤU HÌNH =====================
BASE_DIR     = Path.cwd()
COOKIES_JSON = str(BASE_DIR / "cookies_shopee.json")
DOWNLOAD_DIR = str((BASE_DIR / "downloads" / "ads_live").resolve())

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

BASE_URL   = "https://banhang.shopee.vn"
TARGET_URL = "https://banhang.shopee.vn/portal/marketing/pas/index?source_page_id=1"

HEADLESS = True   # Đặt True nếu muốn chạy ẩn
PAGE_LOAD_TIMEOUT = 60
CLICK_TIMEOUT = 45
SLEEP_BEFORE_ACTIONS = 10

# Mở dropdown ngày (xpath gốc + fallback bền)
X1_OPEN_SELECT_CANDIDATES = [
    "/html/body/div[1]/div[2]/div[2]/div[2]/div/div/div/div[3]/div[2]/div[2]/div[1]/div/div[1]/div[1]/div/div/div",
    "//div[contains(@class,'eds-selector')][.//text()[contains(.,'GMT') or contains(.,'Hôm nay')]][1]"
]
DATE_SHORTCUT_FIRST = "//li[contains(@class,'eds-date-shortcut-item')][1]"

# Dropdown export
OPEN_EXPORT_DROPDOWN = "//button[@data-testid='export-data-dropdown-trigger']"
EXPORT_ITEM_FIRST    = "//li[@data-testid='export-data-dropdown-item'][1]"

# Nút cần pre-click ngay sau khi vào trang (nếu cần)
PRE_CLICK_XPATH = "/html/body/div[1]/div[2]/div[2]/div[2]/div/div/div/div[3]/div[2]/div[1]/div[1]/div/div[1]/div[5]"

# ========== JS: click 'Tải dữ liệu' ĐẦU TIÊN trong panel 'Báo cáo mới nhất' (không scroll) ==========
JS_CLICK_FIRST_DL_IN_REPORT_PANEL = r"""
function isVisible(el){
  if(!el) return false;
  const s = window.getComputedStyle(el);
  if (s.display === 'none' || s.visibility === 'hidden' || parseFloat(s.opacity) === 0) return false;
  const r = el.getBoundingClientRect();
  return r.width > 1 && r.height > 1;
}
function textOf(el){
  return (el.innerText || el.textContent || '').trim().replace(/\s+/g,' ');
}
function hasReportHeader(el){
  let p = el, hops = 0;
  while (p && hops < 8){
    const t = textOf(p);
    if (/Báo cáo mới nhất/i.test(t)) return true;
    p = p.parentElement; hops++;
  }
  return false;
}
let cands = Array.from(document.querySelectorAll("button,a")).filter(b => {
  const txt = textOf(b);
  if (!/Tải dữ liệu/i.test(txt)) return false;
  if (b.getAttribute('data-testid') === 'export-data-dropdown-trigger') return false;
  return isVisible(b);
});
let btn = cands.find(hasReportHeader) || cands[0] || null;
if (!btn){
  return {found:false, reason:"no_visible_button"};
}
try {
  btn.click();
  return {found:true, clicked:true, firstInPanel:true};
} catch(e){
  try {
    btn.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
    return {found:true, clicked:true, via:'dispatch', firstInPanel:true};
  } catch(e2){
    return {found:true, clicked:false, firstInPanel:true, error:String(e2)};
  }
}
"""
def rec(*args, **kwargs):
    print("[LOG]", *args, kwargs if kwargs else "")
# <<<

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


# ===================== WEBDRIVER (EDGE ONLY) =====================
def make_driver():
    from selenium.webdriver.edge.options import Options as EdgeOptions
    opts = EdgeOptions()
    if HEADLESS:
        opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1366,768")
    else:
        opts.add_argument("--start-maximized")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")

    # (Windows) Tuỳ chọn chỉ định msedge.exe nếu muốn; nếu không Selenium Manager sẽ tự lo.
    if platform.system() == "Windows":
        for p in (
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        ):
            if os.path.exists(p):
                opts.binary_location = p
                break

    prefs = {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "safebrowsing.enabled": True,
    }
    opts.add_experimental_option("prefs", prefs)

    d = webdriver.Edge(options=opts)  # Selenium Manager sẽ tự tải msedgedriver nếu cần
    d.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    try:
        d.execute_cdp_cmd("Page.setDownloadBehavior",
                          {"behavior": "allow", "downloadPath": DOWNLOAD_DIR})
    except Exception:
        pass
    if not HEADLESS:
        try: d.maximize_window()
        except Exception: pass
    return d

# ===================== HELPERS =====================
def wait_click(d, xpath, timeout=CLICK_TIMEOUT):
    el = WebDriverWait(d, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
    try: d.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    except Exception: pass
    try:
        el.click()
    except Exception:
        d.execute_script("arguments[0].click();", el)
    return el

def wait_click_any(d, xpaths, timeout=CLICK_TIMEOUT):
    end = time.time() + timeout
    last_err = None
    while time.time() < end:
        for xp in xpaths:
            try:
                el = WebDriverWait(d, 2).until(EC.element_to_be_clickable((By.XPATH, xp)))
                try: d.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                except Exception: pass
                try: el.click()
                except Exception: d.execute_script("arguments[0].click();", el)
                return el
            except Exception as e:
                last_err = e
        time.sleep(0.2)
    if last_err: raise last_err
    raise TimeoutError("Không click được bằng bất kỳ XPath nào.")

def pick_first_dropdown_item(d, timeout=CLICK_TIMEOUT):
    candidates = [
        "//div[contains(@class,'el-select-dropdown') and not(contains(@style,'display: none'))]//li[contains(@class,'el-select-dropdown__item')][1]",
        "//div[contains(@class,'ant-select-dropdown') and not(contains(@style,'hidden'))]//div[contains(@class,'ant-select-item')][1]",
        "//*[(@role='listbox' or @role='menu') and not(contains(@style,'display: none'))]//li[1]",
        "(//div[not(contains(@style,'display: none'))]//li[1])[last()]",
    ]
    last_err = None
    for xp in candidates:
        try:
            el = WebDriverWait(d, timeout).until(EC.element_to_be_clickable((By.XPATH, xp)))
            try: d.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            except Exception: pass
            try:
                el.click()
            except Exception:
                d.execute_script("arguments[0].click();", el)
            return True
        except Exception as e:
            last_err = e
    # Fallback bàn phím
    try:
        ActionChains(d).pause(0.1).send_keys(Keys.ARROW_DOWN).pause(0.1).send_keys(Keys.ENTER).perform()
        return True
    except Exception:
        pass
    if last_err: raise last_err
    raise TimeoutError("Không chọn được item đầu trong dropdown.")

def tmp_download_started(dirpath):
    try:
        return any(n.endswith((".crdownload", ".tmp")) for n in os.listdir(dirpath))
    except Exception:
        return False

def wait_for_downloads(download_dir, min_seconds=2, max_wait=240):
    time.sleep(min_seconds)
    waited = min_seconds
    while waited < max_wait:
        names = os.listdir(download_dir)
        if not any(n.endswith((".crdownload", ".tmp")) for n in names):
            break
        time.sleep(1); waited += 1
    return [f for f in os.listdir(download_dir) if os.path.isfile(os.path.join(download_dir, f))]

def load_cookies(driver, cookies_path, base=BASE_URL):
    if not os.path.exists(cookies_path):
        raise FileNotFoundError(f"Không tìm thấy file cookie: {cookies_path}")
    driver.get(base)
    with open(cookies_path, "r", encoding="utf-8") as f:
        cookies = json.load(f)
    for c in cookies:
        if c.get("name") and c.get("value"):
            try:
                driver.add_cookie({
                    "name": c["name"], "value": c["value"],
                    "domain": c.get("domain"), "path": c.get("path", "/"),
                    "secure": c.get("secure", False), "httpOnly": c.get("httpOnly", False)
                })
            except Exception:
                pass
    driver.refresh()

# ===================== FLOW CHÍNH =====================
def run_with_pre_click_no_logs():
    d = make_driver()
    try:
        # 0) đăng nhập bằng cookie + mở trang
        load_cookies(d, COOKIES_JSON, base=BASE_URL)
        d.get(TARGET_URL)
        time.sleep(SLEEP_BEFORE_ACTIONS)
        human_space(0.6, 1.6, "before_click_first_download")
        # 0.5) Pre-click nếu có
        try:
            wait_click(d, PRE_CLICK_XPATH)
        except Exception:
            pass  # không cần/không thấy thì bỏ qua

        # 1) mở dropdown ngày -> 2) chọn item đầu
        wait_click_any(d, X1_OPEN_SELECT_CANDIDATES)
        try:
            wait_click(d, DATE_SHORTCUT_FIRST)
        except Exception:
            pick_first_dropdown_item(d)
        human_space(0.6, 1.6, "before_click_first_download")
        # 3) mở dropdown 'Tải dữ liệu' -> 4) chọn mục đầu
        wait_click(d, OPEN_EXPORT_DROPDOWN)
        human_space(0.6, 1.6, "before_click_first_download")
        wait_click(d, EXPORT_ITEM_FIRST)

        # 4.5) nếu đã bắt đầu tải thì bỏ qua bước panel
        started = False
        for _ in range(30):  # ~15s
            if tmp_download_started(DOWNLOAD_DIR):
                started = True
                break
            time.sleep(0.5)
        human_space(0.6, 1.6, "before_click_first_download")
        # 5) nếu chưa, click 'Tải dữ liệu' đầu tiên trong panel 'Báo cáo mới nhất' (không scroll, có retry)
        if not started:
            res = d.execute_script(JS_CLICK_FIRST_DL_IN_REPORT_PANEL)
            if not res.get("found", False) or not res.get("clicked", False):
                end = time.time() + 20
                while time.time() < end:
                    time.sleep(0.5)
                    res = d.execute_script(JS_CLICK_FIRST_DL_IN_REPORT_PANEL)
                    if res.get("clicked", False):
                        break

        # 6) chờ file tải xong
        files = wait_for_downloads(DOWNLOAD_DIR, min_seconds=2, max_wait=240)
        if files:
            print("Downloaded files:", files)
        else:
            print("No files downloaded.")
    finally:
        try:
            d.quit()
        except Exception:
            pass

# GỌI CHẠY
if __name__ == "__main__":
    run_with_pre_click_no_logs()
