import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import openai
import PyPDF2
import docx
import io

# === Configuration ===
st.set_page_config(page_title="AI Financial Analysis Agent", layout="wide")

# Set your OpenAI API key.
# For local testing, you can set your API key here. For deployment on Streamlit Cloud, use secrets management.
openai.api_key = st.secrets.get("OPENAI_API_KEY", "YAIzaSyB6Evv1kEmmQRCRNgd3rpLWo5NGFwektwk")  # Replace with your API key if testing locally

st.title("AI Financial Analysis Agent")
st.write("Upload a financial document (PDF, Excel, Word, or CSV) to get started.")

# === File Upload ===
uploaded_file = st.file_uploader("Upload your financial document", type=["pdf", "xlsx", "xls", "docx", "doc", "csv"])

if uploaded_file is not None:
    file_type = uploaded_file.name.split('.')[-1].lower()
    extracted_text = ""
    df = None  # This will hold tabular data if available

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
            # Convert the DataFrame to CSV text for display and analysis
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
            # Plot the first numeric column against the DataFrame index
            fig, ax = plt.subplots()
            ax.plot(df.index, df[numeric_columns[0]], marker='o')
            ax.set_title(f"Trend of {numeric_columns[0]}")
            ax.set_xlabel("Index")
            ax.set_ylabel(numeric_columns[0])
            st.pyplot(fig)
        else:
            st.info("No numeric columns found in the uploaded table to plot a trend graph.")

    # --- Ask a Financial Question ---
    st.subheader("Ask a Question")
    question = st.text_input("Enter your question about the financial data (e.g., 'What are the key trends in revenue and expenses?')")

    if st.button("Get Analysis"):
        if question.strip() == "":
            st.error("Please enter a question.")
        else:
            # Construct a prompt for the AI. You can tweak this prompt to guide the analysis.
            prompt = (
                f"You are a financial analyst. Given the following financial data extracted from a document:\n\n"
                f"{extracted_text}\n\n"
                f"Answer the following question with a detailed analysis, including any insights or trends you observe:\n"
                f"{question}\n"
            )

            try:
                # Call the OpenAI API (using GPT-3/GPT-4)
                response = openai.Completion.create(
                    engine="text-davinci-003",  # or another model if available
                    prompt=prompt,
                    max_tokens=500,
                    temperature=0.5,
                )
                answer = response.choices[0].text.strip()
                st.subheader("AI Analysis")
                st.write(answer)
            except Exception as e:
                st.error(f"Error communicating with OpenAI API: {e}")
