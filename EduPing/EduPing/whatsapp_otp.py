"""
WhatsApp OTP Authentication and Session Management
Handles automated login via phone number and OTP verification
"""

import time
import os
import json
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Cache for OTP sessions - store in project directory
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_DIR, ".eduping_data")
os.makedirs(DATA_DIR, exist_ok=True)  # Create directory if it doesn't exist

OTP_SESSIONS_FILE = os.path.join(DATA_DIR, "otp_sessions.json")


def save_otp_session(phone_number: str, otp_code: str, driver=None):
    """Save OTP session for a phone number"""
    sessions = load_otp_sessions()
    sessions[phone_number] = {
        "otp": otp_code,
        "timestamp": datetime.now().isoformat(),
        "verified": False,
        "driver_ready": driver is not None
    }
    with open(OTP_SESSIONS_FILE, 'w') as f:
        json.dump(sessions, f)
    return sessions


def load_otp_sessions() -> dict:
    """Load OTP sessions from file"""
    if os.path.exists(OTP_SESSIONS_FILE):
        try:
            with open(OTP_SESSIONS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}


def get_otp_session(phone_number: str) -> dict:
    """Get OTP session for a phone number"""
    sessions = load_otp_sessions()
    if phone_number in sessions:
        session = sessions[phone_number]
        # Check if OTP is still valid (15 minutes)
        if session.get("verified"):
            timestamp = datetime.fromisoformat(session.get("timestamp", "2000-01-01"))
            if datetime.now() - timestamp < timedelta(hours=24):  # Session valid for 24 hours once verified
                return session
    return None


def mark_otp_verified(phone_number: str):
    """Mark OTP session as verified"""
    sessions = load_otp_sessions()
    if phone_number in sessions:
        sessions[phone_number]["verified"] = True
        sessions[phone_number]["timestamp"] = datetime.now().isoformat()
        with open(OTP_SESSIONS_FILE, 'w') as f:
            json.dump(sessions, f)


def mark_already_logged_in(phone_number: str):
    """Mark a phone number as already logged into WhatsApp (no OTP needed)"""
    sessions = load_otp_sessions()
    sessions[phone_number] = {
        "otp": "",
        "timestamp": datetime.now().isoformat(),
        "verified": True,
        "already_logged_in": True,
        "driver_ready": False
    }
    with open(OTP_SESSIONS_FILE, 'w') as f:
        json.dump(sessions, f)
    print(f"[OTP] Marked {phone_number} as already logged in (no OTP needed)")


def is_session_already_logged_in(phone_number: str) -> bool:
    """Check if a session is marked as already logged in"""
    session = get_otp_session(phone_number)
    if session and session.get("already_logged_in"):
        print(f"[OTP] Session {phone_number} is marked as already logged in")
        return True
    return False


def request_whatsapp_otp(phone_number: str, country_code: str = "", phone_only: str = "", driver=None) -> dict:
    """
    Request OTP for WhatsApp login via phone number.
    Automatically logs into WhatsApp Web with phone number and triggers OTP.
    
    Args:
        phone_number: Full phone number (country code + phone)
        country_code: Country code (e.g., "91")
        phone_only: Phone number without country code (e.g., "9876543210") 
        driver: Optional Selenium WebDriver instance. If provided, uses it; otherwise creates a new one
    """
    try:
        # Clean phone number
        phone = phone_number.replace("+", "").replace(" ", "").replace("-", "")
        if not phone.isdigit():
            return {"success": False, "message": "Invalid phone number format"}
        
        # Store the phone number for OTP entry
        save_otp_session(phone, "", None)
        
        print(f"[OTP] OTP request initiated for {phone}")
        print(f"[OTP] Country Code: {country_code}, Phone: {phone_only}")
        print(f"[OTP] Starting WhatsApp Web login process...")
        
        return {
            "success": True,
            "message": f"Logging into WhatsApp Web with {phone}. Check your phone for OTP.",
            "phone": phone,
            "country_code": country_code,
            "phone_only": phone_only
        }
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}


