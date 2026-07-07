from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator
import time

# STATE DEFINITIONS 
def merge_dicts(left: dict, right: dict) -> dict:
    return {**left, **right}

class MainGraphState(TypedDict):
    user_input: str
    parallel_results: Annotated[dict, merge_dicts]
    subgraph_results: Annotated[dict, merge_dicts]
    final_summary: str

class AnalysisSubgraphState(TypedDict):
    text: str
    word_count: int
    char_count: int

class ProcessingSubgraphState(TypedDict):
    text: str
    uppercase: str
    lowercase: str

# PARALLEL NODES 
def sentiment_analyzer(state: MainGraphState) -> MainGraphState:
    print("Sentiment Analyzer started...")
    time.sleep(0.5)
    text = state["user_input"].lower()
    positive = ["good", "great", "excellent", "happy"]
    negative = ["bad", "terrible", "sad", "hate"]
    pos_count = sum(1 for w in positive if w in text)
    neg_count = sum(1 for w in negative if w in text)
    sentiment = "Positive" if pos_count > neg_count else "Negative" if neg_count > pos_count else "Neutral"
    print(f"Sentiment: {sentiment}")
    return {"parallel_results": {**state.get("parallel_results", {}), "sentiment": sentiment}}

def language_detector(state: MainGraphState) -> MainGraphState:
    print("Language Detector started...")
    time.sleep(0.5)
    text = state["user_input"].lower()
    if any(w in text for w in ["hello", "the", "is"]):
        language = "English"
    elif any(w in text for w in ["hola", "el", "es"]):
        language = "Spanish"
    else:
        language = "Unknown"
    print(f"Language: {language}")
    return {"parallel_results": {**state.get("parallel_results", {}), "language": language}}

def keyword_extractor(state: MainGraphState) -> MainGraphState:
    print("Keyword Extractor started...")
    time.sleep(0.5)
    words = state["user_input"].split()
    keywords = [w for w in words if len(w) > 4][:3]
    keywords_str = ", ".join(keywords) if keywords else "None"
    print(f"Keywords: {keywords_str}")
    return {"parallel_results": {**state.get("parallel_results", {}), "keywords": keywords_str}}

#  ANALYSIS
def count_words(state: AnalysisSubgraphState) -> AnalysisSubgraphState:
    print("  Counting words...")
    word_count = len(state["text"].split())
    return {"word_count": word_count}

def count_chars(state: AnalysisSubgraphState) -> AnalysisSubgraphState:
    print("  Counting characters...")
    char_count = len(state["text"])
    return {"char_count": char_count}

def create_analysis_subgraph():
    subgraph = StateGraph(AnalysisSubgraphState)
    subgraph.add_node("count_words", count_words)
    subgraph.add_node("count_chars", count_chars)
    subgraph.set_entry_point("count_words")
    subgraph.add_edge("count_words", "count_chars")
    subgraph.add_edge("count_chars", END)
    return subgraph.compile()

#  PROCESSING 
def to_uppercase(state: ProcessingSubgraphState) -> ProcessingSubgraphState:
    print("  Converting to uppercase...")
    return {"uppercase": state["text"].upper()}

def to_lowercase(state: ProcessingSubgraphState) -> ProcessingSubgraphState:
    print("  Converting to lowercase...")
    return {"lowercase": state["text"].lower()}

def create_processing_subgraph():
    subgraph = StateGraph(ProcessingSubgraphState)
    subgraph.add_node("to_uppercase", to_uppercase)
    subgraph.add_node("to_lowercase", to_lowercase)
    subgraph.set_entry_point("to_uppercase")
    subgraph.add_edge("to_uppercase", "to_lowercase")
    subgraph.add_edge("to_lowercase", END)
    return subgraph.compile()

#  SUBGRAPH INVOKERS
def invoke_analysis_subgraph(state: MainGraphState) -> MainGraphState:
    print("\n→ Invoking Analysis Subgraph...")
    analysis_graph = create_analysis_subgraph()
    subgraph_input = {"text": state["user_input"], "word_count": 0, "char_count": 0}
    result = analysis_graph.invoke(subgraph_input)
    print(f"  Analysis complete: {result['word_count']} words, {result['char_count']} chars")
    return {
        "subgraph_results": {
            **state.get("subgraph_results", {}),
            "analysis": {"word_count": result["word_count"], "char_count": result["char_count"]}
        }
    }

