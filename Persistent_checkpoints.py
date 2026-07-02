from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
import operator

#  STATE 
class OrderState(TypedDict):
    order_id: str
    items: Annotated[list, operator.add]
    total: float
    status: str
    notes: Annotated[list, operator.add]

# WORKFLOW NODES
def validate(state: OrderState) -> OrderState:
    print(f" Validating order {state['order_id']}...")
    return {"status": "validated", "notes": ["Validated"]}

def calculate(state: OrderState) -> OrderState:
    print(f" Calculating total...")
    prices = {"laptop": 999, "mouse": 29, "keyboard": 79, "monitor": 299}
    total = sum(prices.get(item, 50) for item in state['items'])
    return {"total": total, "status": "calculated", "notes": [f"Total: ${total}"]}

def payment(state: OrderState) -> OrderState:
    print(f" Processing payment ${state['total']}...")
    return {"status": "paid", "notes": ["Payment confirmed"]}

def ship(state: OrderState) -> OrderState:
    print(f" Arranging shipment...")
    return {"status": "shipped", "notes": ["Shipped"]}

def complete(state: OrderState) -> OrderState:
    print(f" Order complete!")
    return {"status": "completed", "notes": ["Completed"]}

# GRAPH CREATION
def create_workflow():
    workflow = StateGraph(OrderState)
    workflow.add_node("validate", validate)
    workflow.add_node("calculate", calculate)
    workflow.add_node("payment", payment)
    workflow.add_node("ship", ship)
    workflow.add_node("complete", complete)
    workflow.set_entry_point("validate")
    workflow.add_edge("validate", "calculate")
    workflow.add_edge("calculate", "payment")
    workflow.add_edge("payment", "ship")
    workflow.add_edge("ship", "complete")
    workflow.add_edge("complete", END)
    return workflow

#  UTILITIES
def show_checkpoints(checkpointer, thread_id):
    print(f"\n Checkpoints for '{thread_id}':")
    for i, cp in enumerate(list(checkpointer.list({"configurable": {"thread_id": thread_id}}))[:5], 1):
        status = cp.checkpoint['channel_values'].get('status', 'N/A')
        print(f"   {i}. Status: {status}")

def create_initial_state(order_id, items):
    return {"order_id": order_id, "items": items, "total": 0.0, "status": "pending", "notes": []}

#  BASIC CHECKPOINTING 
def basic_checkpointing():
    print("\n" + "="*60)
    print(" Basic Checkpointing".center(60))
    print("="*60)
    
    with SqliteSaver.from_conn_string(":memory:") as checkpointer:
        app = create_workflow().compile(checkpointer=checkpointer)
        state = create_initial_state("ORD-001", ["laptop", "mouse"])
        config = {"configurable": {"thread_id": "thread-1"}}
        
        print("\n Running workflow with auto-checkpointing...")
        result = app.invoke(state, config)
        
        print(f"\n Final: {result['status']}, Total: ${result['total']}")
        show_checkpoints(checkpointer, "thread-1")
        print("\n Each step automatically checkpointed!")

# RESUME FROM CHECKPOINT 
def resume_from_checkpoint():
    print("\n" + "="*60)
    print(" Resume from Checkpoint".center(60))
    print("="*60)
    
    with SqliteSaver.from_conn_string(":memory:") as checkpointer:
        app = create_workflow().compile(checkpointer=checkpointer)
        state = create_initial_state("ORD-002", ["keyboard"])
        config = {"configurable": {"thread_id": "thread-2"}}
        
        print("\n Starting workflow...")
        for i, step in enumerate(app.stream(state, config)):
            if i == 2:
                print("\n  INTERRUPTION! Stopping after payment...")
                break
        
        current = app.get_state(config)
        print(f"  Paused at: {current.values['status']}")
        show_checkpoints(checkpointer, "thread-2")
        
        print("\n Resuming from checkpoint...")
        result = app.invoke(None, config)
        print(f" Completed: {result['status']}")