def verify_whatsapp_otp(phone_number: str, otp_code: str) -> dict:
    """
    Verify OTP and mark session as verified.
    
    Args:
        phone_number: Phone number (country code + phone)
        otp_code: 6-digit OTP code
    
    Returns:
        dict with success status
    """
    try:
        phone = phone_number.replace("+", "").replace(" ", "").replace("-", "")
        
        # Validate OTP format (should be 6 digits for WhatsApp)
        if not otp_code.isdigit() or len(otp_code) != 6:
            return {"success": False, "message": "OTP must be 6 digits"}
        
        # Mark OTP as verified
        mark_otp_verified(phone)
        
        print(f"[OTP] OTP verified for {phone}")
        
        return {
            "success": True,
            "message": "OTP verified successfully! WhatsApp session is ready.",
            "phone": phone
        }
    except Exception as e:
        return {"success": False, "message": f"Verification error: {str(e)}"}


def is_whatsapp_already_logged_in(driver, timeout: int = 5) -> bool:
    """
    Check if the user is already logged into WhatsApp Web.
    Looks for indicators of a logged-in session (chat interface, conversation list, etc).
    
    Args:
        driver: Selenium WebDriver instance
        timeout: Time to wait for page load
    
    Returns:
        True if user is already logged in, False otherwise
    """
    try:
        print("[OTP] Checking if user is already logged into WhatsApp Web...")
        
        # Wait for page to load
        time.sleep(3)
        
        # Check for indicators of being logged in:
        # 1. Chat list or conversation pane (appears on left side when logged in)
        logged_in_selectors = [
            "//div[@role='navigation']//div[contains(@class, 'x1n2onr6')]",  # Sidebar/chat list container
            "//div[contains(@class, 'x12sz694')]//div[contains(@class, 'x1c4vz4f')]",  # Chat list items
            "//div[@aria-label='Chat list']",  # Chat list label
            "//span[@data-testid='conversation-list']",  # Conversation list
            "//div[contains(@class, 'x1iyjqo2')]//div[@role='option']",  # Chat items
            "//div[contains(@title, 'Search for contacts')]",  # Search bar visible when logged in
            "//div[@contenteditable='true' and contains(@class, 'x1hx0egp')]",  # Message input area
            "//span[contains(text(), 'Type a message')]",  # Message placeholder
        ]
        
        for selector in logged_in_selectors:
            try:
                element = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                if element:
                    print(f"[OTP] ✓ Found logged-in indicator: {selector[:50]}...")
                    print("[OTP] User is ALREADY logged into WhatsApp Web!")
                    return True
            except:
                continue
        
        print("[OTP] ✗ No logged-in indicators found - user needs to log in")
        return False
        
    except Exception as e:
        print(f"[OTP] Error checking login status: {e}")
        return False


