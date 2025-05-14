import os
import requests
from pathlib import Path

# Folder with the project code files
project_folder = "/Users/lucas/dev/ai/Code agent"

# # Hugging Face API setup
# API_URL = "https://api-inference.huggingface.co/models/codellama/CodeLlama-13b-hf"
# API_TOKEN = "your_hf_api_token"  # Get from huggingface.co/settings/tokens
# headers = {"Authorization": f"Bearer {API_TOKEN}"}

# xAI API setup
API_URL = "https://api.x.ai/v1/chat/completions"
API_TOKEN = "<xai-TOKEN_STRING>"  # Get from huggingface.co/settings/tokens
headers = {"Authorization": f"Bearer {API_TOKEN}"}

# Prompt template
PROMPT = "Analyze this Python code for errors, issues, or improvements:\n\n{}"

def read_files(folder):
    files_content = {}
    for file_path in Path(folder).rglob("*.py"): 
        with open(file_path, "r", encoding="utf-8") as f:
            files_content[file_path.name] = f.read()
    return files_content

def analyze_code(code):
    payload = {
        "messages": [
        {
        "role": "system",
        "content": "You are a code assistant."
        },
        {
        "role": "user",
        "content": PROMPT.format(code)
        }
    ],
        
        "model": "grok-2-latest",
        "stream": False,
        "temperature": 0
    }
    response = requests.post(API_URL, headers=headers, json=payload)
    # print(f"Payload:  {payload}")
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.status_code} - {response.text}"

# Main execution
if __name__ == "__main__":
    files = read_files(project_folder)
    for filename, content in files.items():
        print(f"Analyzing {filename}...")
        result = analyze_code(content)
        print(f"Feedback for {filename}:\n{result}\n{'-'*50}")