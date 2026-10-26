
import faiss
import PyPDF2
import numpy as np
import pickle
import os

from sentence_transformers import SentenceTransformer



# Configuration

PDF_FILE = "data/genai.pdf"
INDEX_FILE = "data/vectors.index"
CHUNKS_FILE = "data/chunks.pkl"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

EMBEDDING_MODEL = "all-MiniLM-L6-v2"



# Load embedding model


print("🔄 Loading embedding model...")

embedding_model = SentenceTransformer(EMBEDDING_MODEL)

print("✅ Embedding model loaded")


# PDF to vectors


def pdf_to_vectors(pdf_path):

    print(f"\n📑 Reading PDF: {pdf_path}")

    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return

    # Read PDF
    with open(pdf_path, "rb") as f:

        pdf_reader = PyPDF2.PdfReader(f)

        total_pages = len(pdf_reader.pages)

        print(f"📚 Total pages: {total_pages}")

        all_chunks = []
        chunk_metadata = []

        # Process each page separately
        for page_num, page in enumerate(pdf_reader.pages):

            page_text = page.extract_text() or ""

            page_text = page_text.strip()

            if not page_text:
                continue

            print(
                f"📄 Processing page "
                f"{page_num + 1}/{total_pages}"
            )

            # Create chunks with overlap
            start = 0

            while start < len(page_text):

                end = start + CHUNK_SIZE

                chunk_text = page_text[start:end].strip()

                if chunk_text:

                    all_chunks.append(chunk_text)

                    chunk_metadata.append({
                        "page_number": page_num + 1
                    })

                # Move forward with overlap
                start += CHUNK_SIZE - CHUNK_OVERLAP

    if not all_chunks:
        print("❌ No text extracted from PDF.")
        return

    print(f"\n✂️ Total chunks created: {len(all_chunks)}")


    # Create embeddings
   

    print("🔀 Creating local embeddings...")

    embeddings = embedding_model.encode(
        all_chunks,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    embeddings = embeddings.astype("float32")

    print(f"📐 Vector shape: {embeddings.shape}")

    
    # Create FAISS index
   

    print("📁 Creating FAISS index...")

    dimension = embeddings.shape[1]

    # Inner product on normalized vectors
    # = cosine similarity
    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)

   
    # Save index and metadata
   

    faiss.write_index(index, INDEX_FILE)

    with open(CHUNKS_FILE, "wb") as f:

        pickle.dump(
            {
                "chunks": all_chunks,
                "metadata": chunk_metadata,
                "total_pages": total_pages
            },
            f
        )

    print("\n✅ Vector database created successfully!")

    print(f"📁 Saved: {INDEX_FILE}")
    print(f"📁 Saved: {CHUNKS_FILE}")

    print(f"📚 Total chunks: {len(all_chunks)}")
    print(f"📐 Embedding dimension: {dimension}")

    return embeddings, all_chunks



if __name__ == "__main__":

    pdf_to_vectors(PDF_FILE)