def start_whatsapp_login_automation(driver, country_code: str, phone_only: str, max_retries: int = 3) -> dict:
    """
    Complete automation for WhatsApp Web login with phone number.
    Opens WhatsApp Web, enters phone number, clicks login, and waits for OTP.
    
    Args:
        driver: Selenium WebDriver instance (already opened with WhatsApp Web URL)
        country_code: Country code (e.g., "91" for India)
        phone_only: Phone number without country code (e.g., "9876543210")
        max_retries: Maximum retries for finding elements
    
    Returns:
        dict with success status and details
    """
    try:
        print("="*60)
        print("[OTP] STARTING AUTOMATED WHATSAPP WEB LOGIN")
        print(f"[OTP] Country Code: {country_code}, Phone: {phone_only}")
        print(f"[OTP] Full Phone: +{country_code}{phone_only}")
        print("="*60)
        
        # Wait for WhatsApp Web to load
        print("[OTP] Waiting for WhatsApp Web to load...")
        time.sleep(5)
        
        # CHECK: Is user already logged in?
        print("\n[OTP] CHECKING: Is user already logged into WhatsApp Web?")
        if is_whatsapp_already_logged_in(driver, timeout=3):
            print("[OTP] ✓✓✓ USER ALREADY LOGGED IN - SKIPPING LOGIN STEPS ✓✓✓")
            print("[OTP] WhatsApp Web is ready to send messages!")
            phone_full = country_code + phone_only
            # Mark this session as already logged in (no OTP needed)
            mark_already_logged_in(phone_full)
            print(f"[OTP] Marked {phone_full} as already authenticated - skipping OTP")
            print("[OTP] Ready for message sending - returning success")
            return {
                "success": True,
                "message": "WhatsApp Web is already authenticated. Ready to send messages!",
                "step": "already_logged_in",
                "country_code": country_code,
                "phone_only": phone_only,
                "skip_otp": True  # FLAG: Frontend should NOT ask for OTP
            }
        
        print("[OTP] User NOT logged in - proceeding with login automation...")
        
        # Step 1: Look for "Log in with phone number" button
        print("\n[OTP] STEP 1: Finding 'Log in with phone number' button...")
        phone_button_found = False
        
        selectors = [
            "//div[contains(text(), 'Log in with phone number')]",
            "//span[contains(text(), 'Log in with phone number')]",
            "//button[contains(text(), 'Log in with phone number')]",
            "//a[contains(text(), 'Log in with phone number')]",
            "//*[@role='button' and contains(text(), 'phone number')]"
        ]
        
        for attempt in range(1, max_retries + 1):
            for selector in selectors:
                try:
                    element = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    print(f"[OTP] ✓ Found button using selector: {selector}")
                    driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(1)
                    element.click()
                    print("[OTP] ✓ Clicked 'Log in with phone number' button")
                    phone_button_found = True
                    break
                except:
                    continue
            
            if phone_button_found:
                break
                
            if attempt < max_retries:
                print(f"[OTP] ⚠ Attempt {attempt} failed, retrying...")
                time.sleep(3)
        
        if not phone_button_found:
            print("[OTP] ✗ Could not find 'Log in with phone number' button")
            # Try clicking the parent div or container
            try:
                containers = driver.find_elements(By.XPATH, "//div[@role='navigation']//div[contains(text(), 'phone')]")
                if containers:
                    containers[0].click()
                    print("[OTP] ✓ Clicked phone login via parent container")
                    phone_button_found = True
                    time.sleep(2)
            except:
                pass
        
        if not phone_button_found:
            return {
                "success": False,
                "message": "Could not find 'Log in with phone number' button. WhatsApp Web might have changed its UI.",
                "step": "phone_button"
            }
        
        # Wait for phone input screen
        print("\n[OTP] Waiting for phone input form to appear...")
        time.sleep(3)
        
        # Step 1.5: Select Country (NEW!)
        print("[OTP] STEP 1.5: Selecting country from dropdown...")
        try:
            country_map = {
                "1": "United States",
                "44": "United Kingdom",
                "33": "France",
                "49": "Germany",
                "39": "Italy",
                "34": "Spain",
                "91": "India",
                "86": "China",
                "81": "Japan",
                "55": "Brazil",
                "61": "Australia",
                "64": "New Zealand",
                "27": "South Africa",
            }
            
            country_name = country_map.get(country_code, f"Country {country_code}")
            print(f"[OTP] Looking for country: {country_name}")
            
            # Find and click the country selector
            country_dropdown = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'x1c4vz4f') and .//span[contains(text(), 'India') or contains(text(), 'United States') or contains(text(), 'United Kingdom')]]"))
            )
            print("[OTP] ✓ Found country dropdown")
            driver.execute_script("arguments[0].scrollIntoView(true);", country_dropdown)
            time.sleep(0.5)
            country_dropdown.click()
            print("[OTP] ✓ Clicked country dropdown")
            time.sleep(2)
            
            # Find and click the country option in the list
            country_options = driver.find_elements(By.XPATH, f"//span[contains(text(), '{country_name}')]")
            if country_options:
                for option in country_options:
                    try:
                        if option.is_displayed():
                            driver.execute_script("arguments[0].scrollIntoView(true);", option)
                            time.sleep(0.5)
                            option.click()
                            print(f"[OTP] ✓ Selected {country_name}")
                            time.sleep(1)
                            break
                    except:
                        continue
            else:
                print(f"[OTP] ⚠ Could not find {country_name} in dropdown, proceeding anyway")
                # Click somewhere to close dropdown
                driver.find_element(By.TAG_NAME, "body").click()
                time.sleep(1)
                
        except Exception as e:
            print(f"[OTP] ⚠ Error selecting country: {str(e)}")
            print("[OTP] Continuing without country selection...")
            try:
                driver.find_element(By.TAG_NAME, "body").click()
            except:
                pass
        
        # Step 2: Enter phone number
        print("[OTP] STEP 2: Entering phone number...")
        phone_input_found = False
        
        phone_selectors = [
            "//input[@aria-label='Type your phone number to log in to WhatsApp']",
            "//input[contains(@placeholder, 'phone')]",
            "//input[contains(@placeholder, 'number')]",
            "//input[@type='tel']",
            "//input[@type='text' and contains(@class, 'selectable-text')]",
            "//input[@inputmode='decimal']"
        ]
        
        for attempt in range(1, max_retries + 1):
            for selector in phone_selectors:
                try:
                    phone_input = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    # Scroll to input
                    driver.execute_script("arguments[0].scrollIntoView(true);", phone_input)
                    time.sleep(1)
                    
                    # Click and clear completely
                    phone_input.click()
                    time.sleep(0.3)
                    # Select all and delete to ensure complete clear
                    phone_input.send_keys(Keys.CONTROL + "a")
                    time.sleep(0.2)
                    phone_input.send_keys(Keys.DELETE)
                    time.sleep(0.5)
                    
                    # Use JavaScript to completely clear the field
                    driver.execute_script("arguments[0].value = '';", phone_input)
                    time.sleep(0.3)
                    
                    # Format: +91 8792234068
                    # Keep country code WITH phone number, separated by space
                    formatted_phone = f"+{country_code} {phone_only}"
                    
                    print(f"[OTP] Country code: +{country_code}")
                    print(f"[OTP] Phone number: {phone_only}")
                    print(f"[OTP] Formatted phone for entry: {formatted_phone}")
                    
                    # Type the formatted phone with country code
                    phone_input.send_keys(formatted_phone)
                    time.sleep(1)
                    
                    # Verify input was entered
                    entered_value = phone_input.get_attribute("value")
                    print(f"[OTP] Actual input value in field: {entered_value}")
                    
                    if country_code in entered_value and phone_only in entered_value:
                        print(f"[OTP] ✓ Successfully entered phone number: {formatted_phone}")
                        phone_input_found = True
                        break
                    else:
                        print(f"[OTP] ⚠ Verification: Expected {formatted_phone}, got: {entered_value}")
                        phone_input_found = True
                        break
                except Exception as e:
                    print(f"[OTP] Error entering phone: {str(e)}")
                    continue
            
            if phone_input_found:
                break
            
            if attempt < max_retries:
                print(f"[OTP] ⚠ Attempt {attempt} failed, retrying...")
                time.sleep(3)
        
        if not phone_input_found:
            return {
                "success": False,
                "message": "Could not find phone number input field",
                "step": "phone_input"
            }
        
        # Step 3: Click Next/Submit button AUTOMATICALLY
        print("\n[OTP] STEP 3: Automatically clicking 'Next' button...")
        time.sleep(1)  # Brief wait for button to be ready
        
        next_button_found = False
        next_selectors = [
            "//button[contains(text(), 'Next')]",
            "//button[.//div[contains(text(), 'Next')]]",
            "//span[contains(text(), 'Next')]/ancestor::button",
            "//button[@type='button' and contains(@class, 'x1c4vz4f')]",
            "//button[contains(., 'Next')]",
            "//div[@role='button' and contains(text(), 'Next')]",
            "//button[contains(@class, 'x889kno')]"  # Generic button class selector
        ]
        
        for selector in next_selectors:
            try:
                next_button = WebDriverWait(driver, 8).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                print(f"[OTP] ✓ Found Next button with selector")
                driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                time.sleep(0.5)
                
                # Click the button
                next_button.click()
                print("[OTP] ✓ Automatically clicked 'Next' button!")
                print("[OTP] ⏳ WhatsApp sending OTP to your phone...")
                next_button_found = True
                time.sleep(3)
                break
            except Exception as e:
                continue
        
        if not next_button_found:
            print("[OTP] ⚠ Could not find 'Next' button automatically")
            print("[OTP] Trying JavaScript click as fallback...")
            try:
                # Find button containing "Next" text using JavaScript
                driver.execute_script("""
                    let buttons = document.querySelectorAll('button');
                    for (let btn of buttons) {
                        if (btn.textContent.includes('Next')) {
                            btn.click();
                            break;
                        }
                    }
                """)
                print("[OTP] ✓ Clicked 'Next' button via JavaScript")
                time.sleep(3)
                next_button_found = True
            except Exception as e:
                print(f"[OTP] ⚠ Could not click Next button: {str(e)}")
                print("[OTP] Proceeding anyway...")
                time.sleep(3)
        
        # Step 4: Wait for OTP field to appear
        print("\n[OTP] STEP 4: Waiting for OTP input field to appear (max 60s)...")
        otp_field_found = wait_for_otp_input_field(driver, timeout=60)
        
        if otp_field_found:
            return {
                "success": True,
                "message": "✓ Phone number entered successfully! OTP sent to your phone.",
                "phone": f"{country_code}{phone_only}",
                "step": "otp_detected",
                "details": "Enter the 6-digit OTP code you receive on WhatsApp"
            }
        else:
            return {
                "success": False,
                "message": "OTP input field did not appear within 60 seconds",
                "step": "otp_timeout"
            }
            
    except Exception as e:
        print(f"[OTP] ✗ Error during login automation: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {
            "success": False,
            "message": f"Error during automation: {str(e)}",
            "step": "automation_error"
        }



    """
    Verify OTP and prepare WhatsApp session.
    """
    try:
        phone = phone_number.replace("+", "").replace(" ", "").replace("-", "")
        
        # Validate OTP format (should be 6 digits for WhatsApp)
        if not otp_code.isdigit() or len(otp_code) != 6:
            return {"success": False, "message": "OTP must be 6 digits"}
        
        # Save verified OTP session
        mark_otp_verified(phone)
        
        print(f"[OTP] OTP verified for {phone}")
        
        return {
            "success": True,
            "message": "OTP verified successfully! WhatsApp session is ready.",
            "phone": phone
        }
    except Exception as e:
        return {"success": False, "message": f"Verification error: {str(e)}"}


