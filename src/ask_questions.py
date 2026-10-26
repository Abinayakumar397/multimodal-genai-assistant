import os
import pickle

import faiss

from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer


# ============================================================
# 1. Load environment variables
# ============================================================

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    raise ValueError(
        "GROQ_API_KEY not found in .env file"
    )


# ============================================================
# 2. Groq client
# ============================================================

client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.groq.com/openai/v1"
)


# ============================================================
# 3. Configuration
# ============================================================

INDEX_FILE = "data/vectors.index"
CHUNKS_FILE = "data/chunks.pkl"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

CHAT_MODEL = "openai/gpt-oss-120b"


# ============================================================
# 4. Load embedding model
# ============================================================

print("🔄 Loading embedding model...")

embedding_model = SentenceTransformer(EMBEDDING_MODEL)

print("✅ Embedding model loaded")


# ============================================================
# 5. Load FAISS database
# ============================================================

if not os.path.exists(INDEX_FILE):
    raise FileNotFoundError(
        "vectors.index not found. "
        "Run pdf_to_vectors.py first."
    )

if not os.path.exists(CHUNKS_FILE):
    raise FileNotFoundError(
        "chunks.pkl not found. "
        "Run pdf_to_vectors.py first."
    )


print("🔄 Loading FAISS database...")

index = faiss.read_index(INDEX_FILE)

with open(CHUNKS_FILE, "rb") as f:
    data = pickle.load(f)


chunks = data["chunks"]
metadata = data["metadata"]
total_pages = data["total_pages"]


print("✅ Database loaded successfully!")
print(f"📚 Total pages: {total_pages}")
print(f"✂️ Total chunks: {len(chunks)}")


# ============================================================
# 6. Ask questions
# ============================================================

def ask_questions(question, top_k=3):

    # --------------------------------------------------------
    # Create embedding for user's question
    # --------------------------------------------------------

    query_vector = embedding_model.encode(
        [question],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    query_vector = query_vector.astype("float32")


    # --------------------------------------------------------
    # Search FAISS
    # --------------------------------------------------------

    scores, indices = index.search(
        query_vector,
        top_k
    )


    print("\n🔍 Relevant chunks found:")

    context_parts = []


    # --------------------------------------------------------
    # Get retrieved chunks
    # --------------------------------------------------------

    for rank, (score, idx) in enumerate(
        zip(scores[0], indices[0])
    ):

        # FAISS can return -1 if no result exists

        if idx == -1:
            continue


        page_num = metadata[idx]["page_number"]

        print(
            f"Chunk {rank + 1}: "
            f"Score = {score:.3f}, "
            f"Page = {page_num}"
        )


        chunk_text = chunks[idx]


        context_parts.append(
            f"[Page {page_num}]\n{chunk_text}"
        )


    # --------------------------------------------------------
    # Check whether anything was retrieved
    # --------------------------------------------------------

    if not context_parts:
        return "No relevant information found."


    # Combine retrieved chunks

    context = "\n\n".join(context_parts)


    # --------------------------------------------------------
    # Send retrieved context to Groq
    # --------------------------------------------------------

    print("\n🤖 Generating answer...")


    response = client.chat.completions.create(

        model=CHAT_MODEL,

        messages=[

            {
                "role": "system",

                "content": (
                    "You are a helpful PDF question-answering assistant. "
                    "Answer only using the provided context. "
                    "If the answer is not present in the context, "
                    "say: I could not find this information in the PDF. "
                    "Do not invent facts. "
                    "Mention the page number when possible."
                )
            },

            {
                "role": "user",

                "content": (
                    f"PDF has {total_pages} pages.\n\n"
                    f"Context:\n{context}\n\n"
                    f"Question: {question}\n\n"
                    "Answer:"
                )
            }

        ],

        temperature=0.2
    )


    # Get generated answer

    answer = response.choices[0].message.content

    return answer


# ============================================================
# 7. Interactive chat loop
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 60)

    print("🚀 PDF RAG CHATBOT READY!")

    print("💡 Ask questions about your PDF")

    print("💡 Type 'exit', 'quit', or 'q' to stop")

    print("=" * 60)


    while True:

        question = input("\nYou: ").strip()


        # Exit

        if question.lower() in [
            "exit",
            "quit",
            "q",
            "bye"
        ]:

            print("👋 Goodbye!")

            break


        # Empty question

        if not question:

            print("Please enter a question.")

            continue


        # Ask question

        try:

            answer = ask_questions(question)

            print("\n🤖 Answer:")

            print(answer)


        except Exception as e:

            print(f"\n❌ Error: {e}")