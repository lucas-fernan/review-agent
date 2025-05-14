import os
import requests
import re
from pathlib import Path

# Configuration
project_folder = "../car_management"  # Folder to scan for .cs files (relative or absolute path)
API_URL = "https://api.x.ai/v1/chat/completions"
API_TOKEN = "<xai-TOKEN>"  # Replace with your token
headers = {"Authorization": f"Bearer {API_TOKEN}"}

def read_file(file_path):
    """Read content from a file, return empty string if file doesn't exist."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: {file_path} not found.")
        return ""

def read_cs_files(folder):
    """Recursively collect .cs files from folder, return list of (relative_path, content) tuples."""
    files = []
    folder_path = Path(folder)
    if not folder_path.exists():
        print(f"Warning: Folder {folder} does not exist.")
        return files
    
    for file_path in folder_path.rglob("*.*"):
        relative_path = str(file_path.relative_to(folder_path.parent))
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            files.append((relative_path, content))
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    return files

def read_codebase(codebase_text):
    """Parse codebase text into a list of (filename, content) tuples."""
    files = []
    pattern = r'FILENAME:([^\n]+)\n@!([\s\S]*?)!@'
    matches = re.finditer(pattern, codebase_text, re.MULTILINE)
    for match in matches:
        filename = match.group(1).strip()
        content = match.group(2).strip()
        files.append((filename, content))
    return files

def process_api_response(response):
    """Extract text and code files from API response, return (text, files)."""
    text_parts = []
    files = []
    pattern = r'FILENAME:([^\n]+)\n@!([\s\S]*?)!@'
    matches = re.finditer(pattern, response, re.MULTILINE)
    
    last_pos = 0
    for match in matches:
        text_parts.append(response[last_pos:match.start()])
        filename = match.group(1).strip()
        content = match.group(2).strip()
        files.append((filename, content))
        last_pos = match.end()
    
    text_parts.append(response[last_pos:])
    response_text = ''.join(text_parts).strip()
    
    return response_text, files

def save_code_file(filename, content):
    """Save content to a file at the relative path under 'code' folder, creating directories if needed."""
    file_path = Path("code") / filename  # Prepend 'code' to the relative path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Saved code file: {file_path}")

def analyze_code(instruction, requirements, codebase_files):
    """Send codebase to xAI API for analysis."""
    codebase_summary = "\n".join([f"FILENAME: {f}\n@!{c}!@" for f, c in codebase_files])
    prompt = f"{instruction}\n\nRequirements:\n{requirements}\n\nCodebase:\n{codebase_summary}"
    
    payload = {
        "messages": [
            {
                "role": "system",
                "content": "You are a code assistant."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "model": "grok-2-latest",
        "stream": False,
        "temperature": 0
    }
    
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.status_code} - {response.text}"

def main():
    # Read input files
    requirements = read_file("Requirements.txt")
    instruction = read_file("Instructions.txt")
    codebase_text = read_file("codebase.txt")  # Optional codebase input
    
    if not instruction:
        print("Error: Instruction.txt is empty or missing.")
        return
    
    # Parse codebase from text (if provided)
    codebase_files = read_codebase(codebase_text)
    
    # Collect .cs files from project folder
    cs_files = read_cs_files(project_folder)
    if not cs_files:
        print(f"Warning: No .cs files found in {project_folder}.")
    
    # Combine text-based and .cs files
    codebase_files.extend(cs_files)
    
    if not codebase_files:
        print("Error: No code files to analyze (from codebase.txt or .cs files).")
        return
    
    # Analyze code via API
    print("Analyzing codebase...")
    result = analyze_code(instruction, requirements, codebase_files)
    
    # Process API response
    response_text, response_files = process_api_response(result)
    
    # Print and save response text
    print("API Response Text:")
    print(response_text)
    with open("results.txt", 'w', encoding='utf-8') as f:
        f.write(response_text)
    print("Saved response text to results.txt")
    
    # Save any code files from API response
    for filename, content in response_files:
        save_code_file(filename, content)

if __name__ == "__main__":
    main()