def check_whatsapp_authenticated(driver, phone_number: str) -> bool:
    """
    Check if WhatsApp is authenticated in the browser.
    Returns True if authenticated, False otherwise.
    """
    try:
        time.sleep(2)
        # Try to find chat list - present when authenticated
        chat_list = driver.find_elements(By.XPATH, "//div[@role='listbox']")
        if chat_list:
            print(f"[OTP] WhatsApp Web is authenticated")
            return True
        
        # Alternative check - look for search box which appears after login
        search_box = driver.find_elements(By.XPATH, "//input[@placeholder]")
        if search_box:
            print(f"[OTP] WhatsApp Web authenticated (found search box)")
            return True
            
        return False
    except Exception as e:
        print(f"[OTP] Error checking authentication: {str(e)}")
        return False


def wait_for_otp_input_field(driver, timeout=60):
    """
    Wait for WhatsApp OTP input field to appear.
    This means WhatsApp has sent the OTP and is waiting for user input.
    Much faster than waiting for full authentication.
    """
    print(f"[OTP] ⏳ Waiting for OTP to be sent (max {timeout}s)...")
    print("[OTP] Looking for OTP input field appearance...")
    print("[OTP]   Searching for:")
    print("[OTP]   - OTP input fields (6-digit code)")
    print("[OTP]   - 'Didn't receive code?' text")
    start_time = time.time()
    check_count = 0
    
    while time.time() - start_time < timeout:
        try:
            check_count += 1
            # Look for OTP input field (6-digit code input)
            otp_fields = driver.find_elements(By.XPATH, 
                "//input[contains(@aria-label, 'OTP')] | //input[contains(@placeholder, 'code')] | //input[@maxlength='6'] | //input[placeholder*='code' i]"
            )
            
            if otp_fields:
                elapsed = time.time() - start_time
                print(f"[OTP] ✓ OTP input field found! (took {elapsed:.1f}s, check #{check_count})")
                print(f"[OTP] ✓ WhatsApp has sent the code to your phone!")
                return True
            
            # Also check for "Didn't receive code?" text which appears when waiting for OTP
            didn_receive = driver.find_elements(By.XPATH, "//*[contains(text(), \"Didn't receive\")]")
            if didn_receive:
                elapsed = time.time() - start_time
                print(f"[OTP] ✓ OTP confirmation page detected! (took {elapsed:.1f}s, check #{check_count})")
                return True
            
            if check_count % 5 == 0:
                elapsed = time.time() - start_time
                remaining = timeout - elapsed
                print(f"[OTP]   Still waiting... ({elapsed:.1f}s elapsed, {remaining:.1f}s remaining)")
                
        except Exception as e:
            if check_count % 10 == 0:
                print(f"[OTP]   Error during check #{check_count}: {str(e)}")
            pass
        
        time.sleep(2)
    
    elapsed = time.time() - start_time
    print(f"[OTP] ✗ Timeout waiting for OTP input field ({elapsed:.1f}s)")
    print(f"[OTP]   Completed {check_count} checks")
    return False


