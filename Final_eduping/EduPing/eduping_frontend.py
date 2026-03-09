import streamlit as st
import pandas as pd
import tempfile
import time
from eduping_backend import eduping_backend as core
from auth import register_user, login_user, get_user_by_email, update_whatsapp_number, update_full_name


# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="📚 EduPing",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================
# SESSION STATE INITIALIZATION
# =========================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_data" not in st.session_state:
    st.session_state.user_data = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"
# Custom CSS – richer, bolder palette
st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(180deg, #f5f3ff 0%, #ede9fe 50%, #e9d5ff 100%);
        }
        .main {
            padding-top: 2rem;
            background: transparent;
        }
        .block-container {
            background: transparent;
        }
        .stButton>button {
            width: 100%;
            background: linear-gradient(90deg, #4338ca 0%, #6d28d9 50%, #7e22ce 100%);
            color: white;
            font-weight: bold;
            font-size: 1.1rem;
            padding: 0.75rem 2rem;
            border-radius: 10px;
            border: none;
            transition: all 0.3s;
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(67, 56, 202, 0.55);
        }
        .auth-container {
            max-width: 400px;
            margin: 2rem auto;
            padding: 2rem;
            border-radius: 15px;
            background: #ffffff;
            box-shadow: 0 8px 24px rgba(67, 56, 202, 0.15);
        }
        .uploadedFile {
            border: 2px dashed #5b21b6;
            border-radius: 10px;
            padding: 1rem;
            margin: 1rem 0;
        }
        .status-box {
            background: linear-gradient(135deg, #4338ca 0%, #7c3aed 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
        }
        h1 {
            background: linear-gradient(90deg, #4338ca 0%, #7c3aed 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .hero-box {
            background: linear-gradient(135deg, #3730a3 0%, #5b21b6 50%, #6d28d9 100%);
            color: white;
            padding: 2.5rem;
            border-radius: 20px;
            margin: 2rem 0;
            text-align: center;
            box-shadow: 0 12px 48px rgba(91, 33, 182, 0.45);
        }
        .feature-card {
            background: linear-gradient(135deg, #ede9fe 0%, #e9d5ff 100%);
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            border-left: 4px solid #6d28d9;
        }
        .about-section {
            background: linear-gradient(135deg, #e0e7ff 0%, #ddd6fe 100%);
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            border: 1px solid #a78bfa;
        }
        /* Go to profile button: same proportions as Browse files (compact horizontal bar) */
        .profile-nav-bar .stButton>button {
            height: 38px !important;
            min-height: 38px !important;
            padding: 0.25rem 1rem !important;
            font-size: 0.875rem !important;
            line-height: 1.2 !important;
            white-space: nowrap;
        }
    </style>
""", unsafe_allow_html=True)


# =========================
# HOME PAGE (Landing + About snippet)
# =========================
def show_home_page():
    """Landing page with hero, features, about snippet, and auth CTAs"""
    st.markdown("""
        <div class="hero-box">
            <h1 style="color: white; font-size: 3rem; margin-bottom: 0.5rem;">📚 EduPing</h1>
            <p style="font-size: 1.3rem; opacity: 0.95;">AI-Powered Student Notifications</p>
            <p style="font-size: 1rem; opacity: 0.9; max-width: 600px; margin: 1rem auto;">
                Turn announcements and documents into clear, student-friendly WhatsApp messages. 
                Keep your class updated without the hassle.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # CTA buttons
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        if st.button("🔐 Login", use_container_width=True):
            st.session_state.current_page = "login"
            st.rerun()
    with col2:
        if st.button("📝 Sign Up", use_container_width=True):
            st.session_state.current_page = "signup"
            st.rerun()
    with col3:
        if st.button("ℹ️ About", use_container_width=True):
            st.session_state.current_page = "about"
            st.rerun()
    with col4:
        if st.session_state.authenticated and st.button("📊 Dashboard", use_container_width=True):
            st.session_state.current_page = "main"
            st.rerun()
    
    st.markdown("---")
    st.markdown("### ✨ What EduPing Does")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="feature-card">
            <strong>📄 Upload & Summarize</strong><br>
            Upload PDFs, DOCX, or text. AI turns them into clear, short summaries students can understand.
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="feature-card">
            <strong>📱 WhatsApp Delivery</strong><br>
            Send notifications via WhatsApp in one go. Use your number; we handle the rest.
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="feature-card">
            <strong>👥 Batch & Lists</strong><br>
            Upload a list of phone numbers (CSV/TXT). We send to everyone without manual copying.
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("""
    <div class="about-section">
        <strong>About EduPing</strong><br>
        EduPing helps educators and admins send exam dates, placement drives, and other updates 
        to students quickly and clearly. Messages are rewritten in simple language so every student stays in the loop.
    </div>
    """, unsafe_allow_html=True)
    if st.button("ℹ️ Read more on About page"):
        st.session_state.current_page = "about"
        st.rerun()


# =========================
# ABOUT PAGE
# =========================
def show_about_page():
    """Dedicated About page: mission, how it works, tech, credits"""
    st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1 style="font-size: 2.5rem;">ℹ️ About EduPing</h1>
            <p style="color: #374151;">Mission, features, and how it works</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🎯 Mission")
    st.markdown("""
    EduPing makes it easy to keep students informed. Instead of long PDFs or confusing notices, 
    educators upload content once; our AI creates short, clear summaries and sends them via WhatsApp 
    to a list of numbers. Perfect for exam dates, placement drives, fee reminders, and general announcements.
    """)
    
    st.markdown("### 🔄 How It Works")
    st.markdown("""
    1. **Create an account** and add your WhatsApp number (used to send messages).  
    2. **Upload two files**: one with phone numbers (CSV/TXT/PDF/DOCX), one with the message or document.  
    3. **AI summarizes** the content into student-friendly language.  
    4. **Log in to WhatsApp Web** once (OTP on your phone) so we can send on your behalf.  
    5. **Messages go out** in the background to all numbers in your list.
    """)
    
    st.markdown("### 🛠 Technology")
    st.markdown("""
    - **Frontend:** Streamlit  
    - **Backend:** Python, Selenium (WhatsApp Web automation)  
    - **AI:** Local summarization for clear, readable messages  
    - **Auth & data:** SQLite, bcrypt for secure login  
    - **Files:** CSV, TXT, PDF, DOCX supported for both numbers and messages
    """)
    
    st.markdown("### 📌 Notes")
    st.markdown("""
    - Keep the browser window open while sending; do not close it until the run finishes.  
    - Use phone numbers with country code (e.g. 91 for India).  
    - EduPing is for educational and official use; respect WhatsApp’s terms of service.
    """)
    
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("🏠 Back to Home", use_container_width=True):
            st.session_state.current_page = "home"
            st.rerun()
    with col2:
        if not st.session_state.authenticated and st.button("🔐 Login", use_container_width=True):
            st.session_state.current_page = "login"
            st.rerun()
    with col3:
        if st.session_state.authenticated and st.button("📊 Dashboard", use_container_width=True):
            st.session_state.current_page = "main"
            st.rerun()


# =========================
# PROFILE PAGE (logged-in only)
# =========================
def show_profile_page():
    """User profile: view and edit name, email (read-only), WhatsApp"""
    st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1 style="font-size: 2.5rem;">👤 Profile</h1>
            <p style="color: #374151;">Your account information</p>
        </div>
    """, unsafe_allow_html=True)
    
    u = st.session_state.user_data
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("**Full name**")
        st.info(u.get("full_name") or "—")
        st.markdown("**Email**")
        st.info(u.get("email") or "—")
        st.markdown("**WhatsApp number**")
        st.info(u.get("whatsapp_number") or "—")
    with col2:
        with st.form("profile_form"):
            st.markdown("### Edit profile")
            new_name = st.text_input("Full name", value=u.get("full_name") or "", placeholder="Your display name")
            new_whatsapp = st.text_input(
                "WhatsApp number",
                value=u.get("whatsapp_number") or "",
                placeholder="919876543210 (with country code)"
            )
            sub1, sub2 = st.columns(2)
            with sub1:
                submitted = st.form_submit_button("💾 Save changes")
            with sub2:
                cancel = st.form_submit_button("Cancel")
            if submitted:
                if not new_name.strip():
                    st.error("Name cannot be empty.")
                elif not new_whatsapp or not new_whatsapp.replace(" ", "").replace("+", "").isdigit():
                    st.error("WhatsApp number must contain only digits (with optional + or spaces).")
                else:
                    r1 = update_full_name(u["email"], new_name.strip())
                    r2 = update_whatsapp_number(u["email"], new_whatsapp.replace(" ", "").replace("+", ""))
                    if r1.get("success") and r2.get("success"):
                        st.session_state.user_data["full_name"] = new_name.strip()
                        st.session_state.user_data["whatsapp_number"] = new_whatsapp.replace(" ", "").replace("+", "")
                        st.success("Profile updated successfully!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        for r in (r1, r2):
                            if not r.get("success"):
                                st.error(r.get("message", "Update failed"))
            if cancel:
                st.session_state.current_page = "main"
                st.rerun()
    
    st.markdown("---")
    if st.button("⚙️ Open full settings"):
        st.session_state.current_page = "settings"
        st.rerun()
    if st.button("📊 Back to Dashboard"):
        st.session_state.current_page = "main"
        st.rerun()


# =========================
# AUTHENTICATION PAGES
# =========================
def show_login_page():
    """Display login page"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
            <div style="text-align: center; margin-bottom: 2rem;">
                <h1 style="font-size: 2.5rem; margin-bottom: 0.5rem;">📚 EduPing</h1>
                <p style="font-size: 1rem; color: #374151;">AI-Powered Student Notifications</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🔐 Login to Your Account")
        
        email = st.text_input("📧 Email", placeholder="your.email@example.com")
        password = st.text_input("🔑 Password", type="password", placeholder="Enter your password")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Login", use_container_width=True):
                if email and password:
                    result = login_user(email, password)
                    if result["success"]:
                        st.session_state.authenticated = True
                        st.session_state.user_data = result["user_data"]
                        st.session_state.current_page = "main"
                        st.success("✅ Login successful!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(f"❌ {result['message']}")
                else:
                    st.warning("⚠️ Please enter email and password")
        
        with col2:
            if st.button("Sign Up", use_container_width=True):
                st.session_state.current_page = "signup"
                st.rerun()
        
        st.markdown("---")
        if st.button("🏠 Back to Home", use_container_width=True):
            st.session_state.current_page = "home"
            st.rerun()


def show_signup_page():
    """Display signup page"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
            <div style="text-align: center; margin-bottom: 2rem;">
                <h1 style="font-size: 2.5rem; margin-bottom: 0.5rem;">📚 EduPing</h1>
                <p style="font-size: 1rem; color: #374151;">Join Our Community</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📝 Create Your Account")
        
        full_name = st.text_input("👤 Full Name", placeholder="John Doe")
        email = st.text_input("📧 Email", placeholder="your.email@example.com")
        password = st.text_input("🔑 Password", type="password", placeholder="At least 6 characters")
        whatsapp = st.text_input("📱 WhatsApp Number", placeholder="919876543210 (with country code)")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Sign Up", use_container_width=True):
                if all([full_name, email, password, whatsapp]):
                    result = register_user(email, password, whatsapp, full_name)
                    if result["success"]:
                        st.success("✅ Account created successfully! Please login now.")
                        time.sleep(1)
                        st.session_state.current_page = "login"
                        st.rerun()
                    else:
                        st.error(f"❌ {result['message']}")
                else:
                    st.warning("⚠️ Please fill all fields")
        
        with col2:
            if st.button("Back to Login", use_container_width=True):
                st.session_state.current_page = "login"
                st.rerun()
        
        st.markdown("---")
        if st.button("🏠 Back to Home", use_container_width=True):
            st.session_state.current_page = "home"
            st.rerun()


# =========================
# MAIN APPLICATION PAGE
# =========================
def show_main_page():
    """Display main application"""
    # Sidebar: nav + user info + logout
    with st.sidebar:
        st.markdown("### 👤 Account")
        st.markdown(f"**{st.session_state.user_data.get('full_name') or 'User'}**")
        st.caption(st.session_state.user_data.get('email', ''))
        st.markdown(f"📱 `{st.session_state.user_data.get('whatsapp_number', '')}`")
        st.markdown("---")
        st.markdown("**Navigate**")
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.current_page = "home"
            st.rerun()
        if st.button("ℹ️ About", use_container_width=True):
            st.session_state.current_page = "about"
            st.rerun()
        if st.button("👤 Profile", use_container_width=True):
            st.session_state.current_page = "profile"
            st.rerun()
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state.current_page = "main"
            st.rerun()
        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.current_page = "settings"
            st.rerun()
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_data = None
            st.session_state.current_page = "home"
            st.rerun()
    
    # Header
    st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1 style="font-size: 3rem; margin-bottom: 0.5rem;">📚 EduPing</h1>
            <p style="font-size: 1.2rem; color: #374151;">AI-Powered Student Notifications</p>
            <p style="color: #4b5563;">Keep your students updated with clear, understandable messages</p>
        </div>
    """, unsafe_allow_html=True)


    # =========================
    # FILE UPLOADS
    # =========================
    col1, col2 = st.columns(2)

    with col1:
        phones_file = st.file_uploader(
            "📞 Upload Phone Numbers File",
            type=["csv", "txt", "pdf", "docx"],
            help="File containing phone numbers (CSV, TXT, PDF, or DOCX). CSV can have a 'phone' column or use the first column."
        )

    with col2:
        messages_file = st.file_uploader(
            "📝 Upload Messages File",
            type=["csv", "txt", "pdf", "docx"],
            help="File containing messages to send (CSV, TXT, PDF, or DOCX)"
        )

    # =========================
    # VALIDATION & PREVIEW
    # =========================
    if phones_file and messages_file:
        try:
            # Save both files temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=phones_file.name) as tmp:
                tmp.write(phones_file.read())
                phone_path = tmp.name

            with tempfile.NamedTemporaryFile(delete=False, suffix=messages_file.name) as tmp:
                tmp.write(messages_file.read())
                message_path = tmp.name

            # Extract phones for preview and count (now returns batches dict)
            phone_batches = core.extract_phones_from_file(phone_path)
            
            # Calculate total phone count and get all phones for preview
            all_phones = []
            for batch_id, phones in sorted(phone_batches.items()):
                all_phones.extend(phones)
            phone_count = len(all_phones)
            batch_count = len(phone_batches)

            # Create preview dataframe
            if phones_file.name.lower().endswith('.csv'):
                try:
                    phone_df = pd.read_csv(phone_path)
                    if "phone" in phone_df.columns:
                        if "batch_id" in phone_df.columns:
                            preview_df = phone_df[["batch_id", "phone"]].head()
                        else:
                            preview_df = phone_df[["phone"]].head()
                    else:
                        # Use first column
                        preview_df = phone_df.iloc[:, [0]].head()
                        preview_df.columns = ["Phone Numbers"]
                except:
                    preview_df = pd.DataFrame({"Phone Numbers": all_phones[:10]})
            else:
                # For non-CSV files, create a simple preview
                preview_df = pd.DataFrame({"Phone Numbers": all_phones[:10]})

            # Success message with better styling
            st.markdown("""
                <div style="background: #d1fae5; border-left: 4px solid #059669; padding: 1rem; border-radius: 5px; margin: 1rem 0;">
                    <strong>✅ Files uploaded successfully!</strong>
                </div>
            """, unsafe_allow_html=True)

            # Summary cards
            col1, col2 = st.columns(2)
            with col1:
                st.metric("📞 Phone Numbers", phone_count)
            with col2:
                st.metric("📝 Message File", messages_file.name)

            with st.expander("🔍 Preview phone numbers"):
                st.dataframe(preview_df, width='stretch')

            # =========================
            # ACTION
            # =========================
            # Initialize session state
            if 'sending' not in st.session_state:
                st.session_state.sending = False
            if 'start_time' not in st.session_state:
                st.session_state.start_time = None
            
            # Send Notifications: opens WhatsApp Web, auto-enters phone, user enters OTP, then messages send
            user_whatsapp = st.session_state.user_data.get("whatsapp_number") if st.session_state.user_data else None
            if st.button("🚀 Send Notifications", width='stretch'):
                st.session_state.sending = True
                st.session_state.start_time = time.time()
                core.send_bulk_from_files(
                    phone_path,
                    message_path,
                    user_whatsapp=user_whatsapp,
                    use_authenticated_session=False
                )
                st.rerun()
            
            # Show status if sending
            if st.session_state.get('sending', False):
                status_data = core.get_status()
                current_status = status_data.get("status", "idle")
                
                if current_status == "processing":
                    st.info("🔄 **Generating summaries...** Creating clear, student-friendly summaries using AI")
                    st.progress(0.3)
                    time.sleep(2)
                    st.rerun()

                elif current_status == "waiting_login":
                    msg = status_data.get("message", "Please log in to WhatsApp Web in the opened browser.")
                    st.warning(f"🔐 **Log in to WhatsApp** — {msg}")
                    st.info("📱 WhatsApp Web has opened. Your phone number was entered automatically. Enter the OTP from your phone when it arrives. After login, the window will hide and messages will send.")
                    st.progress(0.4)
                    time.sleep(2)
                    st.rerun()
                    
                elif current_status == "sending":
                    progress = status_data.get("progress", 0)
                    total = status_data.get("total", 1)
                    message = status_data.get("message", "")
                    
                    if total > 0:
                        progress_pct = progress / total
                        st.info(f"📤 **Sending messages...** {message}")
                        st.progress(progress_pct)
                        st.caption(f"Progress: {progress} / {total} messages sent")
                    else:
                        st.info("📤 **Preparing to send messages...**")
                        st.progress(0.5)
                    
                    # Auto-refresh every 2 seconds
                    time.sleep(2)
                    st.rerun()
                        
                elif current_status == "completed":
                    total = status_data.get("total", 0)
                    st.success(f"✅ **Success!** All {total} messages have been sent successfully!")
                    st.progress(1.0)
                    st.session_state.sending = False
                    core.clear_status()
                    
                elif current_status == "error":
                    error_msg = status_data.get("message", "Unknown error occurred")
                    st.error(f"❌ **Error:** {error_msg}")
                    st.session_state.sending = False
                    core.clear_status()
                
                else:
                    # Still processing, refresh
                    if st.session_state.start_time and (time.time() - st.session_state.start_time) < 300:
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.warning("⏱️ **Timeout:** Process is taking longer than expected. Check backend status.")
                        st.session_state.sending = False
                
        except Exception as e:
            st.error(f"❌ **Error:** {str(e)}")
            st.exception(e)
    else:
        # Show instructions when files are not uploaded
        st.info("👆 **Please upload both files above to get started**")
        
        with st.expander("📖 How it works"):
            st.markdown("""
            1. **Upload Phone Numbers File**: CSV (with 'phone' column or first column), TXT, PDF, or DOCX containing phone numbers
            2. **Upload Messages File**: Your messages in CSV, TXT, PDF, or DOCX format
            3. **AI Processing**: Our AI (Phi) will generate clear, student-friendly summaries
            4. **Automatic Sending**: Messages are sent via WhatsApp in the background
            5. **No WhatsApp UI**: All WhatsApp operations happen in the backend - you won't see anything!
            
            **Features:**
            - ✨ Clear, understandable summaries that students can easily read
            - 🔒 Secure backend processing - WhatsApp runs completely in the background
            - 📊 Real-time progress tracking
            - 🎨 Beautiful, modern interface
            - 📁 Support for multiple file formats (CSV, TXT, PDF, DOCX)
            """)


def show_settings_page():
    """Display account settings page"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
            <div style="text-align: center; margin-bottom: 2rem;">
                <h1 style="font-size: 2.5rem; margin-bottom: 0.5rem;">⚙️ Account Settings</h1>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"**Name:** {st.session_state.user_data['full_name']}")
        st.markdown(f"**Email:** {st.session_state.user_data['email']}")
        
        st.markdown("### Update WhatsApp Number")
        new_whatsapp = st.text_input(
            "📱 New WhatsApp Number", 
            value=st.session_state.user_data['whatsapp_number'],
            placeholder="919876543210 (with country code)"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Changes", use_container_width=True):
                if new_whatsapp:
                    result = update_whatsapp_number(st.session_state.user_data['email'], new_whatsapp)
                    if result["success"]:
                        # Update session state
                        st.session_state.user_data['whatsapp_number'] = new_whatsapp
                        st.success("✅ WhatsApp number updated successfully!")
                        time.sleep(0.5)
                        st.session_state.current_page = "main"
                        st.rerun()
                    else:
                        st.error(f"❌ {result['message']}")
                else:
                    st.warning("⚠️ Please enter a valid WhatsApp number")
        
        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.current_page = "main"
                st.rerun()


# =========================
# MAIN APP ROUTER
# =========================
if not st.session_state.authenticated:
    if st.session_state.current_page == "signup":
        show_signup_page()
    elif st.session_state.current_page == "login":
        show_login_page()
    elif st.session_state.current_page == "about":
        show_about_page()
    else:
        show_home_page()
else:
    # Top bar: "Go to profile" next to sidebar (>>) – same size as Browse files button
    st.markdown("<div class='profile-nav-bar'>", unsafe_allow_html=True)
    nav_col, _ = st.columns([2, 7])
    with nav_col:
        if st.button("👤 Go to profile", use_container_width=True):
            st.session_state.current_page = "profile"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div style='margin-top: -0.5rem;'></div>", unsafe_allow_html=True)
    if st.session_state.current_page == "settings":
        show_settings_page()
    elif st.session_state.current_page == "profile":
        show_profile_page()
    elif st.session_state.current_page == "home":
        show_home_page()
    elif st.session_state.current_page == "about":
        show_about_page()
    else:
        show_main_page()
