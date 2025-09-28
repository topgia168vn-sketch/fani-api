# === Creator Center / Live / product-list — chọn hôm nay-2, thao tác dropdown mới, tải dữ liệu (Edge only, no logs) ===
import os, json, time, platform
from pathlib import Path
from datetime import datetime, timedelta
import random
from typing import Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains

try:
    from zoneinfo import ZoneInfo          # Py 3.9+
except Exception:
    try:
        from tzdata import __version__     # Windows thường cần tzdata
        from zoneinfo import ZoneInfo
    except Exception:
        ZoneInfo = None

# ------------------ CẤU HÌNH ------------------
# File cookie đặt cạnh file/script đang chạy
COOKIES_JSON = str((Path.cwd() / "cookies_shopee.json").resolve())

# Thư mục tải xuống an toàn trên Windows (Downloads/shopee)
DOWNLOAD_DIR = str((Path.cwd() / "downloads" / "live_product").resolve())
#DOWNLOAD_DIR =  "Downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

LIVE_URL = "https://banhang.shopee.vn/creator-center/insight/live/product-list"
HEADLESS = True                 # đặt True nếu muốn ẩn trình duyệt
PAGE_LOAD_TIMEOUT = 60
CLICK_TIMEOUT = 45
SLEEP_BEFORE_ACTIONS = 10

# XPaths dự phòng khi UI đổi
X_DATE_OPEN        = "/html/body/div[1]/div[2]/div[2]/div[2]/div/div/div/div/div/div/div/div[2]/div/div[2]/div[2]/div[1]/div/div[1]/div[1]/span[2]/div/div"
X_DOWNLOAD_BTN     = "/html/body/div[1]/div[2]/div[2]/div[2]/div/div/div/div/div/div/div/div[2]/div/div[2]/div[2]/div[1]/div/div[2]/div/div/button"

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


# ------------------ DRIVER (EDGE ONLY, áp dụng Hướng 1) ------------------
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

    # (Windows) chỉ định msedge.exe nếu cần (không bắt buộc)
    if platform.system() == "Windows":
        for p in (
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        ):
            if os.path.exists(p):
                opts.binary_location = p
                break

    # Cho phép tải nhiều file tự động, chặn notifications/popup, đặt thư mục tải
    prefs = {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "profile.default_content_setting_values.automatic_downloads": 1,
        "profile.default_content_setting_values.notifications": 2,  # block notification prompt
        "profile.default_content_setting_values.popups": 0,
    }
    opts.add_experimental_option("prefs", prefs)

    d = webdriver.Edge(options=opts)  # Selenium Manager sẽ tự xử lý msedgedriver
    d.set_page_load_timeout(PAGE_LOAD_TIMEOUT)

    # Cho phép download qua DevTools (đặc biệt hữu ích khi HEADLESS hoặc policy chặt)
    try:
        d.execute_cdp_cmd("Page.setDownloadBehavior",
                          {"behavior": "allow", "downloadPath": DOWNLOAD_DIR})
    except Exception:
        pass

    if not HEADLESS:
        try: d.maximize_window()
        except Exception: pass
    return d

# ------------------ HELPERS ------------------
def wait_dom_ready(d, timeout=PAGE_LOAD_TIMEOUT):
    WebDriverWait(d, timeout).until(lambda drv: drv.execute_script("return document.readyState") == "complete")

def wait_click(d, xpath, timeout=CLICK_TIMEOUT):
    el = WebDriverWait(d, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
    try: d.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    except Exception: pass
    try: el.click()
    except Exception: d.execute_script("arguments[0].click();", el)
    return el

def click_first_visible_css(d, selector, timeout=CLICK_TIMEOUT):
    end = time.time() + timeout
    last_err = None
    while time.time() < end:
        try:
            els = d.find_elements(By.CSS_SELECTOR, selector)
            for el in els:
                try:
                    if el.is_displayed():
                        try: d.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                        except Exception: pass
                        try: el.click()
                        except Exception: d.execute_script("arguments[0].click();", el)
                        return el
                except Exception as e:
                    last_err = e
        except Exception as e:
            last_err = e
        time.sleep(0.2)
    raise TimeoutError(f"Không click được phần tử hiển thị theo CSS: {selector}. LastErr={last_err}")

def hover_element(d, css_selector, timeout=CLICK_TIMEOUT):
    el = WebDriverWait(d, timeout).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_selector)))
    try: d.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    except Exception: pass
    ActionChains(d).move_to_element(el).perform()
    return el

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
    try: target.click()
    except Exception: d.execute_script("arguments[0].click();", target)

