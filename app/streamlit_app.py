import os
import streamlit as st
import requests
import json
from datetime import datetime

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="Logistics AI Assistant",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        opacity: 0.8;
        margin-bottom: 2rem;
    }
    .confidence-high {
        padding: 0.5rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        color: #155724 !important;
        font-weight: bold;
    }
    .confidence-medium {
        padding: 0.5rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        color: #856404 !important;
        font-weight: bold;
    }
    .confidence-low {
        padding: 0.5rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        color: #721c24 !important;
        font-weight: bold;
    }
    .source-box {
        padding: 1rem;
        background-color: rgba(31, 119, 180, 0.1);
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)


def get_api_status():
    """Check API health and document status."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=15)
        if response.status_code == 200:
            data = response.json()
            return True, data.get("document_loaded", False), data.get("filename")
        return False, False, None
    except:
        return False, False, None


def get_document_text():
    """Fetch the full extracted text of the current document."""
    try:
        response = requests.get(f"{API_BASE_URL}/document/text", timeout=30)
        if response.status_code == 200:
            return response.json().get("full_text", "")
        return ""
    except:
        return ""
    
    
def upload_document(file):
    """Upload document to the API."""
    try:
        files = {"file": (file.name, file, "application/octet-stream")}
        response = requests.post(f"{API_BASE_URL}/upload", files=files, timeout=60)
        
        # Check if request was successful
        if response.status_code == 200:
            return response.json()
        else:
            # Handle 4xx/5xx errors
            error_data = response.json()
            return {"error": error_data.get("detail", f"Unexpected error (Status: {response.status_code})")}
    except Exception as e:
        return {"error": str(e)}


def ask_question(question):
    """Ask a question via the API."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/ask",
            json={"question": question},
            timeout=30
        )
        # Check if request was successful
        if response.status_code == 200:
            return response.json()
        else:
            # Handle 4xx/5xx errors
            error_data = response.json()
            return {"error": error_data.get("detail", f"Unexpected error (Status: {response.status_code})")}
    except Exception as e:
        return {"error": str(e)}


def extract_structured():
    """Extract structured data via the API."""
    try:
        response = requests.post(f"{API_BASE_URL}/extract", timeout=60)
        # Check if request was successful
        if response.status_code == 200:
            return response.json()
        else:
            # Handle 4xx/5xx errors
            error_data = response.json()
            return {"error": error_data.get("detail", f"Unexpected error (Status: {response.status_code})")}
    except Exception as e:
        return {"error": str(e)}


def render_confidence_badge(confidence):
    """Render a colored badge based on confidence score."""
    if confidence >= 0.75:
        return f'<div class="confidence-high">Confidence: {confidence:.1%}</div>'
    elif confidence >= 0.5:
        return f'<div class="confidence-medium">Confidence: {confidence:.1%}</div>'
    else:
        return f'<div class="confidence-low">Confidence: {confidence:.1%}</div>'


