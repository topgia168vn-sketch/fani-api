# === Booking (LOCAL) — điều hướng menu (chống stale), chọn today-2, xuất + tải dữ liệu (Edge/Chrome, snapshots) ===
import os, json, time, sys
import datetime as dt
from pathlib import Path
from datetime import datetime, timedelta
import random
from typing import Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.common.exceptions import StaleElementReferenceException

try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except Exception:
    try:
        from tzdata import __version__  # noqa: F401
        from zoneinfo import ZoneInfo
    except Exception:
        ZoneInfo = None

# ------------------ ĐƯỜNG DẪN LOCAL ------------------
BASE_DIR = Path(__file__).resolve().parent
COOKIES_JSON = BASE_DIR / "cookies_shopee.json"
DOWNLOAD_DIR = BASE_DIR / "downloads" / "booking"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ------------------ CẤU HÌNH ------------------
BASE_URL = "https://banhang.shopee.vn/"
HEADLESS = False
PAGE_LOAD_TIMEOUT = 60
CLICK_TIMEOUT = 45

# ------------------ LOG ------------------
STEP_LOGS = []
RUN_ID = dt.datetime.now().strftime("%Y%m%d-%H%M%S")

def now_iso():
    return dt.datetime.now().isoformat(timespec="seconds")

def rec(step, **kw):
    entry = {"ts": now_iso(), "step": step, **kw}
    STEP_LOGS.append(entry)
    print(entry)


def human_pause(min_s: float = 0.4, max_s: float = 1.1, label: Optional[str] = None) -> float:
    """Tạm dừng ngẫu nhiên để dịu nhịp thao tác/SPA render."""
    try:
        t = random.uniform(min_s, max_s)
    except Exception:
        t = (min_s + max_s) / 2.0
    if label:
        rec("human_pause", label=label, seconds=round(t, 2))
    time.sleep(t)
    return t

# ------------------ VIRTUAL DISPLAY SETUP ------------------
def setup_virtual_display():
    """Setup virtual display for non-headless mode on server"""
    if not HEADLESS and not os.environ.get('DISPLAY'):
        try:
            import subprocess
            # Check if Xvfb is already running
            result = subprocess.run(['pgrep', 'Xvfb'], capture_output=True)
            if result.returncode != 0:
                # Start Xvfb virtual display
                subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1366x768x24'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(2)  # Wait for Xvfb to start
            os.environ['DISPLAY'] = ':99'
            rec("virtual_display_setup", display=":99")
        except Exception as e:
            rec("virtual_display_fail", error=str(e))

# ------------------ DRIVER (EDGE ưu tiên, fallback CHROME) ------------------
def make_driver():
    # Setup virtual display for non-headless mode
    setup_virtual_display()

    browser = (os.environ.get("BROWSER") or "edge").lower()
    last_err = None

    def build_edge():
        from selenium.webdriver.edge.options import Options as EdgeOptions
        import tempfile
        import uuid

        opts = EdgeOptions()

        # Basic server options
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")

        # Create unique user data directory for each session (FIXES THE MAIN ISSUE)
        unique_user_data_dir = os.path.join(tempfile.gettempdir(), f"edge_user_data_{uuid.uuid4().hex[:8]}")
        opts.add_argument(f"--user-data-dir={unique_user_data_dir}")

        # Remote debugging port (unique for each session)
        debug_port = 9222 + (os.getpid() % 1000)
        opts.add_argument(f"--remote-debugging-port={debug_port}")

        if HEADLESS:
            opts.add_argument("--headless=new")
        else:
            # For non-headless on server, use virtual display
            if not os.environ.get('DISPLAY'):
                os.environ['DISPLAY'] = ':99'
            opts.add_argument("--start-maximized")

        opts.add_experimental_option("prefs", {
            "download.default_directory": str(DOWNLOAD_DIR),
            "download.prompt_for_download": False,
            "safebrowsing.enabled": True,
        })

        d = webdriver.Edge(options=opts)
        return d

    def build_chrome():
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        import tempfile
        import uuid

        opts = ChromeOptions()

        # Basic server options
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")

        # Create unique user data directory for each session (FIXES THE MAIN ISSUE)
        unique_user_data_dir = os.path.join(tempfile.gettempdir(), f"chrome_user_data_{uuid.uuid4().hex[:8]}")
        opts.add_argument(f"--user-data-dir={unique_user_data_dir}")

        # Remote debugging port (unique for each session)
        debug_port = 9223 + (os.getpid() % 1000)
        opts.add_argument(f"--remote-debugging-port={debug_port}")

        if HEADLESS:
            opts.add_argument("--headless=new")
        else:
            # For non-headless on server, use virtual display
            if not os.environ.get('DISPLAY'):
                os.environ['DISPLAY'] = ':99'
            opts.add_argument("--start-maximized")

        opts.add_experimental_option("prefs", {
            "download.default_directory": str(DOWNLOAD_DIR),
            "download.prompt_for_download": False,
            "safebrowsing.enabled": True,
        })

        d = webdriver.Chrome(options=opts)
        return d

    for name in ([browser] + (["chrome"] if browser != "chrome" else []) + (["edge"] if browser != "edge" else [])):
        try:
            d = build_edge() if name == "edge" else build_chrome()
            d.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
            try:
                d.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior":"allow","downloadPath":str(DOWNLOAD_DIR)})
            except Exception:
                pass
            rec("driver_init", browser=name)
            return d
        except Exception as e:
            last_err = e
            rec("driver_init_fail", browser=name, error=str(e))

    raise RuntimeError(f"Không khởi tạo được trình duyệt. LastErr={last_err}")

