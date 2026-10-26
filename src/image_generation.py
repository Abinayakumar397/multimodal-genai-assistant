
import os
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://aihorde.net/api/v2"
API_KEY = os.getenv("AI_HORDE_API_KEY", "0000000000")


def generate_image(prompt):
    headers = {
        "apikey": API_KEY,
        "Content-Type": "application/json",
        "Client-Agent": "MultimodalGenAIAssistant:1.0"
    }

    payload = {
        "prompt": prompt,
        "params": {
            "width": 512,
            "height": 512,
            "steps": 20,
            "n": 1
        },
        "models": ["Deliberate"]
    }

    print("\nSubmitting image generation request...")

    try:
        response = requests.post(
            f"{API_URL}/generate/async",
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        job_id = response.json()["id"]

        print(f"Request submitted. Job ID: {job_id}")
        print("Waiting for image generation...")

        while True:
            status_response = requests.get(
                f"{API_URL}/generate/check/{job_id}",
                headers=headers,
                timeout=30
            )
            status_response.raise_for_status()
            status = status_response.json()

            if status.get("faulted"):
                print("Image generation failed. Please try again.")
                return

            if status.get("done"):
                break

            print("Still generating...")
            time.sleep(5)

        result_response = requests.get(
            f"{API_URL}/generate/status/{job_id}",
            headers=headers,
            timeout=30
        )
        result_response.raise_for_status()
        generations = result_response.json().get("generations", [])

        if not generations:
            print("No image was returned. Try another prompt later.")
            return

        image_url = generations[0].get("img")
        if not image_url:
            print("The API did not return an image URL.")
            return

        image_response = requests.get(image_url, timeout=60)
        image_response.raise_for_status()

        output_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "generated_images"
        )
        os.makedirs(output_dir, exist_ok=True)

        filename = f"generated_image_{datetime.now():%Y%m%d_%H%M%S}.png"
        output_path = os.path.join(output_dir, filename)

        with open(output_path, "wb") as file:
            file.write(image_response.content)

        print(f"\nImage saved successfully!\nLocation: {output_path}")

    except requests.RequestException as error:
        print(f"API/network error: {error}")
    except (KeyError, ValueError) as error:
        print(f"Unexpected API response: {error}")


if __name__ == "__main__":
    prompt = input("Enter your image prompt: ").strip()

    if prompt:
        generate_image(prompt)
    else:
        print("Please enter a prompt.")
