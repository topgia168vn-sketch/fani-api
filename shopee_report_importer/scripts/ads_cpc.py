# === PAS CPC EXPORT (EDGE-ONLY, VISIBLE) — mở PAS, chọn ngày, export, click "Tải dữ liệu" & chờ tải ===
import os, json, time, datetime, random, platform
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
DOWNLOAD_DIR = str((BASE_DIR / "downloads" / "ads_cpc").resolve())

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

TARGET_URL   = "https://banhang.shopee.vn/portal/marketing/pas/index?source_page_id=1"
HEADLESS = True  # <— Bật hiển thị: False. Nếu muốn chạy ẩn: True
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

# ========== JS: click 'Tải dữ liệu' ĐẦU TIÊN trong panel 'Báo cáo mới nhất' (KHÔNG scroll) ==========
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
const info = {
  tag:(btn.tagName||'').toLowerCase(),
  id:btn.id||null,
  cls:btn.className||null,
  name:btn.getAttribute('name'),
  type:btn.getAttribute('type'),
  role:btn.getAttribute('role'),
  aria:btn.getAttribute('aria-label'),
  text:textOf(btn),
  outer:(btn.outerHTML||'').slice(0,600)
};
try {
  btn.click();
  return {found:true, clicked:true, firstInPanel:true, buttonInfo:info};
} catch(e){
  try {
    btn.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
    return {found:true, clicked:true, via:'dispatch', firstInPanel:true, buttonInfo:info};
  } catch(e2){
    return {found:true, clicked:false, firstInPanel:true, error:String(e2), buttonInfo:info};
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


# --------- Logging helpers ----------
STEP_LOGS = []
RUN_ID = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

def now_iso():
    return datetime.datetime.now().isoformat(timespec="seconds")

def record(step_type, **info):
    entry = {"ts": now_iso(), "step": step_type, **info}
    STEP_LOGS.append(entry)
    def _shorten(v):
        if isinstance(v, str) and len(v) > 200: return v[:200] + "…"
        return v
    pretty = {k: _shorten(v) for k, v in entry.items()}
    print(f"[{entry['ts']}] {step_type} -> {pretty}")

def save_run_log():
    path = os.path.join(DOWNLOAD_DIR, f"RUN_LOG_{RUN_ID}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(STEP_LOGS, f, ensure_ascii=False, indent=2)
    print(f"▶ Log đã lưu: {path}")

def elem_info(driver, el):
    try:
        return driver.execute_script("""
            var e = arguments[0];
            function safe(v){return v===undefined||v===null?null:String(v);}
            return {
              tag: safe(e.tagName ? e.tagName.toLowerCase() : null),
              id: safe(e.id || null),
              cls: safe(e.className || null),
              name: safe(e.getAttribute('name')),
              type: safe(e.getAttribute('type')),
              role: safe(e.getAttribute('role')),
              aria: safe(e.getAttribute('aria-label')),
              text: (e.innerText || e.textContent || '').trim().slice(0,200),
              outer: (e.outerHTML || '').slice(0,500)
            };
        """, el)
    except Exception as e:
        return {"error": f"elem_info_failed: {e.__class__.__name__}"}

# ---------- Edge WebDriver (ONLY) ----------
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

    # --- NEW: Linux binary detection ---
    if platform.system() == "Linux":
        from shutil import which
        linux_edge_bins = [
            "/usr/bin/microsoft-edge-stable",
            "/usr/bin/microsoft-edge",
            "/opt/microsoft/msedge/msedge",
        ]
        edge_bin = next((p for p in linux_edge_bins if os.path.exists(p)), None) or which("microsoft-edge-stable") or which("microsoft-edge")
        if edge_bin:
            opts.binary_location = edge_bin

    # (Windows) Tuỳ chọn chỉ định msedge.exe nếu cần, còn không Selenium Manager sẽ tự lo.
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

    d = webdriver.Edge(options=opts)  # Selenium Manager tự tải msedgedriver nếu cần
    d.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    try:
        d.execute_cdp_cmd("Page.setDownloadBehavior",
                          {"behavior": "allow", "downloadPath": DOWNLOAD_DIR})
    except Exception:
        pass
    if not HEADLESS:
        try: d.maximize_window()
        except Exception: pass
    record("driver_init", browser="edge", prefs=prefs)
    return d

# ---------- Cookie, click, đợi ----------
def load_cookies(driver, cookies_path, base="https://banhang.shopee.vn"):
    if not os.path.exists(cookies_path):
        raise FileNotFoundError(f"Không tìm thấy file cookie: {cookies_path}")
    driver.get(base)
    with open(cookies_path, "r", encoding="utf-8") as f:
        cookies = json.load(f)
    added, skipped = 0, 0
    for c in cookies:
        if c.get("name") and c.get("value"):
            try:
                driver.add_cookie({
                    "name": c["name"], "value": c["value"],
                    "domain": c.get("domain"), "path": c.get("path", "/"),
                    "secure": c.get("secure", False), "httpOnly": c.get("httpOnly", False)
                })
                added += 1
            except Exception:
                skipped += 1
    driver.refresh()
    record("cookies_loaded", from_file=cookies_path, added=added, skipped=skipped)

def scroll_center(driver, el):
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)

def safe_click(driver, el, xpath=None, label=None):
    info = elem_info(driver, el)
    try:
        el.click()
        record("click", xpath=xpath, label=label, element=info, method="native")
    except Exception:
        driver.execute_script("arguments[0].click();", el)
        record("click", xpath=xpath, label=label, element=info, method="js")

def wait_click_any(d, xpaths, timeout=CLICK_TIMEOUT, label=None):
    end = time.time() + timeout
    last_err = None
    while time.time() < end:
        for xp in xpaths:
            try:
                el = WebDriverWait(d, 2).until(EC.element_to_be_clickable((By.XPATH, xp)))
                scroll_center(d, el)
                safe_click(d, el, xpath=xp, label=label or "click")
                return el
            except Exception as e:
                last_err = e
        time.sleep(0.2)
    raise last_err if last_err else TimeoutError(f"Không click được (label={label})")

def wait_click(d, xpath, timeout=CLICK_TIMEOUT, label=None):
    el = WebDriverWait(d, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
    scroll_center(d, el)
    safe_click(d, el, xpath=xpath, label=label or "click")
    return el

def pick_first_dropdown_item(d, timeout=CLICK_TIMEOUT, label="pick_first_dropdown"):
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
            d.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            try:
                el.click(); record("dropdown_pick", xpath=xp, label=label, element=elem_info(d, el), method="native")
            except Exception:
                d.execute_script("arguments[0].click();", el); record("dropdown_pick", xpath=xp, label=label, element=elem_info(d, el), method="js")
            return True
        except Exception as e:
            last_err = e
    try:
        ActionChains(d).pause(0.1).send_keys(Keys.ARROW_DOWN).pause(0.1).send_keys(Keys.ENTER).perform()
        record("dropdown_pick", label=label, method="keyboard", note="ARROW_DOWN+ENTER")
        return True
    except Exception:
        pass
    record("dropdown_pick_failed", label=label, error=str(last_err) if last_err else "unknown")
    raise last_err if last_err else TimeoutError("Không chọn được item đầu trong dropdown")

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
    files = [f for f in os.listdir(download_dir) if os.path.isfile(os.path.join(download_dir, f))]
    record("downloads_done", waited_seconds=waited, files=files)
    return files

# ---------- CHẠY TRÌNH TỰ ----------
def run():
    d = make_driver()
    try:
        # 0) nạp cookies & mở trang PAS
        load_cookies(d, COOKIES_JSON, base="https://banhang.shopee.vn")
        d.get(TARGET_URL); record("open_url", url=TARGET_URL, title=d.title)
        time.sleep(SLEEP_BEFORE_ACTIONS); record("sleep", seconds=SLEEP_BEFORE_ACTIONS, note="wait UI init")
        human_space(0.6, 1.6, "before_click_first_download")
        # 1) mở dropdown ngày -> 2) chọn item đầu
        wait_click_any(d, X1_OPEN_SELECT_CANDIDATES, label="open_first_dropdown")
        try:
            wait_click(d, DATE_SHORTCUT_FIRST, label="pick_date_shortcut_first")
        except Exception:
            pick_first_dropdown_item(d, label="pick_first_dropdown_item")
        human_space(0.6, 1.6, "before_click_first_download")
        # 3) mở dropdown 'Tải dữ liệu' -> 4) chọn mục đầu
        wait_click(d, OPEN_EXPORT_DROPDOWN, label="open_export_dropdown")
        human_space(0.6, 1.6, "before_click_first_download")
        wait_click(d, EXPORT_ITEM_FIRST, label="pick_export_item_first")

        # Ảnh debug


        # 4.5) nếu tải tự diễn ra (có .crdownload/.tmp) thì bỏ qua bước panel
        started = False
        for _ in range(30):  # ~15s
            if tmp_download_started(DOWNLOAD_DIR):
                record("download_appeared", note="Detected temp -> skip panel click")
                started = True
                break
            time.sleep(0.5)

        # 5) nếu chưa, CLICK 'Tải dữ liệu' trong panel 'Báo cáo mới nhất' (KHÔNG scroll, có retry)
        if not started:
            res = d.execute_script(JS_CLICK_FIRST_DL_IN_REPORT_PANEL)
            record("panel_click_probe", result=res)
            if not res.get("found", False) or not res.get("clicked", False):
                end = time.time() + 20
                clicked = res.get("clicked", False)
                while time.time() < end and not clicked:
                    time.sleep(0.5)
                    res = d.execute_script(JS_CLICK_FIRST_DL_IN_REPORT_PANEL)
                    if res.get("clicked", False):
                        record("panel_click_retry_ok", result=res); clicked = True; break
                if not clicked:
                    record("panel_click_failed", last_result=res)

        # 6) chờ file tải xong
        files = wait_for_downloads(DOWNLOAD_DIR, min_seconds=2, max_wait=240)
        print("Downloaded files:", files)
    finally:
        try:
            save_run_log()
        finally:
            d.quit()

# GỌI CHẠY
run()
