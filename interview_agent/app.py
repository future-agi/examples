"""
Interview Agent - Main Application
Gradio interface for the Interview Agent application
"""

import json
import os
import time
import uuid
from datetime import datetime
from pathlib import Path

import gradio as gr
import numpy as np
from fi_instrumentation import FITracer, register
from fi_instrumentation.fi_types import (FiSpanKindValues, ProjectType,
                                         SpanAttributes)
from traceai_openai import OpenAIInstrumentor

from src.multi_interview_analysis import MultiInterviewAnalysisService
from src.question_answering import QuestionAnsweringService
from src.summarization import SummarizationService
from src.transcription import TranscriptionService
from src.vector_storage import VectorStorageService

trace_provider = register(
    project_type=ProjectType.OBSERVE,
    project_name="interview_agent",
)

OpenAIInstrumentor().instrument(tracer_provider=trace_provider)

_futr_tracer = FITracer(trace_provider.get_tracer(__name__))

# Ensure necessary directories exist
os.makedirs("./uploads", exist_ok=True)
os.makedirs("./interviews", exist_ok=True)
os.makedirs("./chroma_db", exist_ok=True)

# Initialize services
transcription_service = TranscriptionService()
summarization_service = SummarizationService()
vector_storage = VectorStorageService(persist_directory="./chroma_db")
qa_service = QuestionAnsweringService(vector_storage)
multi_analysis = MultiInterviewAnalysisService(vector_storage)

# Global state for tracking uploads and processing
state = {
    "current_upload_id": None,
    "current_transcript": None,
    "current_summary": None,
    "interviews": []
}

def refresh_interview_list():
    state["interviews"] = vector_storage.list_interviews()
    return state["interviews"]

def format_interview_choice(interview):
    title = interview.get("title", "Untitled")
    interview_id = interview.get("id", "")
    date = interview.get("date_uploaded", "")
    if date:
        try:
            date_obj = datetime.fromisoformat(date)
            date = date_obj.strftime("%Y-%m-%d %H:%M")
        except:
            pass
    return f"{title} ({date}) [{interview_id}]"

def parse_interview_choice(choice):
    if not choice:
        return None
    start = choice.rfind("[")
    end = choice.rfind("]")
    if start != -1 and end != -1:
        return choice[start+1:end]
    return None

def upload_and_transcribe(audio_file, interview_title):
    with _futr_tracer.start_as_current_span("upload_and_transcribe", fi_span_kind=FiSpanKindValues.CHAIN):
        if not audio_file:
            return None, "Please upload an audio file.", None, None, str(uuid.uuid4())

        # Generate a unique ID for this upload
        upload_id = str(uuid.uuid4())
        state["current_upload_id"] = upload_id

        # Determine file name
        file_name = getattr(audio_file, 'name', str(audio_file))
        file_path = f"./uploads/{upload_id}_{os.path.basename(file_name)}"

        # Save uploaded file robustly
        if hasattr(audio_file, "read"):
            # It's a file-like object
            with open(file_path, "wb") as f:
                f.write(audio_file.read())
        else:
            # It's a path or NamedString, copy the file
            with open(audio_file, "rb") as src, open(file_path, "wb") as dst:
                dst.write(src.read())

        # Default title if not provided
        if not interview_title:
            interview_title = f"Interview {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        try:
            # Transcribe audio
            transcript_result = transcription_service.transcribe_with_progress(file_path)
            transcript_text = transcript_result["text"]
            state["current_transcript"] = transcript_text

            # Generate summary
            summary_result = summarization_service.generate_summary(transcript_text)
            state["current_summary"] = summary_result

            # Store in vector database
            metadata = {
                "title": interview_title,
                "date_uploaded": datetime.now().isoformat(),
                "audio_metadata": {
                    "filename": os.path.basename(file_name),
                    "file_path": file_path
                }
            }

            interview_id = vector_storage.store_interview(
                transcript_text, summary_result, metadata
            )

            # Refresh interview list
            refresh_interview_list()

            # Format summary for display
            formatted_summary = f"# {interview_title}\n\n"
            formatted_summary += f"## Executive Summary\n{summary_result['sections']['executive_summary']}\n\n"
            formatted_summary += f"## Key Topics\n{summary_result['sections']['key_topics']}\n\n"
            formatted_summary += f"## Important Insights\n{summary_result['sections']['important_insights']}\n\n"
            formatted_summary += f"## Notable Quotes\n{summary_result['sections']['notable_quotes']}"

            return interview_id, f"✅ Successfully processed interview: {interview_title}", transcript_text, formatted_summary, str(uuid.uuid4())

        except Exception as e:
            error_msg = f"Error processing audio: {str(e)}"
            return None, error_msg, None, None, str(uuid.uuid4())