#  TIME-TRAVEL 
def time_travel():
    print("\n" + "="*60)
    print("Time-Travel Through States".center(60))
    print("="*60)
    
    with SqliteSaver.from_conn_string(":memory:") as checkpointer:
        app = create_workflow().compile(checkpointer=checkpointer)
        state = create_initial_state("ORD-003", ["monitor"])
        config = {"configurable": {"thread_id": "thread-3"}}
        
        print("\n Executing workflow...")
        result = app.invoke(state, config)
        print(f" Final: {result['status']}")
        
        print("\n Time-traveling through history...")
        history = list(app.get_state_history(config))
        
        for i, snapshot in enumerate(history[:4], 1):
            status = snapshot.values.get('status', 'N/A')
            total = snapshot.values.get('total', 0)
            print(f"   {i}. Status: {status}, Total: ${total}")

#  BRANCHING 
def branching():
    print("\n" + "="*60)
    print("Branching from Checkpoint".center(60))
    print("="*60)
    
    with SqliteSaver.from_conn_string(":memory:") as checkpointer:
        app = create_workflow().compile(checkpointer=checkpointer)
        state = create_initial_state("ORD-004", ["laptop"])
        config = {"configurable": {"thread_id": "thread-4"}}
        
        print("\n Original execution...")
        original = app.invoke(state, config)
        print(f" Original: {len(original['items'])} items, ${original['total']}")
        
        history = list(app.get_state_history(config))
        early_state = None
        for snapshot in reversed(history):
            if snapshot.values.get('status') == 'validated':
                early_state = snapshot
                break
        
        if early_state:
            print("\n Branching from 'validated' checkpoint...")
            branch_state = early_state.values.copy()
            branch_state["items"] = branch_state["items"] + ["keyboard", "mouse"]
            branch_config = {"configurable": {"thread_id": "thread-4-branch"}}
            branch_result = app.invoke(branch_state, branch_config)
            
            print(f" Branch: {len(branch_result['items'])} items, ${branch_result['total']}")
            print(f"   Difference: ${branch_result['total'] - original['total']}")

# PERSISTENT STORAGE 
def persistent_storage():
    print("\n" + "="*60)
    print(" Persistent SQLite Storage".center(60))
    print("="*60)
    
    db_path = "checkpoints.db"
    print(f"\n Using persistent DB: {db_path}")
    
    with SqliteSaver.from_conn_string(db_path) as checkpointer:
        app = create_workflow().compile(checkpointer=checkpointer)
        state = create_initial_state("ORD-005", ["monitor", "keyboard"])
        config = {"configurable": {"thread_id": "persistent-1"}}
        
        print("\n Executing with persistent storage...")
        result = app.invoke(state, config)
        
        print(f" Completed: {result['status']}, ${result['total']}")
        print(f" Checkpoints saved to {db_path}")
        print("   Restart program to access saved checkpoints!")

#  MAIN MENU 
def main():
    print("\n" + "="*60)
    print("LangGraph Persistent Checkpoints".center(60))
    print("="*60)
    
    examples = {
        "1": ("Basic Checkpointing", basic_checkpointing),
        "2": ("Resume from Checkpoint", resume_from_checkpoint),
        "3": ("Time-Travel Through States", time_travel),
        "4": ("Branching from Checkpoint", branching),
        "5": ("Persistent Storage", persistent_storage)
    }
    
    while True:
        for key, (name, _) in examples.items():
            print(f"   {key}. {name}")
        print("   0. Exit")
        
        choice = input("\nSelect (0-6): ").strip()
        
        if choice == "0":
            print("\n Thank you See you Again!")
            break
        elif choice in examples:
            examples[choice][1]()
        elif choice == "6":
            for _, func in examples.values():
                func()
        else:
            print(" Invalid choice")
        
        input("\n Press Enter to continue...")

if __name__ == "__main__":
    try:
        main()
    except ImportError:
        print("\n  Install: pip install langgraph")