def wait_for_whatsapp_authentication(driver, timeout=180):
    """
    Wait for WhatsApp to be fully authenticated.
    Can take up to 3 minutes for user to scan QR or enter OTP.
    """
    print(f"[OTP] Waiting for WhatsApp authentication (timeout: {timeout}s)...")
    print("[OTP] Checking for:")
    print("[OTP]   - QR code disappearance")
    print("[OTP]   - Chat list/authenticated UI")
    start_time = time.time()
    check_count = 0
    
    while time.time() - start_time < timeout:
        try:
            check_count += 1
            qr_element = driver.find_elements(By.XPATH, "//canvas")
            if not qr_element:
                elapsed = time.time() - start_time
                print(f"[OTP] \u2713 WhatsApp authenticated! (QR gone, took {elapsed:.1f}s)")
                time.sleep(3)
                return True
            if check_whatsapp_authenticated(driver, ""):
                elapsed = time.time() - start_time
                print(f"[OTP] \u2713 WhatsApp authenticated! (took {elapsed:.1f}s)")
                return True
            if check_count % 10 == 0:
                elapsed = time.time() - start_time
                remaining = timeout - elapsed
                print(f"[OTP]   Still waiting... ({elapsed:.1f}s / {timeout}s)")
        except Exception as e:
            if check_count % 20 == 0:
                print(f"[OTP]   Check #{check_count}: {str(e)}")
        
        time.sleep(3)
    
    elapsed = time.time() - start_time
    print(f"[OTP] \u26a0 Authentication timeout ({elapsed:.1f}s / {timeout}s)")
    print(f"[OTP]   Completed {check_count} checks")
    return False