def answer_question(interview_choice, question):
    with _futr_tracer.start_as_current_span("answer_question", fi_span_kind=FiSpanKindValues.CHAIN):
        if not interview_choice:
            return "Please select an interview first."
        
        if not question or len(question.strip()) == 0:
            return "Please enter a question."
        
        interview_id = parse_interview_choice(interview_choice)
        if not interview_id:
            return "Invalid interview selection."
        
        try:
            result = qa_service.answer_question(interview_id, question)
            
            # Format answer with context
            answer = f"## Answer\n{result['answer']}\n\n"
            
            if result.get("context"):
                answer += "## Source Context\n"
                for i, context in enumerate(result["context"]):
                    answer += f"### Context {i+1}\n{context[:300]}...\n\n"
            
            return answer
            
        except Exception as e:
            return f"Error: {str(e)}"

def analyze_interviews(interview_choices, analysis_query):
    with _futr_tracer.start_as_current_span("analyze_interviews", fi_span_kind=FiSpanKindValues.CHAIN):
        if not interview_choices or len(interview_choices) == 0:
            return "Please select at least one interview."
        
        if not analysis_query or len(analysis_query.strip()) == 0:
            return "Please enter an analysis query."
        
        # Extract interview IDs
        interview_ids = [parse_interview_choice(choice) for choice in interview_choices]
        interview_ids = [id for id in interview_ids if id]  # Filter out None values
        
        if not interview_ids:
            return "Invalid interview selection."
        
        try:
            result = multi_analysis.analyze_interviews(interview_ids, analysis_query)
            
            # Format analysis
            analysis = f"# Analysis: {analysis_query}\n\n"
            analysis += f"## Interviews Analyzed\n"
            
            for interview in result["interviews"]:
                analysis += f"- {interview['title']}\n"
            
            analysis += f"\n## Analysis Results\n{result['analysis']}"
            
            return analysis
            
        except Exception as e:
            return f"Error: {str(e)}"

def compare_interviews(interview_choices, comparison_aspects):
    with _futr_tracer.start_as_current_span("compare_interviews", fi_span_kind=FiSpanKindValues.CHAIN):
        if not interview_choices or len(interview_choices) < 2:
            return "Please select at least two interviews to compare."
        
        # Extract interview IDs
        interview_ids = [parse_interview_choice(choice) for choice in interview_choices]
        interview_ids = [id for id in interview_ids if id]  # Filter out None values
        
        if len(interview_ids) < 2:
            return "Please select at least two valid interviews to compare."
        
        # Parse comparison aspects
        aspects = []
        if comparison_aspects:
            aspects = [aspect.strip() for aspect in comparison_aspects.split(",") if aspect.strip()]
        
        try:
            result = multi_analysis.compare_interviews(interview_ids, aspects)
            
            # Format comparison
            comparison = f"# Interview Comparison\n\n"
            comparison += f"## Interviews Compared\n"
            
            for interview in result["interviews"]:
                comparison += f"- {interview['title']}\n"
            
            if aspects:
                comparison += f"\n## Aspects Compared\n"
                for aspect in aspects:
                    comparison += f"- {aspect}\n"
            
            comparison += f"\n## Comparison Results\n{result['comparison']}"
            
            return comparison
            
        except Exception as e:
            return f"Error: {str(e)}"