def scroll_to_bottom(d): d.execute_script("window.scrollTo(0, document.body.scrollHeight);")
def scroll_to_top(d):    d.execute_script("window.scrollTo(0, 0);")

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
    return [f for f in os.listdir(download_dir) if os.path.isfile(os.path.join(download_dir, f))]

def load_cookies(driver, cookies_path, base="https://banhang.shopee.vn"):
    if not os.path.exists(cookies_path):
        raise FileNotFoundError(f"Không tìm thấy file cookie: {cookies_path}")
    driver.get(base)
    wait_dom_ready(driver)
    with open(cookies_path, "r", encoding="utf-8") as f:
        cookies = json.load(f)
    for c in cookies:
        if c.get("name") and c.get("value"):
            try:
                driver.add_cookie({
                    "name": c["name"], "value": c["value"],
                    "domain": c.get("domain"),
                    "path": c.get("path", "/"),
                    "secure": c.get("secure", False),
                    "httpOnly": c.get("httpOnly", False)
                })
            except Exception:
                pass
    driver.refresh()
    wait_dom_ready(driver)

# ------------------ CHỌN NGÀY (today-2) ------------------
def pick_d_minus_2_live(d, timeout=CLICK_TIMEOUT):
    """
    Hover vào ul.eds-react-date-picker-shortcut-list.with-display-text li:nth-child(6) → click,
    sau đó chọn today-2 trong lưới ngày. Nếu khác tháng hiện tại thì bấm prev trước.
    """
    shortcut_sel = "ul.eds-react-date-picker-shortcut-list.with-display-text li:nth-child(6)"
    try:
        el = hover_element(d, shortcut_sel, timeout=timeout)
        try: el.click()
        except Exception: d.execute_script("arguments[0].click();", el)
    except Exception:
        pass

    now = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")) if ZoneInfo else datetime.now()
    target = now - timedelta(days=2)
    same_month = (target.year == now.year) and (target.month == now.month)

    if not same_month:
        prev_sel = "div.eds-react-date-picker__header > div:nth-child(2) > span > svg"
        btn = WebDriverWait(d, timeout).until(EC.element_to_be_clickable((By.CSS_SELECTOR, prev_sel)))
        try: d.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        except Exception: pass
        try: btn.click()
        except Exception: d.execute_script("arguments[0].click();", btn)

    _click_eds_day_cell_by_value(d, target.day, timeout=timeout)

# ------------------ MAIN FLOW ------------------
def run_flow():
    d = make_driver()
    try:
        # 0) cookie + vào trang chủ
        load_cookies(d, COOKIES_JSON, base="https://banhang.shopee.vn")
        human_space(0.6, 1.6, "before_click_first_download")
        # 1) mở trang đích và chờ UI init
        d.get(LIVE_URL)
        time.sleep(SLEEP_BEFORE_ACTIONS)
        wait_dom_ready(d)

        # 2) Mở datepicker
        wait_click(d, X_DATE_OPEN)
        time.sleep(0.25)
        human_space(0.6, 1.6, "before_click_first_download")
        # 3) Chọn today-2
        pick_d_minus_2_live(d)
        human_space(0.6, 1.6, "before_click_first_download")
        # 4) Cuộn xuống cuối trang → mở dropdown → chọn item 4 → cuộn lên đầu
        scroll_to_bottom(d)
        click_first_visible_css(d, "div.eds-react-dropdown")
        human_space(0.6, 1.6, "before_click_first_download")
        click_first_visible_css(d, "div.eds-react-popover-inner-content > div:nth-child(4)")
        wait_dom_ready(d)
        time.sleep(0.5)
        scroll_to_top(d)
        human_space(0.6, 1.6, "before_click_first_download")
        # 5) Click nút "Tải dữ liệu"
        wait_click(d, X_DOWNLOAD_BTN)

        # 6) Đợi tải xong
        for _ in range(30):       # ~15s dò file tạm
            if tmp_download_started(DOWNLOAD_DIR):
                break
            time.sleep(0.5)
        files = wait_for_downloads(DOWNLOAD_DIR, min_seconds=2, max_wait=240)
        print("Downloaded files:", files if files else "No files detected.")
    finally:
        try: d.quit()
        except Exception: pass

# ---- RUN ----
if __name__ == "__main__":
    run_flow()