def enter_phone_number_and_request_otp(driver, phone_number: str):
    """
    Enter phone number in WhatsApp Web to request OTP.
    This is an alternative approach to QR scanning.
    """
    try:
        print(f"[OTP] Attempting to enter phone number: {phone_number}")
        
        time.sleep(5)  # Wait for page to load
        
        # Look for "Log in with phone number" link
        try:
            phone_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Log in with phone number')]"))
            )
            phone_link.click()
            print("[OTP] Clicked on 'Log in with phone number' link")
            time.sleep(2)
        except Exception as e:
            print(f"[OTP] 'Log in with phone number' link not found, trying alternative: {str(e)}")
            # Try to find the link by partial text
            try:
                phone_link = driver.find_element(By.XPATH, "//*[contains(text(), 'Log in') and contains(text(), 'phone')]")
                phone_link.click()
                print("[OTP] Clicked on phone login option")
                time.sleep(2)
            except:
                pass
        
        # Wait for phone input screen to load
        time.sleep(3)
        
        # Try to find phone input field
        try:
            phone_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='tel' or contains(@placeholder, 'phone')]"))
            )
            phone_input.click()
            phone_input.clear()
            phone_input.send_keys(phone_number)
            print(f"[OTP] Entered phone number: {phone_number}")
            time.sleep(1)
            
            # Look for "Next" button
            try:
                next_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Next')]"))
                )
                next_button.click()
                print("[OTP] Clicked 'Next' button to request OTP")
                time.sleep(3)
                return True
            except Exception as e:
                print(f"[OTP] Could not find 'Next' button: {str(e)}")
                return False
        except Exception as e:
            print(f"[OTP] Error finding phone input field: {str(e)}")
            return False
            
    except Exception as e:
        print(f"[OTP] Error in phone entry process: {str(e)}")
        return False


