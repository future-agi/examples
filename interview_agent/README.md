# Interview Agent - User Guide

## Overview

The Interview Agent is a powerful application that allows you to:

1. Upload audio interviews and automatically transcribe them to text
2. Generate comprehensive summaries of interviews
3. Store interviews in a searchable vector database
4. Ask questions about specific interviews
5. Analyze and compare multiple interviews
6. Identify patterns across your interview collection

This application uses OpenAI's advanced AI models for transcription, summarization, and question answering, combined with ChromaDB for efficient vector storage and retrieval.

## Requirements

- Python 3.9+
- OpenAI API key
- Internet connection

## Installation

1. Clone or download the repository
2. Install the required dependencies:

```bash
pip install openai chromadb gradio pydub tqdm
```

3. Set your OpenAI API key as an environment variable:

```bash
export OPENAI_API_KEY=your_api_key_here
```

## Running the Application

From the project directory, run:

```bash
python main.py
```

This will start the Gradio web interface, which you can access in your browser.

## Features

### Upload & Transcribe

- Upload audio files in common formats (MP3, WAV, M4A, etc.)
- Automatically transcribe audio to text using OpenAI's Whisper model
- Generate comprehensive summaries with key topics, insights, and quotes
- Store interviews in a searchable vector database

### Question Answering

- Select any stored interview
- Ask specific questions about the interview content
- Get AI-generated answers based on the relevant context
- View the full transcript, summary, or insights for any interview

### Multi-Interview Analysis

- **Query Analysis**: Ask questions that span multiple interviews
- **Compare Interviews**: Compare interviews across specific aspects
- **Pattern Analysis**: Identify common themes and patterns across interviews

### Interview Management

- View a list of all stored interviews
- Access full details of any interview
- Delete interviews when no longer needed

## Usage Tips

1. **Audio Quality**: Better audio quality leads to better transcription results
2. **Specific Questions**: For question answering, be specific to get the most accurate answers
3. **Multiple Interviews**: When analyzing multiple interviews, select interviews on related topics for best results
4. **Comparison Aspects**: When comparing interviews, specify aspects like "main topics," "opinions," or "background" for more focused comparisons

## File Structure

```
interview_agent/
├── app.py              # Main Gradio application
├── main.py             # Entry point script
├── src/                # Source code modules
│   ├── transcription.py           # Audio transcription
│   ├── summarization.py           # Interview summarization
│   ├── vector_storage.py          # Vector database storage
│   ├── question_answering.py      # Single interview QA
│   └── multi_interview_analysis.py # Multi-interview analysis
├── uploads/            # Uploaded audio files
├── interviews/         # Stored interview documents
└── chroma_db/          # Vector database files
```

## Troubleshooting

- **API Key Issues**: Ensure your OpenAI API key is correctly set as an environment variable
- **Audio Format Problems**: If transcription fails, try converting your audio to MP3 format
- **Memory Issues**: For very long interviews, the application may require more memory

## Privacy & Data Storage

- All data is stored locally on your machine
- Audio files are saved in the `uploads` directory
- Transcripts and summaries are stored in the `interviews` directory
- Vector embeddings are stored in the `chroma_db` directory

## License

This project is licensed under the MIT License - see the LICENSE file for details.
