import PySimpleGUI as sg
from config import load_settings, save_settings
from server import query_llm
import os
import time

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

def write_processed_content(file_path: str, llm_response: str, original_content: str) -> None:
    """Write processed content to file in a consistent format."""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f"{llm_response}\n\n{original_content}")

def process_files(server_url, prompt, folder, progress_bar, recursive=False, window=None, timeout=60) -> bool:
    """Process files with optional recursive search. Returns True if completed, False if cancelled."""
    files = get_files_recursive(folder, recursive)
    
    if not files:
        print("No .md or .txt files found in the selected folder.")
        return True
    
    total_files = len(files)
    print(f"\nStarting to process {total_files} files...")
    
    for i, file_path in enumerate(files):
        # Check for stop at the start of each file
        if window:
            event, values = window.read(timeout=1)
            if event == "Stop" or event == sg.WIN_CLOSED:
                print(f"\nProcessing cancelled by user after completing {i} of {total_files} files.")
                progress_bar.UpdateBar(0)
                return False
        
        try:
            print(f"\nProcessing {os.path.basename(file_path)} ({i+1}/{total_files})...")
            
            # Read the file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Combine the prompt with the content
            full_prompt = f"{prompt}\n\nContent:\n{content}"
            
            # Query the LLM with timeout
            try:
                print(f"Sending request to LLM (timeout: {timeout}s)...")
                response = query_llm(server_url, full_prompt, timeout=timeout)
            except Exception as e:
                print(f"Error querying LLM: {str(e)}")
                if "timeout" in str(e).lower():
                    # Ask user if they want to continue with a longer timeout
                    if sg.popup_yes_no("Timeout Error", 
                                     "The server is taking too long to respond.\n\n"
                                     "Would you like to retry with a longer timeout?",
                                     "Yes - Try Again", "No - Skip File") == "Yes - Try Again":
                        try:
                            print(f"Retrying with {timeout * 2}s timeout...")
                            response = query_llm(server_url, full_prompt, timeout=timeout * 2)
                        except Exception as retry_error:
                            print(f"Error on retry: {str(retry_error)}")
                            continue
                    else:
                        continue
                else:
                    continue

            # Extract just the content from the response
            llm_response = response['choices'][0]['message']['content']
            
            # Write back to file using consistent format
            write_processed_content(file_path, llm_response, content)
            
            print(f"Successfully processed {os.path.basename(file_path)}")
            
            # Update progress bar
            progress_bar.UpdateBar((i + 1) / total_files * 100)
            window.refresh()
            
            # Add delay between files
            if i < total_files - 1:  # Don't delay after the last file
                print("\nWaiting 5 seconds before next file...")
                for _ in range(5):
                    if window:
                        event, values = window.read(timeout=1000)  # Check for stop during delay
                        if event == "Stop" or event == sg.WIN_CLOSED:
                            print(f"\nProcessing cancelled by user after completing {i+1} of {total_files} files.")
                            progress_bar.UpdateBar(0)
                            return False
                    time.sleep(1)  # Sleep in 1-second increments while checking for stop
            
        except Exception as e:
            print(f"Error processing {os.path.basename(file_path)}: {str(e)}")
            continue
    
    return True

def test_server_connection(server_url: str) -> bool:
    """Test if the LLM server is responding correctly."""
    try:
        test_prompt = "Respond with 'ok' if you can read this message."
        response = query_llm(server_url, test_prompt)
        # Check if we got a valid response
        if response and 'choices' in response and len(response['choices']) > 0:
            print("Server connection successful!")
            return True
    except Exception as e:
        print(f"Server connection failed: {str(e)}")
        return False