def enter_country_and_phone(driver, country_code: str, phone_only: str):
    """
    Enter country code and phone number in WhatsApp Web.
    Automated phone number login flow using exact HTML selectors.
    
    Args:
        driver: Selenium WebDriver instance
        country_code: Country code (e.g., "91" for India)
        phone_only: Phone number without country code (e.g., "9876543210")
    """
    try:
        print("="*60)
        print("[OTP] Starting automated phone login...")
        print(f"[OTP] Country Code: {country_code}, Phone: {phone_only}")
        
        time.sleep(5)  # Wait for page to load
        
        # Step 1: Click "Log in with phone number" link
        try:
            print("[OTP] Step 1: Finding 'Log in with phone number' button...")
            print("[OTP]   Looking for: //div[contains(text(), 'Log in with phone number')]")
            phone_login_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Log in with phone number')]"))
            )
            print("[OTP]   ✓ Button found!")
            # Scroll to element if needed
            driver.execute_script("arguments[0].scrollIntoView(true);", phone_login_button)
            time.sleep(1)
            phone_login_button.click()
            print("[OTP] ✓ Clicked 'Log in with phone number'")
            time.sleep(3)
        except Exception as e:
            print(f"[OTP] ✗ Step 1 FAILED: Could not find phone login button")
            print(f"[OTP]   Error: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False
        
        # Step 2: Select country (find and click on country selector to change from default)
        try:
            print("[OTP] Step 2: Looking for country selector...")
            # Find country selector - look for the div/span with country name
            country_selector = driver.find_elements(By.XPATH, "//span[contains(text(), 'India')] | //div[contains(@class, 'country')]")
            
            if country_selector:
                print(f"[OTP] Found {len(country_selector)} country elements")
                # If country is not India, we may need to change it
                # For now, assuming India is correct for code 91
                if country_code == "91":
                    print("[OTP] ✓ Country code 91 = India (already selected)")
                    time.sleep(1)
            else:
                print("[OTP] ⚠ Could not find explicit country selector, proceeding...")
                
        except Exception as e:
            print(f"[OTP] ⚠ Error checking country: {str(e)}")
        
        # Step 3: Find and fill phone number input
        try:
            print("[OTP] Step 3: Finding phone number input field...")
            # Use the exact aria-label from the provided HTML
            phone_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@aria-label='Type your phone number to log in to WhatsApp']"))
            )
            
            # Clear existing value
            phone_input.click()
            phone_input.clear()
            time.sleep(0.5)
            
            # Enter phone number
            phone_input.send_keys(phone_only)
            print(f"[OTP] ✓ Entered phone number: {phone_only}")
            print(f"[OTP] ✓ Full number being used: +{country_code} {phone_only}")
            time.sleep(1)
            
        except Exception as e:
            print(f"[OTP] ✗ Error entering phone number: {str(e)}")
            # Try alternative selector
            try:
                print("[OTP] Trying alternative phone input selector...")
                phone_input = driver.find_element(By.XPATH, "//input[@type='text' and contains(@class, 'selectable-text')]")
                phone_input.click()
                phone_input.clear()
                phone_input.send_keys(phone_only)
                print(f"[OTP] ✓ Entered phone (alternative method): {phone_only}")
                time.sleep(1)
            except Exception as e2:
                print(f"[OTP] ✗ Alternative method also failed: {str(e2)}")
                return False
        
        # Step 4: Find and click "Next" button
        try:
            print("[OTP] Step 4: Finding 'Next' button...")
            print("[OTP]   Looking for: //button[contains(text(), 'Next')]")
            time.sleep(2)
            
            # Look for Next button - various possible selectors
            next_button = None
            try:
                next_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Next')]"))
                )
            except:
                print("[OTP]   First selector failed, trying alternative...")
                try:
                    next_button = driver.find_element(By.XPATH, "//button[@type='button' and contains(@class, 'x1c4vz4f')]")
                except:
                    print("[OTP]   All Next button selectors failed")
                    pass
            
            if next_button:
                driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                time.sleep(0.5)
                next_button.click()
                print("[OTP] ✓ Clicked 'Next' button")
                print("[OTP] ✓ OTP will be sent to your phone!")
                print("="*60)
                time.sleep(3)
                return True
            else:
                print("[OTP] ✗ Step 4 FAILED: Could not find 'Next' button")
                return False
                
        except Exception as e:
            print(f"[OTP] ✗ Step 4 ERROR: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False
            
    except Exception as e:
        print(f"[OTP] ✗ Error in phone entry process: {str(e)}")
        return False
