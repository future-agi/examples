from fi_instrumentation.fi_types import EvalName, EvalTag, EvalTagType, EvalSpanKind


list_of_eval_tags = [
        EvalTag(
            eval_name=EvalName.EVALUATE_LLM_FUNCTION_CALLING,
            value=EvalSpanKind.LLM,
            type=EvalTagType.OBSERVATION_SPAN,
            config={},
            mapping={
                'input' : "raw.input",
                'output' : "raw.output"
            },
            custom_eval_name="LLM Function Calling ",
        ),
        EvalTag(
            eval_name=EvalName.FACTUAL_ACCURACY,
            value=EvalSpanKind.AGENT,
            type=EvalTagType.OBSERVATION_SPAN,
            config={},
            mapping={
                'input' : "raw.input",
                'output' : "raw.output"
            },
            custom_eval_name="Factual Accuracy ",
        ),    
        EvalTag(
            eval_name=EvalName.CONTEXT_RELEVANCE,
            value=EvalSpanKind.AGENT,
            type=EvalTagType.OBSERVATION_SPAN,
            config={},
            mapping={
                'input' : "raw.input",
                'context' : "raw.output"
            },
            custom_eval_name="Context Relevance ",
        ),      
        EvalTag(
            eval_name=EvalName.CONVERSATION_RESOLUTION,
            value=EvalSpanKind.AGENT,
            type=EvalTagType.OBSERVATION_SPAN,
            config={},
            mapping={
                'output' : "raw.output"
            },
            custom_eval_name="Conversation Resolution ",
            
        ),
]