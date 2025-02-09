import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import PyPDF2
import docx
import requests
import io

# === App Configuration ===
st.set_page_config(page_title="Google API Financial Analysis Agent", layout="wide")

# Set your Google API key (for Cloud Natural Language API)
# Warning: Hardcoding API keys is not secure. Use secrets or environment variables in production.
GOOGLE_API_KEY = "AIzaSyBPwz9vY4BX4pmTLEx28dNiAQfi7sabXE"

st.title("Google API Financial Analysis Agent")
st.write("Upload a financial document (PDF, Excel, Word, or CSV) to get started.")

# === File Upload Section ===
uploaded_file = st.file_uploader("Upload your financial document", type=["pdf", "xlsx", "xls", "docx", "doc", "csv"])

if uploaded_file is not None:
    file_type = uploaded_file.name.split('.')[-1].lower()
    extracted_text = ""
    df = None  # For tabular data if available

    # --- Process PDF Files ---
    if file_type == 'pdf':
        try:
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            for page in pdf_reader.pages:
                extracted_text += page.extract_text()
        except Exception as e:
            st.error(f"Error reading PDF file: {e}")

    # --- Process Word Documents ---
    elif file_type in ['docx', 'doc']:
        try:
            doc = docx.Document(uploaded_file)
            extracted_text = "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            st.error(f"Error reading Word document: {e}")

    # --- Process Excel Files ---
    elif file_type in ['xlsx', 'xls']:
        try:
            df = pd.read_excel(uploaded_file)
            extracted_text = df.to_csv(index=False)
        except Exception as e:
            st.error(f"Error reading Excel file: {e}")

    # --- Process CSV Files ---
    elif file_type == 'csv':
        try:
            df = pd.read_csv(uploaded_file)
            extracted_text = df.to_csv(index=False)
        except Exception as e:
            st.error(f"Error reading CSV file: {e}")

    else:
        st.error("Unsupported file format.")

    # --- Display Extracted Data ---
    st.subheader("Extracted Data")
    st.text_area("File Content", extracted_text, height=300)

    # --- (Optional) Generate a Trend Graph for Tabular Data ---
    if df is not None:
        st.subheader("Sample Trend Graph")
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
        if numeric_columns:
            fig, ax = plt.subplots()
            ax.plot(df.index, df[numeric_columns[0]], marker='o')
            ax.set_title(f"Trend of {numeric_columns[0]}")
            ax.set_xlabel("Index")
            ax.set_ylabel(numeric_columns[0])
            st.pyplot(fig)
        else:
            st.info("No numeric columns found to plot a trend graph.")

    # === Google Cloud Natural Language API Analysis ===
    st.subheader("Analyze Document with Google Cloud Natural Language API")
    if st.button("Analyze Document"):
        if extracted_text.strip() == "":
            st.error("No text extracted from the document.")
        else:
            # Define helper functions that call the Google API endpoints
            def analyze_sentiment(text, api_key):
                url = f"https://language.googleapis.com/v1/documents:analyzeSentiment?key={api_key}"
                headers = {"Content-Type": "application/json"}
                data = {
                    "document": {
                        "type": "PLAIN_TEXT",
                        "content": text
                    },
                    "encodingType": "UTF8"
                }
                response = requests.post(url, headers=headers, json=data)
                return response.json()

            def analyze_entities(text, api_key):
                url = f"https://language.googleapis.com/v1/documents:analyzeEntities?key={api_key}"
                headers = {"Content-Type": "application/json"}
                data = {
                    "document": {
                        "type": "PLAIN_TEXT",
                        "content": text
                    },
                    "encodingType": "UTF8"
                }
                response = requests.post(url, headers=headers, json=data)
                return response.json()

            with st.spinner("Analyzing document..."):
                sentiment_result = analyze_sentiment(extracted_text, GOOGLE_API_KEY)
                entities_result = analyze_entities(extracted_text, GOOGLE_API_KEY)

            # --- Display Sentiment Analysis Results ---
            st.subheader("Sentiment Analysis")
            try:
                sentiment = sentiment_result.get("documentSentiment", {})
                score = sentiment.get("score", "N/A")
                magnitude = sentiment.get("magnitude", "N/A")
                st.write(f"**Sentiment Score:** {score}")
                st.write(f"**Sentiment Magnitude:** {magnitude}")
            except Exception as e:
                st.error("Error parsing sentiment analysis result.")

            # --- Display Entity Analysis Results ---
            st.subheader("Entity Analysis")
            try:
                entities = entities_result.get("entities", [])
                if entities:
                    for entity in entities:
                        name = entity.get("name", "N/A")
                        entity_type = entity.get("type", "N/A")
                        salience = entity.get("salience", 0)
                        st.write(f"**Entity:** {name} | **Type:** {entity_type} | **Salience:** {salience:.2f}")
                else:
                    st.write("No entities found.")
            except Exception as e:
                st.error("Error parsing entity analysis result.")