def identify_patterns(interview_choices, min_interviews):
    with _futr_tracer.start_as_current_span("identify_patterns", fi_span_kind=FiSpanKindValues.CHAIN):
        if not interview_choices or len(interview_choices) < 2:
            return "Please select at least two interviews for pattern analysis."
        
        # Extract interview IDs
        interview_ids = [parse_interview_choice(choice) for choice in interview_choices]
        interview_ids = [id for id in interview_ids if id]  # Filter out None values
        
        if len(interview_ids) < 2:
            return "Please select at least two valid interviews for pattern analysis."
        
        # Validate min_interviews
        try:
            min_interviews = int(min_interviews)
            if min_interviews < 1:
                min_interviews = 1
            if min_interviews > len(interview_ids):
                min_interviews = len(interview_ids)
        except:
            min_interviews = 2
        
        try:
            result = multi_analysis.identify_patterns(interview_ids, min_interviews)
            
            # Format patterns
            patterns = f"# Pattern Analysis\n\n"
            patterns += f"## Interviews Analyzed\n"
            
            for interview in result["interviews"]:
                patterns += f"- {interview['title']}\n"
            
            patterns += f"\n## Patterns (appearing in at least {min_interviews} interviews)\n{result['patterns']}"
            
            return patterns
            
        except Exception as e:
            return f"Error: {str(e)}"

def get_interview_insights(interview_choice):
    with _futr_tracer.start_as_current_span("get_interview_insights", fi_span_kind=FiSpanKindValues.CHAIN):
        if not interview_choice:
            return "Please select an interview first."
        
        interview_id = parse_interview_choice(interview_choice)
        if not interview_id:
            return "Invalid interview selection."
        
        try:
            result = qa_service.get_interview_insights(interview_id)
            
            # Format insights
            insights = f"# Insights: {result['interview_title']}\n\n"
            insights += result['insights']
            
            return insights
            
        except Exception as e:
            return f"Error: {str(e)}"

def view_full_transcript(interview_choice):
    with _futr_tracer.start_as_current_span("view_full_transcript", fi_span_kind=FiSpanKindValues.CHAIN):
        if not interview_choice:
            return "Please select an interview first."
        
        interview_id = parse_interview_choice(interview_choice)
        if not interview_id:
            return "Invalid interview selection."
        
        try:
            interview = vector_storage.retrieve_interview(interview_id)
            
            # Format transcript
            transcript = f"# Transcript: {interview['title']}\n\n"
            transcript += interview['transcript']
            
            return transcript
            
        except Exception as e:
            return f"Error: {str(e)}"

def view_full_summary(interview_choice):
    with _futr_tracer.start_as_current_span("view_full_summary", fi_span_kind=FiSpanKindValues.CHAIN):
        if not interview_choice:
            return "Please select an interview first."
        
        interview_id = parse_interview_choice(interview_choice)
        if not interview_id:
            return "Invalid interview selection."
        
        try:
            interview = vector_storage.retrieve_interview(interview_id)
            
            if "summary" not in interview or not interview["summary"]:
                return f"No summary available for: {interview['title']}"
            
            # Format summary
            summary = f"# Summary: {interview['title']}\n\n"
            
            if "sections" in interview["summary"]:
                sections = interview["summary"]["sections"]
                
                if "executive_summary" in sections and sections["executive_summary"]:
                    summary += f"## Executive Summary\n{sections['executive_summary']}\n\n"
                
                if "key_topics" in sections and sections["key_topics"]:
                    summary += f"## Key Topics\n{sections['key_topics']}\n\n"
                
                if "important_insights" in sections and sections["important_insights"]:
                    summary += f"## Important Insights\n{sections['important_insights']}\n\n"
                
                if "notable_quotes" in sections and sections["notable_quotes"]:
                    summary += f"## Notable Quotes\n{sections['notable_quotes']}\n\n"
                
                if "context_and_background" in sections and sections["context_and_background"]:
                    summary += f"## Context and Background\n{sections['context_and_background']}\n\n"
                
                if "conclusion" in sections and sections["conclusion"]:
                    summary += f"## Conclusion\n{sections['conclusion']}"
            else:
                summary += interview["summary"].get("full_summary", "No summary content available.")
            
            return summary
            
        except Exception as e:
            return f"Error: {str(e)}"

