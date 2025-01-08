import PySimpleGUI as sg
from config import load_settings, save_settings
from server import query_llm
import os

def get_files_recursive(folder, recursive=False):
    """Get all .md and .txt files from folder and optionally its subfolders."""
    files = []
    if recursive:
        # Walk through all subdirectories
        for root, _, filenames in os.walk(folder):
            for filename in filenames:
                if filename.endswith(('.md', '.txt')):
                    # Store full path for processing
                    files.append(os.path.join(root, filename))
    else:
        # Original behavior - only current directory
        files = [os.path.join(folder, f) for f in os.listdir(folder) 
                if f.endswith(('.md', '.txt'))]
    return files

def process_files(server_url, prompt, folder, progress_bar, recursive=False):
    """Process files with optional recursive search."""
    files = get_files_recursive(folder, recursive)
    
    if not files:
        print("No .md or .txt files found in the selected folder.")
        return
    
    for i, file_path in enumerate(files):
        try:
            print(f"Processing {os.path.basename(file_path)}...")
            
            # Read the file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Combine the prompt with the content
            full_prompt = f"{prompt}\n\nContent:\n{content}"
            
            # Query the LLM
            response = query_llm(server_url, full_prompt)
            
            # Extract just the content from the response
            llm_response = response['choices'][0]['message']['content']
            
            # Write back to the file with simpler format
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"{llm_response}\n\n{content}")
            
            print(f"Successfully processed {os.path.basename(file_path)}")
            
            # Update progress bar
            progress_bar.UpdateBar((i + 1) / len(files) * 100)
            
        except Exception as e:
            print(f"Error processing {os.path.basename(file_path)}: {str(e)}")
            continue

def create_window():
    settings = load_settings()
    
    layout = [
        [sg.Text("LM Studio Server Configuration")],
        [sg.Text("Server Port:"), sg.Input(settings.get("server_port", "1234"), key="server_port", size=(10, 1))],
        [sg.Checkbox("Log Prompts", default=settings.get("log_prompts", True), key="log_prompts")],
        [sg.Text("Prompt Folder:"), 
         sg.Input(settings.get("prompt_folder", ""), key="prompt_folder"), 
         sg.FolderBrowse()],
        [sg.Text("Files Folder:"), 
         sg.Input(settings.get("files_folder", ""), key="files_folder"), 
         sg.FolderBrowse()],
        [sg.Checkbox("Search Subfolders", default=settings.get("recursive_search", False), key="recursive_search")],
        [sg.Text("Selected Prompt:"), 
         sg.Combo([], key="selected_prompt", size=(40, 1), default_value=settings.get("selected_prompt", ""))],
        [sg.Button("Save Settings"), sg.Button("Refresh Prompts"), sg.Button("Start Processing")],
        [sg.ProgressBar(100, orientation='h', size=(40, 20), key='progress_bar')],
        [sg.Output(size=(80, 20))],
    ]

    window = sg.Window("LM Studio File Processor", layout, finalize=True)
    
    # Initialize prompts list if prompt folder exists
    if settings.get("prompt_folder") and os.path.exists(settings.get("prompt_folder")):
        prompts = update_prompt_list(window, settings.get("prompt_folder"))
        # If saved prompt doesn't exist in current folder, clear it
        if settings.get("selected_prompt") not in prompts:
            settings["selected_prompt"] = ""
            save_settings(settings)
    
    return window

def update_prompt_list(window, prompt_folder):
    if not prompt_folder or not os.path.exists(prompt_folder):
        return []
    
    prompts = [f for f in os.listdir(prompt_folder) if f.endswith(('.md', '.txt'))]
    window['selected_prompt'].update(values=prompts)
    return prompts

def main():
    window = create_window()
    progress_bar = window['progress_bar']

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            break

        if event == "Save Settings":
            settings = {
                "server_port": values["server_port"],
                "log_prompts": values["log_prompts"],
                "prompt_folder": values["prompt_folder"],
                "files_folder": values["files_folder"],
                "selected_prompt": values["selected_prompt"],
                "recursive_search": values["recursive_search"]
            }
            save_settings(settings)
            sg.popup("Settings saved successfully!")

        elif event == "Refresh Prompts":
            prompts = update_prompt_list(window, values["prompt_folder"])
            if not prompts:
                sg.popup("No prompt files found in the selected folder!")
            else:
                # If current selection is not in new prompt list, clear it
                if values["selected_prompt"] not in prompts:
                    window["selected_prompt"].update(value="")
                    settings = load_settings()
                    settings["selected_prompt"] = ""
                    save_settings(settings)

        elif event == "Start Processing":
            if not values["selected_prompt"]:
                sg.popup("Please select a prompt first!")
                continue
                
            if not values["files_folder"]:
                sg.popup("Please select a files folder first!")
                continue

            server_url = f"http://localhost:{values['server_port']}"
            
            # Save the current settings before processing
            settings = load_settings()
            settings["selected_prompt"] = values["selected_prompt"]
            settings["recursive_search"] = values["recursive_search"]
            save_settings(settings)
            
            # Read the selected prompt
            prompt_path = os.path.join(values["prompt_folder"], values["selected_prompt"])
            with open(prompt_path, 'r') as f:
                prompt = f.read()

            try:
                process_files(server_url, prompt, values["files_folder"], 
                            progress_bar, values["recursive_search"])
                sg.popup("Processing complete!")
            except Exception as e:
                sg.popup_error(f"Error during processing: {str(e)}")

    window.close()

if __name__ == "__main__":
    main()
