import os
from server import query_llm
from typing import List, Dict, Optional

def process_files(server_url: str, prompt: str, folder: str, progress_bar) -> None:
    files: List[str] = [f for f in os.listdir(folder) if f.endswith(('.md', '.txt'))]
    
    if not files:
        print("No .md or .txt files found in the selected folder.")
        return
    
    for i, file in enumerate(files):
        try:
            file_path = os.path.join(folder, file)
            print(f"Processing {file}...")
            
            # Read the file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Combine the prompt with the content
            full_prompt = f"{prompt}\n\nContent:\n{content}"
            
            # Query the LLM
            response = query_llm(server_url, full_prompt)
            
            # Extract the response text
            llm_response = response['choices'][0]['message']['content']
            
            # Write back to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"LLM Response:\n{llm_response}\n\nOriginal Content:\n{content}")
            
            print(f"Successfully processed {file}")
            
            # Update progress bar
            progress_bar.UpdateBar((i + 1) / len(files) * 100)
            
        except Exception as e:
            print(f"Error processing {file}: {str(e)}")
            continue 