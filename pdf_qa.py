
from langchain_community.document_loaders import PyPDFLoader
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_classic.chains import RetrievalQA

import tempfile
import os


def answer_question(pdf_file, question):

    # Save uploaded PDF temporarily
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".pdf"
    ) as temp_file:
        temp_file.write(pdf_file.getvalue())
        pdf_path = temp_file.name

    try:
        # Load PDF
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()

        # Split PDF into chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

        chunks = splitter.split_documents(documents)

        if not chunks:
            raise ValueError("The uploaded PDF contains no readable text.")

        # Create embeddings
        embeddings = OllamaEmbeddings(
            model="nomic-embed-text"
        )

        # Store chunks in ChromaDB
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings
        )

        # Retrieve relevant document chunks
        retriever = vectorstore.as_retriever(
            search_kwargs={"k": 3}
        )

        # Load Ollama language model
        llm = ChatOllama(
            model="llama3.2",
            temperature=0
        )

        # Create question-answering chain
        qa = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever
        )

        # Generate answer
        result = qa.invoke({"query": question})

        return result["result"], chunks

    finally:
        # Delete temporary PDF
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