def invoke_processing_subgraph(state: MainGraphState) -> MainGraphState:
    print("\n→ Invoking Processing Subgraph...")
    processing_graph = create_processing_subgraph()
    subgraph_input = {"text": state["user_input"], "uppercase": "", "lowercase": ""}
    result = processing_graph.invoke(subgraph_input)
    print(f"  Processing complete")
    return {
        "subgraph_results": {
            **state.get("subgraph_results", {}),
            "processing": {"uppercase": result["uppercase"], "lowercase": result["lowercase"]}
        }
    }

#SUMMARY NODE
def create_summary(state: MainGraphState) -> MainGraphState:
    print("\n→ Creating Final Summary...")
    parallel = state.get("parallel_results", {})
    subgraph = state.get("subgraph_results", {})
    
    summary = f"""

 INPUT: {state['user_input']}

 PARALLEL EXECUTION RESULTS:
   • Sentiment: {parallel.get('sentiment', 'N/A')}
   • Language: {parallel.get('language', 'N/A')}
   • Keywords: {parallel.get('keywords', 'N/A')}

 ANALYSIS SUBGRAPH RESULTS:
   • Words: {subgraph.get('analysis', {}).get('word_count', 'N/A')}
   • Characters: {subgraph.get('analysis', {}).get('char_count', 'N/A')}

 PROCESSING SUBGRAPH RESULTS:
   • Uppercase: {subgraph.get('processing', {}).get('uppercase', 'N/A')[:40]}...
   • Lowercase: {subgraph.get('processing', {}).get('lowercase', 'N/A')[:40]}...
"""
    print(summary)
    return {"final_summary": summary}

# MAIN GRAPH
def create_main_graph():
    workflow = StateGraph(MainGraphState)
    
    # Add parallel nodes
    workflow.add_node("sentiment_analyzer", sentiment_analyzer)
    workflow.add_node("language_detector", language_detector)
    workflow.add_node("keyword_extractor", keyword_extractor)
    
    # Add subgraph invokers
    workflow.add_node("invoke_analysis", invoke_analysis_subgraph)
    workflow.add_node("invoke_processing", invoke_processing_subgraph)
    
    # Add summary node
    workflow.add_node("create_summary", create_summary)
    
    # PARALLEL EXECUTION: Set multiple entry points
    workflow.set_entry_point("sentiment_analyzer")
    workflow.set_entry_point("language_detector")
    workflow.set_entry_point("keyword_extractor")
    
    # All parallel nodes converge to analysis subgraph
    workflow.add_edge("sentiment_analyzer", "invoke_analysis")
    workflow.add_edge("language_detector", "invoke_analysis")
    workflow.add_edge("keyword_extractor", "invoke_analysis")
    
    # Sequential subgraph invocation
    workflow.add_edge("invoke_analysis", "invoke_processing")
    workflow.add_edge("invoke_processing", "create_summary")
    workflow.add_edge("create_summary", END)
    
    return workflow.compile()

# APPLICATION 
def run_application():
    app = create_main_graph()
    
    print("\n" + "="*60)
    print(" Parallel Execution and Subgraph Invocation".center(60))
    print("="*60)
    
    while True:
        user_text = input("\nEnter text to process (or 'quit' to exit): ").strip()
        
        if user_text.lower() in ['quit', 'exit', 'q']:
            print("\n Thanks for using the application!")
            break
        
        if not user_text:
            print(" Please enter some text.")
            continue
        
        initial_state = {
            "user_input": user_text,
            "parallel_results": {},
            "subgraph_results": {},
            "final_summary": ""
        }
        
        print(f"\n{'='*60}")
        print("EXECUTION STARTED".center(60))
        print(f"{'='*60}\n")
        print(" Running 3 parallel nodes...")
        
        start_time = time.time()
        final_state = app.invoke(initial_state)
        elapsed = time.time() - start_time
        
        print(f"\n{'='*60}")
        print(f"  TOTAL EXECUTION TIME: {elapsed:.2f}s".center(60))
        print(f"{'='*60}\n")
        
        continue_choice = input("Process another text? (y/n): ").strip().lower()
        if continue_choice not in ['y', 'yes', '']:
            print("\n Thanks for using the application!")
            break

if __name__ == "__main__":
    try:
        run_application()
    except ImportError:
        print("Install with: pip install langgraph")