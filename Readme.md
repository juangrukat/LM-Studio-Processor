# LM Studio File Processor

## Overview
The LM Studio File Processor is a Python application designed to streamline the processing of text files (.md and .txt) using a Language Model (LLM) server. It allows users to configure server settings, select prompts, and process files in a user-friendly graphical interface.

Basically, you can use one prompt to process multiple files. This is useful for generating summaries, translations, or other text-based outputs such as YAML, JSON, or metadata, etc.

![LM Studio Processor](https://github.com/user-attachments/assets/3fbc6e2e-70cb-4438-9399-5b403722241e)


## Features
- **File Processing**: Automatically processes .md and .txt files in a specified folder by sending their content along with a user-defined prompt to an LLM server.
- **User Configuration**: Users can configure server settings, including the server port and file paths, through a simple GUI.
- **Prompt Management**: Users can select prompts from a designated folder, which can be updated dynamically.
- **Progress Tracking**: A progress bar provides real-time feedback on the processing status of files.
- **Error Handling**: The application includes error handling to manage issues during file processing and server communication.

## Requirements
- Python 3.x
- Required Python packages listed in `requirements.txt`


1. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables in a `.env` file or directly in your environment.

## Usage
1. Run the application:
   ```
   python main.py
   ```
2. Configure the server settings and select the prompt folder.
3. Choose the files folder containing the text files you want to process.
4. Select a prompt and click "Start Processing" to begin.

