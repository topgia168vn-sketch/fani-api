# === ORDER EXPORT (STANDALONE WITH COOKIES) — Home -> Order -> Export -> DateRange (today-2) -> Confirm -> Wait -> Download ===
import os, json, time, sys, random
from typing import Optional
from pathlib import Path
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException

# --- múi giờ VN (tùy chọn) ---
try:
    from zoneinfo import ZoneInfo  # Py3.9+
except Exception:
    try:
        from tzdata import __version__  # noqa
        from zoneinfo import ZoneInfo
    except Exception:
        ZoneInfo = None

# ------------------ CẤU HÌNH ------------------
BASE_URL  = "https://banhang.shopee.vn/"
ORDER_URL = "https://banhang.shopee.vn/portal/sale/order"

HEADLESS = True
PAGE_LOAD_TIMEOUT = 60
CLICK_TIMEOUT = 45

BASE_DIR = Path.cwd()
COOKIES_JSON = BASE_DIR / "cookies_shopee.json"

DOWNLOAD_DIR = BASE_DIR / "downloads" / "order"

DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ------------------ LOG NHẸ ------------------
def rec(step, **kw):
    print({"step": step, **kw})

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

# ------------------ DRIVER ------------------
def make_driver():
    last_err = None

    def build_edge():
        from selenium.webdriver.edge.options import Options as EdgeOptions
        opts = EdgeOptions()
        if HEADLESS: opts.add_argument("--headless=new")
        else:        opts.add_argument("--start-maximized")
        opts.add_argument("--no-sandbox"); opts.add_argument("--disable-dev-shm-usage")
        opts.add_experimental_option("prefs", {
            "download.default_directory": str(DOWNLOAD_DIR),
            "download.prompt_for_download": False,
            "safebrowsing.enabled": True,
        })
        d = webdriver.Edge(options=opts)
        return d

    def build_chrome():
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        opts = ChromeOptions()
        if HEADLESS: opts.add_argument("--headless=new")
        else:        opts.add_argument("--start-maximized")
        opts.add_argument("--no-sandbox"); opts.add_argument("--disable-dev-shm-usage")
        opts.add_experimental_option("prefs", {
            "download.default_directory": str(DOWNLOAD_DIR),
            "download.prompt_for_download": False,
            "safebrowsing.enabled": True,
        })
        d = webdriver.Chrome(options=opts)
        return d

    for name, builder in (("edge", build_edge), ("chrome", build_chrome)):
        try:
            d = builder()
            d.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
            try:
                d.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior":"allow","downloadPath":str(DOWNLOAD_DIR)})
            except Exception:
                pass
            rec("driver_init", browser=name)
            return d
        except Exception as e:
            last_err = e
            rec("driver_fail", browser=name, error=str(e))
    raise RuntimeError(f"Không khởi tạo được trình duyệt. LastErr={last_err}")

# ------------------ HELPERS CHUNG ------------------
def wait_dom_ready(d, timeout=PAGE_LOAD_TIMEOUT):
    WebDriverWait(d, timeout).until(lambda drv: drv.execute_script("return document.readyState") == "complete")
    rec("dom_ready")

def click_css_stable(d, selector, label, timeout=CLICK_TIMEOUT, attempts=12):
    """
    Click CSS: ưu tiên JS click -> nếu fail, tìm fresh element & native click (fallback JS).
    """
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

def _double_click(d, el):
    try:
        ActionChains(d).double_click(el).perform()
        return "actionchains"
    except Exception:
        d.execute_script("""
            const el = arguments[0];
            const ev = new MouseEvent('dblclick', {bubbles:true, cancelable:true});
            el.dispatchEvent(ev);
        """, el)
        return "js_dblclick"

def _find_day_cell_in_panel(d, panel_root_css: str, day: int, timeout=CLICK_TIMEOUT):
    """
    Tìm cell 'span.eds-date-table__cell-inner.normal' có text = day trong panel chỉ định.
    """
    end = time.time() + timeout
    target_text = str(int(day))
    last_err = None
    selector = (
        f"{panel_root_css} div.eds-date-table div.eds-date-table__rows "
        f"div div span.eds-date-table__cell-inner.normal"
    )
    while time.time() < end:
        try:
            cells = d.find_elements(By.CSS_SELECTOR, selector)
            for c in cells:
                try:
                    if not c.is_displayed():
                        continue
                    txt = (c.text or c.get_attribute("textContent") or "").strip()
                    if txt == target_text:
                        try: d.execute_script("arguments[0].scrollIntoView({block:'center'});", c)
                        except Exception: pass
                        return c
                except Exception as e:
                    last_err = e
        except Exception as e:
            last_err = e
        time.sleep(0.15)
    raise TimeoutError(f"Không thấy cell ngày = {target_text} trong panel {panel_root_css}. LastErr={last_err}")

def pick_today_minus_2_daterange_by_rule(d, timeout=CLICK_TIMEOUT):
    """
    - Nếu month(today-2) != month(today)  => double-click panel TRÁI
    - Nếu month(today-2) == month(today)  => double-click panel PHẢI
    """
    tz = None
    try:
        tz = ZoneInfo("Asia/Ho_Chi_Minh")
    except Exception:
        pass
    now = datetime.now(tz) if tz else datetime.now()
    target = now - timedelta(days=2)
    same_month = (target.year == now.year and target.month == now.month)
    panel_css = "div.eds-daterange-picker-panel__body-right" if same_month \
                else "div.eds-daterange-picker-panel__body-left"
    human_space(0.4, 0.9, "before_pick_today_minus_2")
    cell = _find_day_cell_in_panel(d, panel_css, target.day, timeout=timeout)
    how = _double_click(d, cell)
    rec("daterange_double_click", panel=("right" if same_month else "left"),
        target=str(target.date()), method=how)