# ------------------ HELPERS CHUNG ------------------
def wait_dom_ready(d, timeout=PAGE_LOAD_TIMEOUT):
    WebDriverWait(d, timeout).until(lambda drv: drv.execute_script("return document.readyState") == "complete")
    rec("dom_ready")

def click_css_stable(d, selector, label, timeout=CLICK_TIMEOUT, attempts=12):
    """
    Click theo CSS chống-stale:
    1) Ưu tiên JS (querySelector + click).
    2) Nếu fail: tìm fresh element, native click → fallback JS. Có retry.
    """
    end = time.time() + timeout
    tries = 0
    last_err = None
    while time.time() < end and tries < attempts:
        tries += 1
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

        try:
            el = WebDriverWait(d, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            WebDriverWait(d, 2).until(lambda drv: el.is_displayed())
            try:
                d.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            except Exception:
                pass
            try:
                el.click(); m = "native"
            except (StaleElementReferenceException, Exception):
                d.execute_script("arguments[0].click();", el); m = "js"
            rec("click_css_fresh", label=label, selector=selector, method=m, attempt=tries)
            return True
        except Exception as e:
            last_err = e
            time.sleep(0.25)
    raise TimeoutError(f"Không click được phần tử hiển thị theo CSS: {selector}. LastErr={last_err}")

def hover_css(d, selector, timeout=CLICK_TIMEOUT):
    el = WebDriverWait(d, timeout).until(EC.visibility_of_element_located((By.CSS_SELECTOR, selector)))
    try: d.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    except Exception: pass
    ActionChains(d).move_to_element(el).perform()
    rec("hover_css", selector=selector)
    return el

def click_by_text_exact(d, text, timeout=CLICK_TIMEOUT):
    xp = f"//*[self::button or self::a or self::span or self::div][normalize-space(text())='{text}']"
    el = WebDriverWait(d, timeout).until(EC.element_to_be_clickable((By.XPATH, xp)))
    try: d.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    except Exception: pass
    try: el.click(); m = "native"
    except Exception:
        d.execute_script("arguments[0].click();", el); m = "js"
    rec("click_text_exact", text=text, method=m)
    return el

# ------------------ DATEPICKER: chọn today-2 ------------------
def _click_eds_day_cell_by_value(d, day, timeout=CLICK_TIMEOUT):
    WebDriverWait(d, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR,
            "div.eds-react-date-picker__table-cell-wrap div.eds-react-date-picker__table-cell"))
    )
    cells = d.find_elements(By.CSS_SELECTOR,
        "div.eds-react-date-picker__table-cell-wrap div.eds-react-date-picker__table-cell")
    target_text = str(int(day))
    target = None
    for c in cells:
        try:
            cls = (c.get_attribute("class") or "").lower()
            if "disabled" in cls: continue
            if not c.is_displayed(): continue
            if (c.text or "").strip() == target_text:
                target = c; break
        except Exception:
            continue
    if not target:
        raise TimeoutError(f"Không tìm thấy ô ngày có giá trị = {target_text}")
    try: target.click(); m = "native"
    except Exception:
        d.execute_script("arguments[0].click();", target); m = "js"
    rec("click_eds_day_cell", day=int(day), method=m)