def delete_interview(interview_choice):
    with _futr_tracer.start_as_current_span("delete_interview", fi_span_kind=FiSpanKindValues.LLM):
        if not interview_choice:
            return "Please select an interview to delete."
        
        interview_id = parse_interview_choice(interview_choice)
        if not interview_id:
            return "Invalid interview selection."
        
        try:
            # Get interview title before deletion
            interview = vector_storage.retrieve_interview(interview_id)
            interview_title = interview.get("title", f"Interview {interview_id}")
            
            # Delete interview
            success = vector_storage.delete_interview(interview_id)
            
            if success:
                # Refresh interview list
                refresh_interview_list()
                return f"✅ Successfully deleted interview: {interview_title}"
            else:
                return f"Failed to delete interview: {interview_title}"
            
        except Exception as e:
            return f"Error: {str(e)}"

# Initialize interview list
refresh_interview_list()

# Create Gradio interface
with gr.Blocks(title="Interview Agent", theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🎙️ Interview Agent")
    gr.Markdown("Upload interview audio, get transcriptions, summaries, and ask questions about your interviews.")
    
    # Initialize interview choices for dropdowns
    interview_choices = [format_interview_choice(interview) for interview in state["interviews"]]
    
    with gr.Tabs() as tabs:
        # Upload and Transcribe Tab
        with gr.TabItem("Upload & Transcribe"):
            gr.Markdown("## Upload Interview Audio")
            
            with gr.Row():
                with gr.Column():
                    audio_file = gr.File(label="Upload Audio File", file_types=["audio"])
                    interview_title = gr.Textbox(label="Interview Title (optional)")
                    upload_button = gr.Button("Upload and Process", variant="primary")
                
                with gr.Column():
                    interview_id_output = gr.Textbox(label="Interview ID", visible=False)
                    status_output = gr.Textbox(label="Status")
                    dropdown_update_trigger = gr.Textbox(visible=False)
            
            gr.Markdown("## Transcription Result")
            transcript_output = gr.Textbox(label="Transcript", lines=10)
            
            gr.Markdown("## Summary")
            summary_output = gr.Markdown(label="Summary")
        
        # Question Answering Tab
        with gr.TabItem("Question Answering"):
            gr.Markdown("## Ask Questions About an Interview")
            
            interview_dropdown_qa = gr.Dropdown(
                choices=interview_choices,
                label="Select Interview",
                interactive=True
            )
            
            question_input = gr.Textbox(
                label="Your Question",
                placeholder="e.g., What were the main points discussed about climate change?"
            )
            
            ask_button = gr.Button("Ask Question", variant="primary")
            answer_output = gr.Markdown(label="Answer")
            
            with gr.Accordion("View Full Content", open=False):
                with gr.Row():
                    view_transcript_button = gr.Button("View Full Transcript")
                    view_summary_button = gr.Button("View Full Summary")
                    view_insights_button = gr.Button("View Interview Insights")
        
        # Multi-Interview Analysis Tab
        with gr.TabItem("Multi-Interview Analysis"):
            gr.Markdown("## Analyze Multiple Interviews")
            
            with gr.Tabs() as analysis_tabs:
                # Query-based Analysis
                with gr.TabItem("Query Analysis"):
                    interview_dropdown_multi = gr.Dropdown(
                        choices=interview_choices,
                        label="Select Interviews",
                        multiselect=True,
                        interactive=True
                    )
                    
                    analysis_query = gr.Textbox(
                        label="Analysis Query",
                        placeholder="e.g., Compare perspectives on renewable energy"
                    )
                    
                    analyze_button = gr.Button("Analyze Interviews", variant="primary")
                    analysis_output = gr.Markdown(label="Analysis Results")
                
                # Comparison
                with gr.TabItem("Compare Interviews"):
                    interview_dropdown_compare = gr.Dropdown(
                        choices=interview_choices,
                        label="Select Interviews to Compare",
                        multiselect=True,
                        interactive=True
                    )
                    
                    comparison_aspects = gr.Textbox(
                        label="Comparison Aspects (comma-separated, optional)",
                        placeholder="e.g., main topics, opinions, background"
                    )
                    
                    compare_button = gr.Button("Compare Interviews", variant="primary")
                    comparison_output = gr.Markdown(label="Comparison Results")
                
                # Pattern Analysis
                with gr.TabItem("Pattern Analysis"):
                    interview_dropdown_patterns = gr.Dropdown(
                        choices=interview_choices,
                        label="Select Interviews for Pattern Analysis",
                        multiselect=True,
                        interactive=True
                    )
                    
                    min_interviews = gr.Number(
                        label="Minimum Interviews for Pattern",
                        value=2,
                        minimum=1,
                        step=1
                    )
                    
                    patterns_button = gr.Button("Identify Patterns", variant="primary")
                    patterns_output = gr.Markdown(label="Pattern Analysis Results")
        
        # Manage Interviews Tab
        with gr.TabItem("Manage Interviews"):
            gr.Markdown("## Interview Management")
            
            refresh_button = gr.Button("Refresh Interview List")
            
            interview_dropdown_manage = gr.Dropdown(
                choices=interview_choices,
                label="Select Interview",
                interactive=True
            )
            
            with gr.Row():
                view_button = gr.Button("View Details")
                delete_button = gr.Button("Delete Interview", variant="stop")
            
            management_output = gr.Markdown(label="Management Results")
    
    # Set up event handlers
    upload_button.click(
        upload_and_transcribe,
        inputs=[audio_file, interview_title],
        outputs=[interview_id_output, status_output, transcript_output, summary_output, dropdown_update_trigger]
    )
    
    ask_button.click(
        answer_question,
        inputs=[interview_dropdown_qa, question_input],
        outputs=[answer_output]
    )
    
    analyze_button.click(
        analyze_interviews,
        inputs=[interview_dropdown_multi, analysis_query],
        outputs=[analysis_output]
    )
    
    compare_button.click(
        compare_interviews,
        inputs=[interview_dropdown_compare, comparison_aspects],
        outputs=[comparison_output]
    )
    
    patterns_button.click(
        identify_patterns,
        inputs=[interview_dropdown_patterns, min_interviews],
        outputs=[patterns_output]
    )
    
    view_transcript_button.click(
        view_full_transcript,
        inputs=[interview_dropdown_qa],
        outputs=[answer_output]
    )
    
    view_summary_button.click(
        view_full_summary,
        inputs=[interview_dropdown_qa],
        outputs=[answer_output]
    )
    
    view_insights_button.click(
        get_interview_insights,
        inputs=[interview_dropdown_qa],
        outputs=[answer_output]
    )
    
    view_button.click(
        view_full_summary,
        inputs=[interview_dropdown_manage],
        outputs=[management_output]
    )
    
    delete_button.click(
        delete_interview,
        inputs=[interview_dropdown_manage],
        outputs=[management_output]
    )
    
    # Function to update all interview dropdowns
    def update_all_dropdowns():
        refresh_interview_list()
        choices = [format_interview_choice(interview) for interview in state["interviews"]]
        return choices, choices, choices, choices, choices
    
    refresh_button.click(
        update_all_dropdowns,
        inputs=[],
        outputs=[
            interview_dropdown_qa,
            interview_dropdown_multi,
            interview_dropdown_compare,
            interview_dropdown_patterns,
            interview_dropdown_manage
        ]
    )
    
    # Update dropdowns when a new interview is processed
    dropdown_update_trigger.change(
        update_all_dropdowns,
        inputs=[],
        outputs=[
            interview_dropdown_qa,
            interview_dropdown_multi,
            interview_dropdown_compare,
            interview_dropdown_patterns,
            interview_dropdown_manage
        ]
    )

# Launch the app
if __name__ == "__main__":
    app.launch()
