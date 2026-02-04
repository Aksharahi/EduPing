import time
import requests
import pandas as pd
import re
import threading
import os
import json
import subprocess
from datetime import datetime
import platform

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# File parsing
from pathlib import Path

# Optional imports (used only if file type matches)
import docx
import pdfplumber


# =========================
# OLLAMA CONFIG
# =========================
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "phi"
OLLAMA_TIMEOUT = 120


# =========================
# WHATSAPP PROFILE (PERSISTENT)
# =========================
WHATSAPP_PROFILE_DIR = r"C:\eduping_whatsapp_profile"
PROFILE_LOCK_FILE = os.path.join(WHATSAPP_PROFILE_DIR, ".lock")
STATUS_FILE = os.path.join(WHATSAPP_PROFILE_DIR, ".status.json")


def clean_phone_num(phone):
    """Clean phone number and ensure proper format for WhatsApp"""
    phone = str(phone).strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    # Remove any leading zeros
    if phone.startswith("0"):
        phone = phone[1:]
    # Add country code if not present (assuming India +91)
    if not phone.startswith("+") and not phone.startswith("91"):
        phone = "91" + phone
    elif phone.startswith("+"):
        phone = phone[1:]  # Remove + as WhatsApp URL doesn't need it
    print(f"[PHONE] Cleaned: {phone}")
    return phone


# =========================
# MESSAGE FILE EXTRACTION
# =========================
def extract_messages_from_file(file_path: str) -> list[str]:
    ext = Path(file_path).suffix.lower()

    if ext == ".csv":
        df = pd.read_csv(file_path)
        if "message" not in df.columns:
            raise ValueError("CSV must contain a 'message' column")
        return df["message"].dropna().astype(str).tolist()

    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]

    if ext == ".pdf":
        messages = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    for line in text.split("\n"):
                        if line.strip():
                            messages.append(line.strip())
        return messages

    if ext == ".docx":
        doc = docx.Document(file_path)
        return [p.text.strip() for p in doc.paragraphs if p.text.strip()]

    raise ValueError("Unsupported message file type")


