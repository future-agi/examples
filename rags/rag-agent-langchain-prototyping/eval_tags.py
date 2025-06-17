from fi_instrumentation.fi_types import EvalName, EvalTag, EvalTagType, EvalSpanKind


list_of_eval_tags = [
        EvalTag(
            eval_name=EvalName.CONTEXT_RELEVANCE,
            value=EvalSpanKind.RETRIEVER,
            type=EvalTagType.OBSERVATION_SPAN,
            config={},
            mapping={
                'input' : "input.value",
                'context' : "output.value"
            },
            custom_eval_name="Context Relevance",
        ),
        EvalTag(
            eval_name=EvalName.EVAL_CONTEXT_RETRIEVAL_QUALITY,
            value=EvalSpanKind.AGENT,
            type=EvalTagType.OBSERVATION_SPAN,
            config={},
            mapping={
                'context' : "documents_retrieved",
                'input' : "raw.input",
                'output' : "raw.output"
            },
            custom_eval_name="Retrieval Quality",
        ),    
        EvalTag(
            eval_name=EvalName.CHUNK_UTILIZATION,
            value=EvalSpanKind.AGENT,
            type=EvalTagType.OBSERVATION_SPAN,
            config={},
            mapping={
                'context' : "documents_retrieved",
                'input' : "raw.input",
                'output' : "raw.output"
            },
            custom_eval_name="Chunk Utilization",
        ),      
        EvalTag(
            eval_name=EvalName.EVAL_RANKING,
            value=EvalSpanKind.RETRIEVER,
            type=EvalTagType.OBSERVATION_SPAN,
            config={},
            mapping={
                'input' : "input.value",
                'context' : "output.value"
            },
            custom_eval_name="Retriever Ranking",
            
        ),
]