def create_window():
    settings = load_settings()
    
    # Validate stored paths exist, clear if they don't
    if settings.get("prompt_folder") and not os.path.exists(settings.get("prompt_folder")):
        settings["prompt_folder"] = ""
    if settings.get("files_folder") and not os.path.exists(settings.get("files_folder")):
        settings["files_folder"] = ""
    save_settings(settings)
    
    layout = [
        [sg.Text("LM Studio Server Configuration")],
        [sg.Text("Server Port:"), sg.Input(settings.get("server_port", "1234"), key="server_port", size=(10, 1)),
         sg.Text("Timeout (s):"), sg.Input(settings.get("timeout", "60"), key="timeout", size=(10, 1)),
         sg.Button("Test Connection")],
        [sg.Checkbox("Log Prompts", default=settings.get("log_prompts", True), key="log_prompts")],
        [sg.Text("Prompt Folder:"), 
         sg.Input(settings.get("prompt_folder", ""), key="prompt_folder", enable_events=True), 
         sg.FolderBrowse(target="prompt_folder")],
        [sg.Text("Files Folder:"), 
         sg.Input(settings.get("files_folder", ""), key="files_folder", enable_events=True), 
         sg.FolderBrowse(target="files_folder")],
        [sg.Checkbox("Search Subfolders", default=settings.get("recursive_search", False), key="recursive_search")],
        [sg.Text("Selected Prompt:"), 
         sg.Combo([], key="selected_prompt", size=(40, 1), default_value=settings.get("selected_prompt", ""))],
        [sg.Button("Save Settings"), sg.Button("Refresh Prompts"), 
         sg.Button("Start Processing"), sg.Button("Stop", button_color=("white", "red"), disabled=True)],
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
    processing = False
    stop_requested = False

    while True:
        event, values = window.read(timeout=100)  # Add timeout to make the window more responsive

        if event == sg.WIN_CLOSED:
            break

        elif event == "Test Connection":
            server_url = f"http://localhost:{values['server_port']}"
            if test_server_connection(server_url):
                sg.popup("Success", "Server is responding correctly!")
            else:
                sg.popup_error("Error", "Could not connect to LLM server.\nMake sure LM Studio is running and the port is correct.")

        elif event == "FolderBrowse":  # Handle folder selection events
            if values["prompt_folder"]:
                settings = load_settings()
                settings["prompt_folder"] = values["prompt_folder"]
                save_settings(settings)
                update_prompt_list(window, values["prompt_folder"])
            
            if values["files_folder"]:
                settings = load_settings()
                settings["files_folder"] = values["files_folder"]
                save_settings(settings)

        elif event == "Save Settings":
            # Validate paths before saving
            prompt_folder = values["prompt_folder"]
            files_folder = values["files_folder"]
            
            if prompt_folder and not os.path.exists(prompt_folder):
                sg.popup_error("Error", "Prompt folder path does not exist!")
                continue
                
            if files_folder and not os.path.exists(files_folder):
                sg.popup_error("Error", "Files folder path does not exist!")
                continue
            
            settings = {
                "server_port": values["server_port"],
                "log_prompts": values["log_prompts"],
                "prompt_folder": prompt_folder,
                "files_folder": files_folder,
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
                if values["selected_prompt"] not in prompts:
                    window["selected_prompt"].update(value="")
                    settings = load_settings()
                    settings["selected_prompt"] = ""
                    save_settings(settings)

        elif event == "Start Processing" and not processing:
            if not values["selected_prompt"]:
                sg.popup("Please select a prompt first!")
                continue
                
            if not values["files_folder"]:
                sg.popup("Please select a files folder first!")
                continue

            # Test connection before starting
            server_url = f"http://localhost:{values['server_port']}"
            if not test_server_connection(server_url):
                sg.popup_error("Error", "Could not connect to LLM server.\nMake sure LM Studio is running and the port is correct.")
                continue

            # Update button states
            window["Start Processing"].update(disabled=True)
            window["Stop"].update(disabled=False)
            window["Save Settings"].update(disabled=True)
            window["Refresh Prompts"].update(disabled=True)
            window["Test Connection"].update(disabled=True)
            window.refresh()
            
            processing = True
            stop_requested = False
            
            # Save the current settings before processing
            settings = load_settings()
            settings["selected_prompt"] = values["selected_prompt"]
            settings["recursive_search"] = values["recursive_search"]
            save_settings(settings)
            
            # Read the selected prompt
            prompt_path = os.path.join(values["prompt_folder"], values["selected_prompt"])
            try:
                with open(prompt_path, 'r') as f:
                    prompt = f.read()
            except Exception as e:
                sg.popup_error(f"Error reading prompt file: {str(e)}")
                continue
            
            try:
                timeout = int(values["timeout"])
                if timeout < 10:
                    sg.popup_error("Error", "Timeout must be at least 10 seconds!")
                    continue
            except ValueError:
                sg.popup_error("Error", "Timeout must be a number!")
                continue

            try:
                completed = process_files(server_url, prompt, values["files_folder"], 
                                       progress_bar, values["recursive_search"], 
                                       window, timeout=timeout)
                if completed:
                    sg.popup("Processing complete!")
                else:
                    print("Processing was cancelled.")
            except Exception as e:
                sg.popup_error(f"Error during processing: {str(e)}")
            finally:
                # Reset button states
                window["Start Processing"].update(disabled=False)
                window["Stop"].update(disabled=True)
                window["Save Settings"].update(disabled=False)
                window["Refresh Prompts"].update(disabled=False)
                window["Test Connection"].update(disabled=False)
                progress_bar.UpdateBar(0)
                window.refresh()
                processing = False
                stop_requested = False

        elif event == "Stop" and processing:
            print("\nStop requested - processing will stop after current file completes...")
            stop_requested = True
            window["Stop"].update(disabled=True)  # Prevent multiple stop requests
            window.refresh()

    window.close()

if __name__ == "__main__":
    main()
