from fi_instrumentation.fi_types import EvalName, EvalTag, EvalTagType, EvalSpanKind

eval_tags = [
    # Evaluate LLM function calling for emotion and occasion recognition
    EvalTag(
        eval_name=EvalName.EVALUATE_LLM_FUNCTION_CALLING,
        value=EvalSpanKind.LLM,
        type=EvalTagType.OBSERVATION_SPAN,
        config={},
        mapping={
            'input': 'llm.input_messages.0.message.content',
            'output': 'llm.output_messages.0.message.tool_calls.0.tool_call.function.name',
        },
        custom_eval_name="LLM Function Call Accuracy",
    ),
    
    # Evaluate response helpfulness and relevance
    EvalTag(
        eval_name=EvalName.DETERMINISTIC_EVALS,
        type=EvalTagType.OBSERVATION_SPAN,
        value=EvalSpanKind.AGENT,
        config={
            "rule_prompt": "Check if the font suggestions provided ({{output.value}}) are appropriate for the user's stated purpose ({{input.value}})",
            "choices": ["Yes", "No"],
            "multi_choice": False
        },
        mapping={},
        custom_eval_name="Font Suggestion Relevance",
    ),

    # Evaluation of emotion recognition accuracy
    EvalTag(
        eval_name=EvalName.DETERMINISTIC_EVALS,
        type=EvalTagType.OBSERVATION_SPAN,
        value=EvalSpanKind.LLM,
        config={
            "rule_prompt": "Check if the emotions and occasions detected ({{output.value}}) are relevant to the user's stated purpose ({{input.value}})",
            "choices": ["Relevant", "Not Relevant", "Partially Relevant"],
            "multi_choice": False
        },
        mapping={},
        custom_eval_name="Emotion/Occasion Recognition Accuracy",
    ),
    
    # Completeness of the font suggestions
    EvalTag(
        eval_name=EvalName.COMPLETENESS,
        type=EvalTagType.OBSERVATION_SPAN,
        value=EvalSpanKind.AGENT,
        config={},
        mapping={
            "input": "input.value",
            "output": "output.value"
        },
        custom_eval_name="Font Suggestion Completeness",
    )
]