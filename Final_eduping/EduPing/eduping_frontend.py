import streamlit as st
import pandas as pd
import tempfile
import time
from eduping_backend import eduping_backend as core
from auth import register_user, login_user, get_user_by_email, update_whatsapp_number


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
    st.session_state.current_page = "login"
# Custom CSS for better UI
st.markdown("""
    <style>
        .main {
            padding-top: 2rem;
        }
        .stButton>button {
            width: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
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
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .auth-container {
            max-width: 400px;
            margin: 2rem auto;
            padding: 2rem;
            border-radius: 15px;
            background: white;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .uploadedFile {
            border: 2px dashed #667eea;
            border-radius: 10px;
            padding: 1rem;
            margin: 1rem 0;
        }
        .status-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
        }
        h1 {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
    </style>
""", unsafe_allow_html=True)


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
                <p style="font-size: 1rem; color: #666;">AI-Powered Student Notifications</p>
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


def show_signup_page():
    """Display signup page"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
            <div style="text-align: center; margin-bottom: 2rem;">
                <h1 style="font-size: 2.5rem; margin-bottom: 0.5rem;">📚 EduPing</h1>
                <p style="font-size: 1rem; color: #666;">Join Our Community</p>
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


# =========================
# MAIN APPLICATION PAGE
# =========================
def show_main_page():
    """Display main application"""
    # Sidebar with user info and logout
    with st.sidebar:
        st.markdown("### 👤 Account")
        st.markdown(f"**{st.session_state.user_data['full_name']}**")
        st.caption(st.session_state.user_data['email'])
        
        # Display current WhatsApp
        st.markdown("---")
        st.markdown(f"📱 **WhatsApp:** `{st.session_state.user_data['whatsapp_number']}`")
        
        if st.button("⚙️ Update WhatsApp Number"):
            st.session_state.current_page = "settings"
            st.rerun()
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_data = None
            st.session_state.current_page = "login"
            st.rerun()
    
    # Header
    st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1 style="font-size: 3rem; margin-bottom: 0.5rem;">📚 EduPing</h1>
            <p style="font-size: 1.2rem; color: #666;">AI-Powered Student Notifications</p>
            <p style="color: #999;">Keep your students updated with clear, understandable messages</p>
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
                <div style="background: #d4edda; border-left: 4px solid #28a745; padding: 1rem; border-radius: 5px; margin: 1rem 0;">
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
    else:
        show_login_page()
else:
    if st.session_state.current_page == "settings":
        show_settings_page()
    else:
        show_main_page()