def main():
    # Header
    st.markdown('<div class="main-header">🚢 Logistics AI Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">AI-powered logistics document analysis and Q&A system</div>', unsafe_allow_html=True)
    
    # API Health and Document Status Check
    api_connected, document_loaded, current_filename = get_api_status()
    
    if not api_connected:
        st.error(f"⚠️ **API Backend Not Available** - Please ensure the FastAPI server is running on {API_BASE_URL}")
        st.stop()
    
    # Sidebar
    with st.sidebar:
        st.header("📄 Document Upload")
        
        # Display current status
        if document_loaded:
            st.success(f"**🟢 Active Document:**\n{current_filename}")
        else:
            st.warning("**🔴 No Document Loaded**")
            
        st.markdown("---")
        
        uploaded_file = st.file_uploader(
            "Upload New Document",
            type=['pdf', 'docx', 'txt'],
            help="Upload rate confirmations, BOLs, shipment instructions, or invoices"
        )
        
        # Check if the file has already been uploaded in this session
        if uploaded_file and st.session_state.get('last_uploaded_file') != uploaded_file.name:
            with st.spinner("Processing document..."):
                result = upload_document(uploaded_file)
            
            if "error" in result:
                st.error(f"❌ Upload failed: {result['error']}")
            else:
                st.success(f"✅ {result['message']}")
                # Track this file as processed
                st.session_state['last_uploaded_file'] = uploaded_file.name
                
                # AUTOMATIC EXTRACTION: Trigger structured extraction immediately
                with st.spinner("Performing initial data extraction..."):
                    extract_result = extract_structured()
                    if "extracted_data" in extract_result:
                        st.session_state['auto_extraction'] = extract_result["extracted_data"]
                
                # Force refresh to update document_loaded status
                st.rerun()
    
    # Main content area with tabs
    tab1, tab2, tab3 = st.tabs(["❓ Ask Questions", "📊 Structured Extraction", "📄 Document Text"])
    
    # Automatic Extraction Summary (Always visible if document loaded)
    if document_loaded and 'auto_extraction' in st.session_state:
        with st.expander("📝 Quick Shipment Summary", expanded=True):
            data = st.session_state['auto_extraction']
            # Show all 11 fields as requested in the skill test
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Shipment ID", data.get("shipment_id", "N/A"))
                st.metric("Mode", data.get("mode", "N/A"))
                st.metric("Equipment", data.get("equipment_type", "N/A"))
            with col2:
                st.metric("Carrier", data.get("carrier_name", "N/A"))
                st.metric("Rate", f"{data.get('rate', 'N/A')} {data.get('currency', '')}")
                st.metric("Weight", data.get("weight", "N/A"))
            with col3:
                st.metric("Shipper", data.get("shipper", "N/A"))
                st.metric("Pickup", data.get("pickup_datetime", "N/A")[:16])
            with col4:
                st.metric("Consignee", data.get("consignee", "N/A"))
                st.metric("Delivery", data.get("delivery_datetime", "N/A")[:16])
    
    # Tab 1: Q&A
    with tab1:
        if not document_loaded:
            st.warning("⚠️ **No document loaded.** Please upload a document in the sidebar to start asking questions.")
        
        question = st.text_input(
            "Your Question:",
            placeholder="e.g., What is the carrier rate?",
            key="question_input",
            disabled=not document_loaded
        )
        
        if question:
            with st.spinner("Searching document and generating answer..."):
                result = ask_question(question)
            
            if "error" in result:
                st.error(f"❌ Error: {result['error']}")
            else:
                # Display answer
                st.subheader("Answer:")
                st.write(result.get("answer", "No answer provided"))
                
                # Display confidence
                confidence = result.get("confidence", 0.0)
                st.markdown(render_confidence_badge(confidence), unsafe_allow_html=True)
                
                # Display guardrail status
                if result.get("guardrail_triggered"):
                    st.warning(f"⚠️ **Guardrail Activated:** {result.get('guardrail_reason', 'Unknown reason')}")
                
                # Display sources
                st.subheader("📚 Supporting Sources:")
                sources = result.get("sources", [])
                if sources:
                    for i, source in enumerate(sources, 1):
                        with st.expander(f"Source {i} (Similarity: {source.get('similarity', 0):.1%})"):
                            st.markdown(f'<div class="source-box">{source.get("text", "")}</div>', unsafe_allow_html=True)
                else:
                    st.info("No relevant sources found in the document.")
    
    # Tab 2: Structured Extraction
    with tab2:
        st.header("Structured Shipment Data Extraction")
        st.caption("Extract key shipment fields from the uploaded document")
        
        if not document_loaded:
            st.warning("⚠️ **No document loaded.** Please upload a document in the sidebar to extract structured data.")
        
        if st.button("🔍 Extract Structured Data", type="primary", disabled=not document_loaded):
            with st.spinner("Extracting shipment data..."):
                result = extract_structured()
            
            if "error" in result:
                st.error(f"❌ Extraction failed: {result['error']}")
            elif result.get("status") == "error":
                st.error(f"❌ {result.get('message', 'Unknown error')}")
                if result.get("raw_output"):
                    with st.expander("View Raw Output"):
                        st.code(result["raw_output"])
            else:
                st.success("✅ Extraction Complete")
                
                extracted_data = result.get("extracted_data", {})
                
                # Display as JSON
                st.subheader("Extracted Data (JSON):")
                st.json(extracted_data)
                
                # Display as table
                st.subheader("Extracted Data (Table):")
                
                # Create a nice table view
                data_rows = []
                for key, value in extracted_data.items():
                    display_key = key.replace("_", " ").title()
                    display_value = str(value) if value is not None else "❌ Not Found"
                    data_rows.append({"Field": display_key, "Value": display_value})
                
                st.table(data_rows)
                
    # Tab 3: Document Text
    with tab3:
        st.header("Extracted Document Content")
        st.caption("Raw text extracted from the uploaded document")
        
        if not document_loaded:
            st.warning("⚠️ **No document loaded.** Please upload a document in the sidebar to view extracted text.")
        else:
            if st.button("🔄 Fetch/Refresh Text"):
                with st.spinner("Fetching document text..."):
                    full_text = get_document_text()
                    if full_text:
                        st.text_area("Full Extracted Text", full_text, height=600)
                    else:
                        st.error("Could not retrieve document text.")
    
    # Footer
    st.markdown("---")
    st.caption("Logistics AI Assistant POC | Built with Streamlit, FastAPI, and RAG")


if __name__ == "__main__":
    main()
