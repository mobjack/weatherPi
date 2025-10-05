#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv("../conf/weather.conf")

# Initialize client
client = OpenAI()

# Test API call with a simple prompt
try:
    print("Testing OpenAI API connection...")
    result = client.images.generate(
        model="dall-e-3",
        prompt="A simple test image of a sunny day",
        size="1024x1024",
        n=1,
        response_format="b64_json",
    )
    print("✅ API call successful!")
    print(
        f"Generated image data length: {len(result.data[0].b64_json)} characters")

except Exception as e:
    print(f"❌ API Error: {type(e).__name__}: {e}")
    if hasattr(e, 'response'):
        print(f"Response status: {e.response.status_code}")
        print(f"Response text: {e.response.text}")
