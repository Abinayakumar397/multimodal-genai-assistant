import os
import re

from dotenv import load_dotenv
from openai import OpenAI
from youtube_transcript_api import YouTubeTranscriptApi


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

CHAT_MODEL = "openai/gpt-oss-20b"

CHUNK_SIZE = 12000


# ============================================================
# 4. Extract YouTube video ID
# ============================================================

def extract_video_id(url):

    patterns = [

        r"(?:youtube\.com/watch\?v=)([^&?/]+)",

        r"(?:youtu\.be/)([^&?/]+)",

        r"(?:youtube\.com/embed/)([^&?/]+)",

        r"(?:youtube\.com/live/)([^&?/]+)"

    ]

    for pattern in patterns:

        match = re.search(pattern, url)

        if match:
            return match.group(1)

    raise ValueError(
        "Invalid YouTube URL."
    )


# ============================================================
# 5. Get YouTube transcript
# ============================================================

def get_transcript(video_id):

    print("\n📝 Getting YouTube transcript...")

    youtube_api = YouTubeTranscriptApi()

    transcript = youtube_api.fetch(
        video_id,
        languages=["en"]
    )

    # Convert transcript snippets to plain text

    text_parts = []

    for snippet in transcript:

        text_parts.append(
            snippet.text
        )

    full_text = " ".join(text_parts)

    if not full_text.strip():

        raise ValueError(
            "No transcript found for this video."
        )

    print(
        f"✅ Transcript retrieved "
        f"({len(full_text)} characters)"
    )

    return full_text


# ============================================================
# 6. Split transcript into chunks
# ============================================================

def split_text(text, chunk_size=CHUNK_SIZE):

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end]

        chunks.append(chunk)

        start = end

    return chunks


# ============================================================
# 7. Summarize one transcript chunk
# ============================================================

def summarize_chunk(chunk, chunk_number, total_chunks):

    print(
        f"🤖 Summarizing chunk "
        f"{chunk_number}/{total_chunks}..."
    )

    response = client.chat.completions.create(

        model=CHAT_MODEL,

        messages=[

            {
                "role": "system",

                "content": (
                    "You are a YouTube video summarization assistant. "
                    "Summarize the provided transcript accurately. "
                    "Identify the main topics, important explanations, "
                    "examples, and key points. "
                    "Do not invent information."
                )
            },

            {
                "role": "user",

                "content": (
                    "Summarize the following section of a YouTube "
                    "video transcript.\n\n"
                    f"Transcript section:\n{chunk}"
                )
            }

        ],

        temperature=0.2
    )

    return response.choices[0].message.content


# ============================================================
# 8. Create final summary
# ============================================================

def create_final_summary(partial_summaries):

    print("\n🧠 Creating final video summary...")

    combined_summary = "\n\n".join(
        partial_summaries
    )

    response = client.chat.completions.create(

        model=CHAT_MODEL,

        messages=[

            {
                "role": "system",

                "content": (
                    "You are an expert video summarization assistant. "
                    "Create a clear final summary from the provided "
                    "partial summaries. "
                    "Do not add information that is not present. "
                    "Organize the answer with useful headings."
                )
            },

            {
                "role": "user",

                "content": (
                    "Create the final summary of the YouTube video "
                    "using these partial summaries.\n\n"
                    f"{combined_summary}\n\n"
                    "Give the answer in this format:\n\n"
                    "1. Main Topic\n"
                    "2. Key Points\n"
                    "3. Important Concepts\n"
                    "4. Examples Mentioned\n"
                    "5. Short Overall Summary"
                )
            }

        ],

        temperature=0.2
    )

    return response.choices[0].message.content


# ============================================================
# 9. Complete YouTube summarization
# ============================================================

def summarize_youtube_video(youtube_url):

    # --------------------------------------------------------
    # Extract video ID
    # --------------------------------------------------------

    video_id = extract_video_id(
        youtube_url
    )

    print(
        f"\n🎥 YouTube Video ID: {video_id}"
    )

    # --------------------------------------------------------
    # Get transcript
    # --------------------------------------------------------

    transcript = get_transcript(
        video_id
    )

    # --------------------------------------------------------
    # Split transcript
    # --------------------------------------------------------

    chunks = split_text(
        transcript
    )

    print(
        f"✂️ Transcript split into "
        f"{len(chunks)} chunks"
    )

    # --------------------------------------------------------
    # Summarize chunks
    # --------------------------------------------------------

    partial_summaries = []

    for i, chunk in enumerate(chunks):

        summary = summarize_chunk(
            chunk,
            i + 1,
            len(chunks)
        )

        partial_summaries.append(
            summary
        )

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    final_summary = create_final_summary(
        partial_summaries
    )

    return final_summary


# ============================================================
# 10. Main program
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 60)

    print(
        "🎥 YOUTUBE VIDEO SUMMARIZER"
    )

    print("=" * 60)

    youtube_url = input(
        "\nEnter YouTube URL: "
    ).strip()

    try:

        summary = summarize_youtube_video(
            youtube_url
        )

        print("\n" + "=" * 60)

        print(
            "🤖 YOUTUBE VIDEO SUMMARY"
        )

        print("=" * 60)

        print(summary)

    except Exception as e:

        print("\n❌ Error:")

        print(e)