# =========================
# PHONE FILE EXTRACTION
# =========================
def extract_phones_from_file(file_path: str) -> dict[int, list[str]]:
    """Extract phone numbers grouped by batch_id from various file formats"""
    ext = Path(file_path).suffix.lower()

    if ext == ".csv":
        df = pd.read_csv(file_path)
        
        # Check if batch_id column exists
        if "batch_id" in df.columns:
            batches = {}
            if "phone" in df.columns:
                for batch_id, group in df.groupby("batch_id"):
                    phones = group["phone"].dropna().astype(str).tolist()
                    batches[int(batch_id)] = phones
            else:
                # Use first column as phone if no phone column
                phone_col = df.columns[0]
                for batch_id, group in df.groupby("batch_id"):
                    phones = group[phone_col].dropna().astype(str).tolist()
                    batches[int(batch_id)] = phones
            return batches
        else:
            # No batch_id column - group phones into batches of 8
            if "phone" in df.columns:
                phones = df["phone"].dropna().astype(str).tolist()
            else:
                if len(df.columns) > 0:
                    phones = df.iloc[:, 0].dropna().astype(str).tolist()
                else:
                    raise ValueError("CSV file is empty or has no columns")
            
            # Group into batches of 8
            batches = {}
            batch_size = 8
            for i in range(0, len(phones), batch_size):
                batch_id = (i // batch_size) + 1
                batches[batch_id] = phones[i:i + batch_size]
            return batches

    if ext == ".txt":
        phones = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    # Each line is treated as a phone number
                    phones.append(line)
        # Group into batches of 8
        batches = {}
        batch_size = 8
        for i in range(0, len(phones), batch_size):
            batch_id = (i // batch_size) + 1
            batches[batch_id] = phones[i:i + batch_size]
        return batches

    if ext == ".pdf":
        phones = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    for line in text.split("\n"):
                        line = line.strip()
                        if line:
                            phones.append(line)
        # Group into batches of 8
        batches = {}
        batch_size = 8
        for i in range(0, len(phones), batch_size):
            batch_id = (i // batch_size) + 1
            batches[batch_id] = phones[i:i + batch_size]
        return batches

    if ext == ".docx":
        doc = docx.Document(file_path)
        phones = []
        for p in doc.paragraphs:
            text = p.text.strip()
            if text:
                phones.append(text)
        # Group into batches of 8
        batches = {}
        batch_size = 8
        for i in range(0, len(phones), batch_size):
            batch_id = (i // batch_size) + 1
            batches[batch_id] = phones[i:i + batch_size]
        return batches

    raise ValueError("Unsupported phone file type")


# =========================
# SUMMARY HELPERS
# =========================
def sanitize_summary(text: str) -> str:
    text = re.sub(r"^\d+\.\s*", "", text.strip())
    return text.strip(" .-")


def extract_summary_deterministic(message):
    """Extract summary using deterministic rule-based approach for consistency"""
    msg = message.strip()
    
    # If message already has format like "Event - Date: X, Time: Y", keep it as-is
    if " - Date:" in msg or " - Date: " in msg:
        # Clean up extra spaces but keep the format
        msg = re.sub(r'\s+', ' ', msg)  # Normalize spaces
        return msg
    
    # For natural language messages, extract key information deterministically
    import re
    
    # Pattern: "Event on [date] at [time] in [location]"
    # Example: "Placement drive for HPE... is being held on 23rd March in Seminar hall"
    pattern = r"^(.+?)\s+(?:is\s+)?(?:being\s+)?(?:held|scheduled|conducted|planned)\s+on\s+([^at\n\.]+?)(?:\s+at\s+([^in\n\.]+?))?(?:\s+in\s+([^\.\n]+?))?(?:\.|$)"
    match = re.search(pattern, msg, re.IGNORECASE)
    if match:
        event = match.group(1).strip()
        date = match.group(2).strip() if match.group(2) else ""
        time_part = match.group(3).strip() if match.group(3) else ""
        location = match.group(4).strip() if match.group(4) else ""
        
        # Build summary preserving the message structure
        result = event
        if date:
            result += f" on {date}"
        if time_part:
            result += f" at {time_part}"
        if location:
            result += f" in {location}"
        
        # Add any additional info after the location
        if match.end() < len(msg):
            remaining = msg[match.end():].strip()
            if remaining and not remaining.startswith('.'):
                result += " " + remaining
        return result.strip()
    
    # Pattern: "Event on [date]" (simpler pattern)
    pattern2 = r"^(.+?)\s+on\s+([^\.\n]+?)(?:\.|$)"
    match = re.search(pattern2, msg, re.IGNORECASE)
    if match:
        event = match.group(1).strip()
        rest = match.group(2).strip()
        return f"{event} on {rest}".strip()
    
    # If message is already concise and clear, return as-is
    if len(msg) < 200 and ('.' not in msg or msg.count('.') <= 1):
        return msg
    
    # Fallback: return the message as-is (deterministic - no transformation)
    return msg


def batch_summarize_messages(messages):
    """Generate summaries in format: Event name - date - time - location"""
    if not messages:
        return []
    
    # Build a single prompt for all messages
    prompt = (
        "Extract information from each message and format EXACTLY as: Event name - date - time - location\n\n"
        "Rules:\n"
        "- Extract the EVENT NAME (exam name, event name, meeting name, etc.)\n"
        "- Extract the DATE (if mentioned)\n"
        "- Extract the TIME (if mentioned)\n"
        "- Extract the LOCATION (if mentioned)\n"
        "- Use ' - ' (space dash space) to separate each part\n"
        "- If date/time/location is NOT mentioned, skip that part\n"
        "- Keep event names short (just the key name, not full sentence)\n"
        "- Output ONE summary per message, one per line\n"
        "- NO explanations, NO extra text, just the formatted summaries\n\n"
        "Examples:\n"
        "The BDA exam is on 12th Jan at 10 30 → BDA exam - 12th Jan - 10 30\n"
        "Placement drive for HPE is on 23rd March in Seminar hall → Placement drive for HPE - 23rd March - Seminar hall\n"
        "Internal assessment test for Data Structures on 5th Feb at 2 00 PM in Block B → Data Structures assessment - 5th Feb - 2 00 PM - Block B\n"
        "Workshop on AI on 18th April at Main Auditorium → AI Workshop - 18th April - Main Auditorium\n"
        "SAN exam is on 1st Dec at 10 30 am → SAN exam - 1st Dec - 10 30 am\n\n"
        "Now extract from these messages:\n\n"
    )
    
    # Add all messages
    for i, msg in enumerate(messages, 1):
        prompt += f"{i}. {msg}\n"
    
    prompt += "\nSummaries (format: Event name - date - time - location, one per line):\n"
    
    # Single API call for all messages
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    summaries = []
    
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT)
        resp.raise_for_status()
        raw = resp.json()["response"]
        
        # Parse the response to extract summaries
        lines = raw.splitlines()
        extracted_summaries = []
        
        for line in lines:
            line = line.strip()
            # Skip empty lines
            if not line or len(line) < 5:
                continue
            # Skip instruction/header lines
            if line.lower().startswith(("example", "rules:", "messages", "summaries", "output", "format:", "now extract")):
                continue
            # Skip lines that are just numbers
            if re.match(r'^\d+\.?\s*$', line):
                continue
            # Look for lines with the dash format (our target format)
            if " - " in line:
                # Remove leading numbers if present
                line = re.sub(r'^\d+\.?\s*', '', line).strip()
                if line and len(line) > 5:
                    extracted_summaries.append(line)
            # Also accept lines that look like summaries (long enough, not headers)
            elif len(line) > 15 and not line.lower().startswith(("message", "summary")):
                line = re.sub(r'^\d+\.?\s*', '', line).strip()
                extracted_summaries.append(line)
        
        # Match summaries to messages
        for i, msg in enumerate(messages):
            if i < len(extracted_summaries):
                summary = extracted_summaries[i].strip()
                # Clean up summary
                summary = sanitize_summary(summary)
            else:
                # Fallback: try to extract basic info
                summary = extract_basic_summary(msg)
            
            # Validate and clean summary
            if not summary or len(summary) < 3:
                summary = extract_basic_summary(msg)
            
            summaries.append(summary)
        
        # Ensure we have the right number of summaries
        while len(summaries) < len(messages):
            msg = messages[len(summaries)]
            summary = extract_basic_summary(msg)
            summaries.append(summary)
            
    except Exception as e:
        # Fallback: extract basic summaries
        for msg in messages:
            summary = extract_basic_summary(msg)
            summaries.append(summary)
    
    return summaries[:len(messages)]


def extract_basic_summary(msg):
    """Fallback function to extract basic summary from message"""
    msg = msg.strip()
    parts = []
    
    # Extract event name (first part before "on", "is", "will be", etc.)
    event_match = re.match(r'^(.+?)\s+(?:is|will be|is being|is scheduled|is planned|will be conducted)', msg, re.IGNORECASE)
    if event_match:
        event = event_match.group(1).strip()
        # Clean up event name
        event = re.sub(r'^(The|A|An)\s+', '', event, flags=re.IGNORECASE).strip()
        parts.append(event)
    else:
        # Try simpler pattern
        event = msg.split(' on ')[0].split(' is ')[0].split(' will ')[0].strip()
        event = re.sub(r'^(The|A|An)\s+', '', event, flags=re.IGNORECASE).strip()
        parts.append(event if event else "Event")
    
    # Extract date
    date_match = re.search(r'on\s+(\d+(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*(?:\s+\d+)?)', msg, re.IGNORECASE)
    if date_match:
        parts.append(date_match.group(1).strip())
    
    # Extract time
    time_match = re.search(r'at\s+(\d+\s*\d*\s*(?:am|pm|AM|PM))', msg, re.IGNORECASE)
    if time_match:
        parts.append(time_match.group(1).strip())
    
    # Extract location
    location_match = re.search(r'in\s+([^and\.]+?)(?:\s+and|\.|$)', msg, re.IGNORECASE)
    if location_match:
        location = location_match.group(1).strip()
        if len(location) < 50:  # Reasonable location length
            parts.append(location)
    
    return " - ".join(parts) if len(parts) > 1 else msg[:80]


def format_as_bullets(summary: str) -> str:
    """Format summary as a single-line, clear message in format: *Event Name - Date - Time - Location*"""
    # Clean up the summary
    summary = summary.strip()
    # Remove any extra dashes or formatting
    parts = [p.strip() for p in summary.split(" - ") if p.strip()]
    # Join all parts with " - " to create one clear line
    single_line = " - ".join(parts)
    # Wrap in asterisks for WhatsApp bold formatting (no emojis to avoid ChromeDriver BMP issues)
    return f"*{single_line}*"


# =========================
# BUILD PAIRS
# =========================
def build_pairs(phone_file_path, message_file_path):
    """Build phone-summary pairs: Combine all summaries into one message, send to each batch"""
    phone_batches = extract_phones_from_file(phone_file_path)
    messages = extract_messages_from_file(message_file_path)
    
    print("\n" + "="*50)
    print("[SUMMARY GENERATION] Starting...")
    print(f"[SUMMARY] Total messages to process: {len(messages)}")
    print("="*50)
    
    summaries = batch_summarize_messages(messages)
    
    print("\n" + "="*50)
    print("[SUMMARIES GENERATED]")
    print("="*50)
    for i, summary in enumerate(summaries, 1):
        print(f"  {i}. {summary}")
    print("="*50 + "\n")

    # Format each summary
    formatted_summaries = [format_as_bullets(summary) for summary in summaries]
    
    # Combine all summaries into one message (one per line)
    combined_message = "\n".join(formatted_summaries)
    
    print("[COMBINED MESSAGE TO SEND]:")
    print("-"*50)
    print(combined_message)
    print("-"*50 + "\n")

    # Create pairs: send combined message to all phones in each batch
    pairs = []
    all_phones = []
    for batch_id, phones in sorted(phone_batches.items()):
        for phone in phones:
            cleaned_phone = clean_phone_num(phone)
            pairs.append((cleaned_phone, combined_message))
            all_phones.append(cleaned_phone)
    
    print(f"[PHONES] Will send to {len(pairs)} phone numbers:")
    for p in all_phones:
        print(f"  - {p}")
    print("")
    
    return pairs


# =========================
# LOCK FILE HELPERS
# =========================
def is_process_running(pid):
    """Check if a process is still running"""
    try:
        if platform.system() == "Windows":
            # On Windows, use tasklist or try to signal the process
            import subprocess
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            return str(pid) in result.stdout
        else:
            # On Unix-like systems, use os.kill with signal 0
            os.kill(pid, 0)
            return True
    except (OSError, ProcessLookupError, subprocess.SubprocessError):
        return False


def cleanup_stale_lock():
    """Remove lock file if the process is no longer running"""
    if os.path.exists(PROFILE_LOCK_FILE):
        try:
            with open(PROFILE_LOCK_FILE, "r") as f:
                pid_str = f.read().strip()
                if pid_str.isdigit():
                    pid = int(pid_str)
                    if not is_process_running(pid):
                        # Process is dead, remove stale lock
                        os.remove(PROFILE_LOCK_FILE)
                        return True
                    else:
                        # Process is still running
                        return False
                else:
                    # Invalid lock file, remove it
                    os.remove(PROFILE_LOCK_FILE)
                    return True
        except Exception:
            # Error reading lock file, remove it
            try:
                os.remove(PROFILE_LOCK_FILE)
            except:
                pass
            return True
    return True


# =========================
# SELENIUM (OFF-SCREEN)
# =========================
def setup_webdriver():
    os.makedirs(WHATSAPP_PROFILE_DIR, exist_ok=True)

    # Check and clean up stale lock file
    if os.path.exists(PROFILE_LOCK_FILE):
        if not cleanup_stale_lock():
            raise RuntimeError("WhatsApp already running in background")

    # Create new lock file
    with open(PROFILE_LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))

    opts = Options()
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-notifications")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--no-sandbox")
    # Hide Chrome window off-screen (runs in background)
    opts.add_argument("--window-position=-32000,-32000")
    opts.add_argument("--window-size=800,600")
    opts.add_argument(f"--user-data-dir={WHATSAPP_PROFILE_DIR}")
    opts.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    print("[WHATSAPP] Starting Chrome browser...")
    driver = webdriver.Chrome(service=Service(), options=opts)
    driver.get("https://web.whatsapp.com")
    print("[WHATSAPP] Opened WhatsApp Web - waiting for login/load...")
    return driver


def send_message_once(driver, phone, message):
    """Send a single message attempt"""
    # Navigate to the chat with this phone number
    url = f"https://web.whatsapp.com/send?phone={phone}&text=&app_absent=0"
    print(f"[WHATSAPP] Opening URL: {url}")
    driver.get(url)
    
    # Wait for page to fully load
    print("[WHATSAPP] Waiting for chat to load...")
    time.sleep(8)
    
    # Check if there's an error (invalid phone number)
    try:
        error_popup = driver.find_elements(By.XPATH, "//*[contains(text(), 'Phone number shared via url is invalid')]")
        if error_popup:
            print(f"[WHATSAPP] ERROR: Invalid phone number: {phone}")
            return False
    except:
        pass
    
    # Try multiple XPath options for the message box
    textbox_xpaths = [
        "//div[@role='textbox' and @aria-placeholder='Type a message']",
        "//div[@contenteditable='true' and @data-tab='10']",
        "//div[@contenteditable='true'][@role='textbox']",
        "//footer//div[@contenteditable='true']",
        "//div[contains(@class, 'selectable-text')][@contenteditable='true']"
    ]
    
    box = None
    for xpath in textbox_xpaths:
        try:
            box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            if box:
                print(f"[WHATSAPP] Found textbox")
                break
        except:
            continue
    
    if not box:
        print("[WHATSAPP] ERROR: Could not find message textbox!")
        return False

    # Click on textbox and type message
    box.click()
    time.sleep(0.5)
    box.send_keys(message)
    time.sleep(1)
    
    # Press Enter to send
    box.send_keys(Keys.ENTER)
    time.sleep(2)
    
    # Try clicking the send button as backup
    try:
        send_btn = driver.find_elements(By.XPATH, "//span[@data-icon='send']")
        if send_btn:
            send_btn[0].click()
            time.sleep(1)
    except:
        pass
    
    return True


def check_and_retry_failed_messages(driver):
    """Check for failed messages and click retry on them"""
    retried = 0
    try:
        # Look for error/alert icons on messages (red exclamation marks)
        error_icons = driver.find_elements(By.XPATH, "//span[@data-icon='alert-phone']|//span[@data-icon='msg-error']|//div[@data-icon='alert-phone']")
        
        for icon in error_icons:
            try:
                # Click on the error icon to retry
                icon.click()
                time.sleep(1)
                
                # Look for retry button and click it
                retry_btns = driver.find_elements(By.XPATH, "//*[contains(text(), 'Retry')]|//*[contains(text(), 'retry')]")
                for btn in retry_btns:
                    try:
                        btn.click()
                        retried += 1
                        print(f"[WHATSAPP] Clicked retry on failed message")
                        time.sleep(2)
                    except:
                        pass
            except:
                pass
        
        if retried > 0:
            print(f"[WHATSAPP] Retried {retried} failed messages")
            time.sleep(5)  # Wait for retries to process
            
    except Exception as e:
        print(f"[WHATSAPP] Error checking for failed messages: {e}")
    
    return retried


def send_message(driver, phone, message, max_retries=3):
    """Send message with automatic retry on failure"""
    print(f"\n[WHATSAPP] Sending to: {phone}")
    print(f"[WHATSAPP] Message preview: {message[:80]}...")
    
    for attempt in range(1, max_retries + 1):
        print(f"[WHATSAPP] Attempt {attempt} of {max_retries}")
        
        # Send the message
        if send_message_once(driver, phone, message):
            # Wait for delivery
            print("[WHATSAPP] Waiting for delivery...")
            time.sleep(5)
            
            # Check for delivery confirmation
            try:
                # Look for tick marks (sent/delivered)
                ticks = driver.find_elements(By.XPATH, "//span[@data-icon='msg-check' or @data-icon='msg-dblcheck']")
                if ticks:
                    print(f"[WHATSAPP] Message delivered to {phone}")
                    return True
                
                # Check for error icons
                errors = driver.find_elements(By.XPATH, "//span[@data-icon='alert-phone']|//span[@data-icon='msg-error']")
                if errors and attempt < max_retries:
                    print(f"[WHATSAPP] Delivery failed, retrying...")
                    # Try clicking retry on the failed message
                    check_and_retry_failed_messages(driver)
                    time.sleep(3)
                    continue
            except:
                pass
            
            # If we can't determine status, assume success after waiting
            print(f"[WHATSAPP] Message sent to {phone} (status unknown)")
            return True
        else:
            if attempt < max_retries:
                print(f"[WHATSAPP] Send failed, retrying in 3 seconds...")
                time.sleep(3)
    
    print(f"[WHATSAPP] Failed to send to {phone} after {max_retries} attempts")
    return False


# =========================
# STATUS TRACKING
# =========================
def update_status(status: str, progress: int = 0, total: int = 0, message: str = ""):
    """Update status file for frontend to read"""
    os.makedirs(WHATSAPP_PROFILE_DIR, exist_ok=True)
    status_data = {
        "status": status,  # "processing", "sending", "completed", "error"
        "progress": progress,
        "total": total,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    with open(STATUS_FILE, "w") as f:
        json.dump(status_data, f)


def get_status():
    """Get current status"""
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"status": "idle", "progress": 0, "total": 0, "message": ""}


def clear_status():
    """Clear status file"""
    if os.path.exists(STATUS_FILE):
        os.remove(STATUS_FILE)


def clear_lock_file():
    """Manually clear the lock file (use if you get 'WhatsApp already running' error)"""
    if os.path.exists(PROFILE_LOCK_FILE):
        try:
            os.remove(PROFILE_LOCK_FILE)
            return True
        except Exception:
            return False
    return True


# =========================
# BACKGROUND WORKER
# =========================
def _background_worker(phone_file_path, message_file_path):
    driver = None
    try:
        print("\n" + "="*60)
        print("[EDUPING] Starting background worker...")
        print("="*60)
        
        update_status("processing", 0, 0, "Generating summaries...")
        pairs = build_pairs(phone_file_path, message_file_path)
        
        total = len(pairs)
        print(f"\n[EDUPING] Total pairs to send: {total}")
        update_status("sending", 0, total, f"Preparing to send {total} messages...")
        
        print("[EDUPING] Starting WhatsApp WebDriver...")
        driver = setup_webdriver()
        print("[EDUPING] WebDriver started, waiting for WhatsApp to load...")
        print("[EDUPING] *** If you see QR code, please scan it with your phone ***")
        print("[EDUPING] Waiting 15 seconds for WhatsApp Web to fully load...")
        time.sleep(15)  # Give more time for login/QR scan if needed
        
        update_status("sending", 0, total, "Connecting to WhatsApp...")
        print("[EDUPING] WhatsApp should be loaded now, starting to send messages...\n")

        failed_phones = []
        for idx, (phone, summary) in enumerate(pairs, 1):
            try:
                print(f"\n[EDUPING] === Sending message {idx} of {total} ===")
                success = send_message(driver, phone, summary)
                if success:
                    update_status("sending", idx, total, f"Sent message {idx} of {total}")
                else:
                    failed_phones.append(phone)
                    update_status("sending", idx, total, f"Failed to send to {phone}")
                print(f"[EDUPING] Waiting before next message...")
                time.sleep(3)
            except Exception as e:
                print(f"[EDUPING] ERROR sending to {phone}: {str(e)}")
                failed_phones.append(phone)
                update_status("sending", idx, total, f"Error sending to {phone}: {str(e)}")
                time.sleep(3)

        # Final check: retry any remaining failed messages
        if failed_phones:
            print(f"\n[EDUPING] Retrying {len(failed_phones)} failed messages...")
            update_status("sending", total, total, f"Retrying {len(failed_phones)} failed messages...")
            check_and_retry_failed_messages(driver)
            time.sleep(5)

        print("\n" + "="*60)
        if failed_phones:
            print(f"[EDUPING] COMPLETED! Sent {total - len(failed_phones)} of {total} messages.")
            print(f"[EDUPING] Failed phones: {failed_phones}")
        else:
            print(f"[EDUPING] COMPLETED! All {total} messages sent successfully!")
        print("="*60 + "\n")
        update_status("completed", total, total, f"Sent {total - len(failed_phones)} of {total} messages")

    except Exception as e:
        print(f"\n[EDUPING] FATAL ERROR: {str(e)}")
        update_status("error", 0, 0, f"Error: {str(e)}")
    finally:
        if driver:
            print("[EDUPING] Closing WebDriver...")
            driver.quit()
        if os.path.exists(PROFILE_LOCK_FILE):
            os.remove(PROFILE_LOCK_FILE)
        print("[EDUPING] Background worker finished.")


# =========================
# PUBLIC API
# =========================
def send_bulk_from_files(phone_file_path, message_file_path):
    """Start background process to send messages. Returns immediately."""
    clear_status()  # Clear any previous status
    thread = threading.Thread(
        target=_background_worker,
        args=(phone_file_path, message_file_path),
        daemon=True
    )
    thread.start()
    return thread
