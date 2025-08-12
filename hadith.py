import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
from PyPDF2 import PdfReader
import os
import json
from gtts import gTTS
import tempfile

# Load API key from .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

model = genai.GenerativeModel(model_name="gemini-1.5-flash-8b")

PDF_PATH = "Hadith_collection.pdf"  # apni hadith PDF ka path yahan dein

# Function to read PDF and extract text
def read_pdf(PDF_PATH):
    reader = PdfReader(PDF_PATH)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text.strip()

# Split text into smaller chunks (for retrieval)
def split_text(text, max_words=250):
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words):
        chunk = " ".join(words[i:i+max_words])
        chunks.append(chunk)
    return chunks


def text_to_speech(text, lang="en"):
    tts = gTTS(text=text, lang=lang)
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(tmp_file.name)
    return tmp_file.name
# Simple keyword based retrieval from chunks
def retrieve_chunks(query, chunks):
    query_words = query.lower().split()
    matched_chunks = []
    for chunk in chunks:
        chunk_lower = chunk.lower()
        if any(word in chunk_lower for word in query_words):
            matched_chunks.append(chunk)
    return matched_chunks[:3] if matched_chunks else chunks[:2]

# Generate answer using Gemini
def generate_answer(context, query):
    prompt = f"""
You are an Islamic Hadith assistant. Use the following context (Hadiths) to answer the question.

Context:
{context}

User's Question:
{query}

Answer with relevant Hadith references or explanations.
"""
    response = model.generate_content(prompt)
    return response.text.strip()

@st.cache_resource
def load_knowledge_base():
    raw_text = read_pdf(PDF_PATH)
    return split_text(raw_text)

# Streamlit UI
st.set_page_config(page_title="Islamic Hadith Bot with Translation & Voice", page_icon="🕌")
st.title("🕌 Islamic Hadith Bot")

st.markdown("""
Ask your questions related to Hadith and Islamic teachings.
You can select the language to translate the answer and listen to it in audio.
""")

chunks = load_knowledge_base()

query = st.text_input("Enter your question about Hadith:")


if st.button("Ask"):   
    if not query.strip():
        st.warning("Please enter your question first.")
    else:
        with st.spinner("Searching and generating answer..."):
            relevant_chunks = retrieve_chunks(query, chunks)
            context = "\n\n".join(relevant_chunks)
            answer = generate_answer(context, query)
                                             
            st.subheader("📖 Answer:")
            st.markdown(answer)
            with st.spinner("Loading Audio"):
    # Generate and play TTS audio
                audio_file = text_to_speech(answer)
                audio_bytes = open(audio_file, "rb").read()
                st.audio(audio_bytes, format="audio/mp3")