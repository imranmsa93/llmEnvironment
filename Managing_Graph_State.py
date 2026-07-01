from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
import operator

# Define the state structure
class GraphState(TypedDict):
    messages: Annotated[Sequence[str], operator.add]  # Automatically concatenates lists
    counter: int
    user_input: str
    processed_data: str
    context: dict
    history: Annotated[Sequence[str], operator.add]  # Automatically concatenates lists


# Define node functions that update state
def input_node(state: GraphState) -> GraphState:
    
    print(f"\n=== INPUT NODE ===")
    print(f"Received input: {state['user_input']}")
    
    return {
        "messages": [f"User: {state['user_input']}"],
        "counter": state["counter"] + 1,
        "history": ["input_node"]
    }


def process_node(state: GraphState) -> GraphState:
   
    print(f"\n=== PROCESS NODE ===")
    processed = state["user_input"].upper()
    print(f"Processed: {processed}")
    
    return {
        "processed_data": processed,
        "context": {**state.get("context", {}), "last_processed": processed},
        "counter": state["counter"] + 1,
        "history": ["process_node"]
    }


def enrich_node(state: GraphState) -> GraphState:
    
    print(f"\n=== ENRICH NODE ===")
    
    enriched_data = {
        "original": state["user_input"],
        "processed": state["processed_data"],
        "length": len(state["user_input"]),
        "word_count": len(state["user_input"].split())
    }
    
    print(f"Enriched data: {enriched_data}")
    
    return {
        "context": {
            **state.get("context", {}),
            "enriched": enriched_data
        },
        "counter": state["counter"] + 1,
        "history": ["enrich_node"]
    }

def output_node(state: GraphState) -> GraphState:
    
    print(f"\n=== OUTPUT NODE ===")
    
    word_count = state["context"]["enriched"]["word_count"]
    response = f"Processed: '{state['processed_data']}' ({word_count} words)"
    print(f"Response: {response}")
    
    return {
        "messages": [f"Assistant: {response}"],
        "counter": state["counter"] + 1,
        "history": ["output_node"]
    }

def create_graph():
    # Initialize the graph with our state schema
    workflow = StateGraph(GraphState)
    
    # Add nodes to the graph
    workflow.add_node("input", input_node)
    workflow.add_node("process", process_node)
    workflow.add_node("enrich", enrich_node)
    workflow.add_node("output", output_node)
    
    # Define the edges (flow between nodes)
    workflow.add_edge("input", "process")
    workflow.add_edge("process", "enrich")
    workflow.add_edge("enrich", "output")
    workflow.add_edge("output", END)
    
    # Set the entry point
    workflow.set_entry_point("input")
    
    # Compile the graph
    app = workflow.compile()
    
    return app

def print_state(state: GraphState, title: str = "Current State"):

    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")
    print(f"Counter: {state.get('counter', 0)}")
    print(f"User Input: {state.get('user_input', 'N/A')}")
    print(f"Processed Data: {state.get('processed_data', 'N/A')}")
    print(f"Messages: {state.get('messages', [])}")
    print(f"History: {' -> '.join(state.get('history', []))}")
    print(f"Context: {state.get('context', {})}")
    print(f"{'='*50}\n")


def run_application():
    
    # Create the graph
    app = create_graph()
    
    print("\nThis application will process your text through a stateful graph.")
    
    while True:
        # Get user input
        user_text = input("\n Enter text to process (or 'quit' to exit): ").strip()
        
        if user_text.lower() in ['quit', 'exit', 'q']:
            print("\nThanks for using the application!")
            break
        
        if not user_text:
            print(" Please enter some text.")
            continue
        
        # Ask for execution mode
        print("\nChoose execution mode:")
        print("1. Normal execution")
        print("2. Step-by-step execution")
        
        mode = input("Enter 1 or 2 (default: 1): ").strip()
        
        # Create initial state
        initial_state = {
            "messages": [],
            "counter": 0,
            "user_input": user_text,
            "processed_data": "",
            "context": {},
            "history": []
        }
        
        print_state(initial_state, "Initial State")
        
        if mode == "2":
            # Stream through each step
            print("\n Streaming execution...")
            for i, step in enumerate(app.stream(initial_state), 1):
                print(f"\n--- Step {i} ---")
                for node_name, node_state in step.items():
                    print(f" Completed Node: {node_name}")
                    print(f"  Counter: {node_state.get('counter')}")
                    print(f"  History: {' -> '.join(node_state.get('history', []))}")
            
            # Get final state
            final_state = app.invoke(initial_state)
            print_state(final_state, "Final State After Execution")
        else:
            # Normal execution
            print("\n Running graph...")
            final_state = app.invoke(initial_state)
            print_state(final_state, "Final State After Execution")
        
        # Ask if user wants to continue
        continue_processing = input("\n Process another text? (y/n): ").strip().lower()
        if continue_processing not in ['y', 'yes', '']:
            print("\nThanks for using the application!")
            break
    

if __name__ == "__main__":
    
    try:
        run_application()
    except ImportError:
        print("\n" + "!"*70)
        print("ERROR: LangGraph not installed!".center(70))
        print("!"*70 + "\n")