def tmp_download_started(dirp):
    try:
        return any(n.endswith((".crdownload", ".tmp")) for n in os.listdir(dirp))
    except Exception:
        return False

def wait_for_downloads(download_dir, min_seconds=2, max_wait=240):
    time.sleep(min_seconds)
    waited = min_seconds
    while waited < max_wait:
        if not tmp_download_started(download_dir):
            break
        time.sleep(1); waited += 1
    files = [f for f in os.listdir(download_dir) if os.path.isfile(os.path.join(download_dir, f))]
    rec("downloads_done", waited_seconds=waited, files=files)
    return files

# ------------------ COOKIE HELPERS ------------------
def save_current_cookies(d, path: Path):
    try:
        cookies = d.get_cookies()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        rec("cookies_saved", file=str(path), count=len(cookies))
    except Exception as e:
        rec("cookies_save_fail", error=str(e))

def load_or_login_then_save_cookies(d):
    """
    Nếu có cookies_shopee.json → load vào domain rồi refresh.
    Nếu KHÔNG → mở BASE_URL để bạn đăng nhập thủ công, bấm Enter để tiếp tục và lưu cookie.
    """
    d.get(BASE_URL)
    wait_dom_ready(d)
    if COOKIES_JSON.exists():
        try:
            with open(COOKIES_JSON, "r", encoding="utf-8") as f:
                for c in json.load(f):
                    if c.get("name") and c.get("value"):
                        try:
                            d.add_cookie({
                                "name": c["name"], "value": c["value"],
                                "domain": c.get("domain"), "path": c.get("path", "/"),
                                "secure": c.get("secure", False), "httpOnly": c.get("httpOnly", False)
                            })
                        except Exception:
                            pass
            d.refresh()
            wait_dom_ready(d)
            rec("cookies_loaded", from_file=str(COOKIES_JSON))
            return
        except Exception as e:
            rec("cookies_load_fail", error=str(e))

    # Không có cookie → để bạn login thủ công
    print("\n=== VUI LÒNG ĐĂNG NHẬP TRÊN TRÌNH DUYỆT VỪA MỞ ===")
    print("Sau khi đăng nhập thành công và thấy giao diện Seller Center, quay lại terminal và nhấn Enter…")
    input("Nhấn Enter để tiếp tục và lưu cookie: ")
    d.get(BASE_URL)  # đảm bảo đúng domain
    wait_dom_ready(d)
    save_current_cookies(d, COOKIES_JSON)

# ------------------ MAIN: theo trình tự bạn yêu cầu + cookies ------------------
def run_order_export_with_cookies():
    d = make_driver()
    try:
        # 0) đăng nhập (nạp cookie hoặc login thủ công rồi lưu)
        load_or_login_then_save_cookies(d)
        human_space(0.6, 1.4, "after_home_ready")

        # 1) đến url: /portal/sale/order
        d.get(ORDER_URL)
        wait_dom_ready(d)
        human_space(0.5, 1.2, "after_nav_order")

        # 2) click button có class: export và export-with-modal
        click_css_stable(d, "button.export.export-with-modal", "open_export_modal", timeout=15, attempts=8)
        wait_dom_ready(d)
        human_space(0.4, 1.0, "after_open_export_modal")

        # 3) click div có class: eds-date-picker__input (mở date range picker)
        click_css_stable(d, "div.eds-date-picker__input div", "open_daterange_input", timeout=10, attempts=8)
        human_space(0.4, 0.9, "after_open_daterange_input")

        # 4) nếu tháng today-2 khác/bằng tháng today -> double click cell tương ứng (panel trái/phải)
        pick_today_minus_2_daterange_by_rule(d, timeout=CLICK_TIMEOUT)

        # 5) click div.eds-modal__footer > div > button (confirm export)
        human_space(0.6, 1.3, "before_confirm_export")
        click_css_stable(d, "div.eds-modal__footer > div > button", "confirm_export", timeout=15, attempts=8)

        # 6) đợi 30s (backend xử lý export)
        rec("wait_backend_export", seconds=30)
        time.sleep(30)

        # 7) click nút download: export list → hàng 1, cột 2 → button
        human_space(0.6, 1.6, "before_click_first_download")
        download_btn_selector = (
            "div.export-container > div.eds-table.list > "
            "div.eds-table__body-container > div.eds-table__main-body > "
            "div > div > div.eds-scrollbar__content > table > tbody > "
            "tr:first-child > td:nth-child(2) > div > div > button"
        )
        click_css_stable(d, download_btn_selector, "download_first_row_col2_btn", timeout=20, attempts=10)

        # 8) đợi tải xong (lưu file trong DOWNLOAD_DIR)
        for _ in range(30):
            if tmp_download_started(str(DOWNLOAD_DIR)):
                rec("download_appeared", note="temp file detected")
                break
            time.sleep(0.5)
        wait_for_downloads(str(DOWNLOAD_DIR), min_seconds=2, max_wait=240)
        rec("download_completed", dir=str(DOWNLOAD_DIR))

    finally:
        try: d.quit()
        except Exception: pass

# ---- RUN ----
if __name__ == "__main__":
    run_order_export_with_cookies()