def pick_d_minus_2_live(d, timeout=CLICK_TIMEOUT):
    shortcut_sel = "ul.eds-react-date-picker-shortcut-list.with-display-text li:nth-child(6)"
    try:
        hover_css(d, shortcut_sel, timeout=timeout)
    except Exception:
        pass


    now = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")) if ZoneInfo else datetime.now()
    target = now - timedelta(days=2)
    same_month = (target.year == now.year) and (target.month == now.month)
    rec("date_target", today=str(now.date()), target=str(target.date()), same_month=same_month)

    if not same_month:
        prev_sel = "div.eds-react-date-picker__header > div:nth-child(2) > span > svg"
        click_css_stable(d, prev_sel, "datepicker_prev_svg", timeout=timeout, attempts=6)


    _click_eds_day_cell_by_value(d, target.day, timeout=timeout)


# ------------------ DOWNLOAD HELPERS ------------------
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

# ------------------ COOKIE HELPERS (LOCAL) ------------------
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

    print("\n=== VUI LÒNG ĐĂNG NHẬP TRÊN TRÌNH DUYỆT VỪA MỞ ===")
    print("Sau khi đăng nhập thành công và thấy giao diện Seller Center, quay lại cửa sổ terminal và nhấn Enter...")
    input("Nhấn Enter để tiếp tục và lưu cookie: ")
    d.get(BASE_URL)
    wait_dom_ready(d)
    save_current_cookies(d, COOKIES_JSON)

# ------------------ MAIN FLOW ------------------
def run_flow():
    d = make_driver()
    try:
        # 0) Cookie + vào BASE_URL
        load_or_login_then_save_cookies(d)
        human_pause(0.6, 1.4, "after_login_ready")

        # 1) Điều hướng trực tiếp đến trang analytics (đang dùng deep link)
        wait_dom_ready(d)
        time.sleep(5)
        d.get("https://banhang.shopee.vn/portal/web-seller-affiliate/product_analytics")
        human_pause(0.5, 1.2, "before_nav")

        # 2) Mở datepicker input
        click_css_stable(
            d,
            "div.eds-react-date-picker__input.eds-react-date-picker__input--normal",
            "open_datepicker_input",
            timeout=10,
            attempts=8
        )

        # 3) Chọn ngày today-2
        pick_d_minus_2_live(d)
        human_pause(0.6, 1.4, "after_nav_product_analytics")

        # 4) Click button "Xuất dữ liệu"
        click_by_text_exact(d, "Xuất dữ liệu", timeout=15)
        wait_dom_ready(d)

        # 5) Đợi thêm 5 giây cho backend xử lý
        time.sleep(5); rec("sleep_extra", seconds=5)
        human_pause(0.5, 1.2, "before_open_datepicker")

        # 6) Click nút download ở hàng đầu tiên, cột 4
        click_css_stable(
            d,
            "div.eds-react-table-content table tbody tr:first-child td:nth-child(4) div button",
            "download_first_row_btn",
            timeout=15,
            attempts=10
        )

        # 7) Chờ file tải xong
        for _ in range(30):
            if tmp_download_started(str(DOWNLOAD_DIR)):
                rec("download_appeared", note="temp file detected")
                break
            time.sleep(0.5)
        wait_for_downloads(str(DOWNLOAD_DIR), min_seconds=2, max_wait=240)

    finally:
        try: d.quit()
        except Exception: pass

# ---- RUN ----
if __name__ == "__main__":
    try:
        run_flow()
    except KeyboardInterrupt:
        print("\n🛑 Đã dừng bởi người dùng.")
        sys.exit(1)
