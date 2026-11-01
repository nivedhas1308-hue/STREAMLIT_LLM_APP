import streamlit as st
from pdf_qa import answer_question
from pypdf import PdfReader
import time
import io
import os
import csv

# Page configuration
st.set_page_config(
    page_title="PDF AI Assistant",
    page_icon="📄",
    layout="wide"
)

# File paths
DATASET_FOLDER = "dataset"
UPLOAD_FOLDER = os.path.join(DATASET_FOLDER, "uploaded_files")
QUERIES_FILE = os.path.join(DATASET_FOLDER, "queries.csv")
ANSWERS_FILE = os.path.join(DATASET_FOLDER, "answers.csv")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Create CSV files with headers if they do not exist
for file_path, header in [
    (QUERIES_FILE, ["query"]),
    (ANSWERS_FILE, ["answer"])
]:
    if not os.path.exists(file_path):
        with open(file_path, "w", newline="", encoding="utf-8") as file:
            csv.writer(file).writerow(header)

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "chunks" not in st.session_state:
    st.session_state.chunks = []

# Application title and logo
st.image("assets/logo.png", width=100)
st.title("PDF AI Assistant")
st.caption("Upload PDFs and ask questions using AI.")

# Sidebar
st.sidebar.title("Upload PDF")

uploaded_files = st.sidebar.file_uploader(
    "Choose PDF files",
    type=["pdf"],
    accept_multiple_files=True
)

# Save uploaded PDFs
if uploaded_files:
    for pdf in uploaded_files:
        file_path = os.path.join(UPLOAD_FOLDER, os.path.basename(pdf.name))

        with open(file_path, "wb") as file:
            file.write(pdf.getvalue())

# Clear chat history
if st.sidebar.button("Clear Chat History"):
    st.session_state.chat_history = []
    st.session_state.chunks = []
    st.rerun()

# Display uploaded documents and allow PDF selection
if uploaded_files:
    st.sidebar.subheader("Uploaded Documents")

    for pdf in uploaded_files:
        st.sidebar.write(f"📄 {pdf.name}")

    selected_pdf = st.selectbox(
        "Select a PDF document",
        uploaded_files,
        format_func=lambda pdf: pdf.name
    )

    try:
        pdf_reader = PdfReader(io.BytesIO(selected_pdf.getvalue()))

        st.success(f"Uploaded: {selected_pdf.name}")
        st.write(f"Total pages: {len(pdf_reader.pages)}")

        question = st.text_input("Enter your question", key="question_input")

        if st.button("Get Answer"):
            if question.strip():
                start_time = time.time()

                with st.spinner("Reading PDF and generating answer..."):
                    answer, chunks = answer_question(selected_pdf, question)

                elapsed = time.time() - start_time

                # Save conversation in Streamlit session
                chat_entry = {
                    "question": question,
                    "answer": answer,
                    "filename": selected_pdf.name,
                    "time": elapsed,
                    "chunks": chunks
                }
                st.session_state.chat_history.append(chat_entry)
                st.session_state.chunks = chunks

                # Save question and answer to CSV files
                with open(QUERIES_FILE, "a", newline="", encoding="utf-8") as file:
                    csv.writer(file).writerow([question])

                with open(ANSWERS_FILE, "a", newline="", encoding="utf-8") as file:
                    csv.writer(file).writerow([answer])

            else:
                st.warning("Please enter a question.")

    except Exception as error:
        st.error(f"Unable to read this PDF: {error}")

else:
    st.info("Upload one or more PDF files from the sidebar to begin.")

# Display answers and retrieved chunks for each conversation
if st.session_state.chat_history:
    st.subheader("Answers and Retrieved Document Chunks")

    for chat in reversed(st.session_state.chat_history):
        st.markdown(f"**PDF:** {chat['filename']}")
        st.markdown(f"**Question:** {chat['question']}")
        st.markdown(f"**Answer:** {chat['answer']}")
        st.caption(f"Response time: {chat['time']:.2f} seconds")

        with st.expander("Retrieved document chunks"):
            for i, chunk in enumerate(chat["chunks"], start=1):
                st.write(f"Chunk {i}")
                st.write(chunk.page_content)
                st.write(f"Page: {chunk.metadata.get('page', 'Unknown')}")
                st.divider()

        st.divider()

# Display conversation history
st.subheader("Conversation History")

if st.session_state.chat_history:
    for chat in st.session_state.chat_history:
        st.write(f"**PDF:** {chat['filename']}")
        st.write(f"**Question:** {chat['question']}")
        st.write(f"**Answer:** {chat['answer']}")
        st.divider()
else:
    st.write("No conversation history yet.")
