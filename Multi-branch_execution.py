from typing import TypedDict, Literal, Annotated
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import operator, json, time

# STATE 
class WorkflowState(TypedDict):
    user_input: str
    current_step: str
    branch_chosen: str
    result: str
    history: Annotated[list, operator.add]
    final: str

#  NODES 
def input_processor(state: WorkflowState) -> WorkflowState:
    print(f"\n Processing: '{state['user_input']}'")
    time.sleep(0.5)
    return {"current_step": "input_processor", "history": ["Input processed"]}

def branch_router(state: WorkflowState) -> Literal["branch_a", "branch_b", "branch_c"]:
    text = state["user_input"].lower()
    branch = "branch_a" if any(w in text for w in ["a", "1", "first"]) else "branch_b" if any(w in text for w in ["b", "2", "second"]) else "branch_c"
    print(f" Routing to: {branch.upper()}")
    return branch

def branch_a_processor(state: WorkflowState) -> WorkflowState:
    print(f"\n [BRANCH A] Data Analysis...")
    for i in range(3):
        print(f"   {(i+1)*33}%")
        time.sleep(1)
    res = f"Analyzed '{state['user_input']}' - 42 points"
    return {"current_step": "branch_a", "branch_chosen": "branch_a", "result": res, "history": [res]}

def branch_b_processor(state: WorkflowState) -> WorkflowState:
    print(f"\n [BRANCH B] ML Pipeline...")
    for i in range(3):
        print(f"   Epoch {i+1}")
        time.sleep(1)
    res = f"Trained '{state['user_input']}' - 94.5% acc"
    return {"current_step": "branch_b", "branch_chosen": "branch_b", "result": res, "history": [res]}

def branch_c_processor(state: WorkflowState) -> WorkflowState:
    print(f"\n [BRANCH C] NLP...")
    for i in range(3):
        print(f"   Stage {i+1}")
        time.sleep(1)
    res = f"Processed '{state['user_input']}' - 15 entities"
    return {"current_step": "branch_c", "branch_chosen": "branch_c", "result": res, "history": [res]}

def aggregator(state: WorkflowState) -> WorkflowState:
    print(f"\n Aggregating from {state['branch_chosen']}...")
    time.sleep(0.5)
    return {"current_step": "aggregator", "final": f"Final: {state['result']}", "history": ["Aggregated"]}

#  GRAPH
def create_workflow():
    memory = MemorySaver()
    wf = StateGraph(WorkflowState)
    wf.add_node("input", input_processor)
    wf.add_node("branch_a", branch_a_processor)
    wf.add_node("branch_b", branch_b_processor)
    wf.add_node("branch_c", branch_c_processor)
    wf.add_node("agg", aggregator)
    wf.set_entry_point("input")
    wf.add_conditional_edges("input", branch_router, {"branch_a": "branch_a", "branch_b": "branch_b", "branch_c": "branch_c"})
    wf.add_edge("branch_a", "agg")
    wf.add_edge("branch_b", "agg")
    wf.add_edge("branch_c", "agg")
    wf.add_edge("agg", END)
    return wf.compile(checkpointer=memory)

# CHECKPOINT 
def save_checkpoint(tid):
    with open("checkpoint.json", 'w') as f:
        json.dump({"thread_id": tid, "time": time.time()}, f)
    print(f"\n Saved! Thread: {tid}")

def load_checkpoint():
    try:
        with open("checkpoint.json", 'r') as f:
            return json.load(f)
    except:
        return None

def show_state(app, tid):
    try:
        state = app.get_state({"configurable": {"thread_id": tid}})
        if state and state.values:
            print(f"\nCHECKPOINT STATE\n")
            print(f"Thread: {tid}")
            print(f"Step: {state.values.get('current_step', 'N/A')}")
            print(f"Branch: {state.values.get('branch_chosen', 'TBD')}")
            print(f"Input: {state.values.get('user_input', 'N/A')}")
            print(f"History: {state.values.get('history', [])}")
            print(f"{'='*60}\n")
            return True
        print("  No checkpoint")
        return False
    except Exception as e:
        print(f"  Error: {e}")
        return False

#  WORKFLOW OPS 
def new_workflow(app):
    print(f"\nNEW WORKFLOW\n")
    text = input("\n Input: ").strip()
    if not text:
        print("  Empty input")
        return
    
    tid = f"t_{int(time.time())}"
    print(f"\n Thread: {tid}")
    print("\nBranches: 'a'/'1' → A (Analysis) | 'b'/'2' → B (ML) | else → C (NLP)")
    
    state = {"user_input": text, "current_step": "", "branch_chosen": "", "result": "", "history": [], "final": ""}
    
    try:
        print("\n Running... \n")
        for _ in app.stream(state, {"configurable": {"thread_id": tid}}):
            pass
        final = app.get_state({"configurable": {"thread_id": tid}})
        print(f"\nCOMPLETED\n{final.values.get('final', 'No output')}\n")
    except KeyboardInterrupt:
        print("\n  PAUSED!")
        save_checkpoint(tid)
        print(f"Resume with: {tid}")

def resume_workflow(app):
    print(f"\nRESUME WORKFLOW\n")
    cp = load_checkpoint()
    
    if cp:
        print(f"\n Found: {cp['thread_id']}")
        tid = cp['thread_id'] if input("Use? (y/n): ").lower() in ['y', 'yes'] else input("Thread ID: ").strip()
    else:
        tid = input("\n Thread ID: ").strip()
    
    if not tid:
        print("  No ID")
        return
    
    if not show_state(app, tid):
        return
    
    if input("Resume? (y/n): ").lower() not in ['y', 'yes']:
        print(" Cancelled")
        return
    
    try:
        print("\n Resuming...\n")
        for _ in app.stream(None, {"configurable": {"thread_id": tid}}):
            pass
        final = app.get_state({"configurable": {"thread_id": tid}})
        print(f"\nCOMPLETED\n{'='*60}\n{final.values.get('final', 'No output')}\n")
    except KeyboardInterrupt:
        print("\n  PAUSED AGAIN!")
        save_checkpoint(tid)

def view_checkpoints(app):
    print(f"\nCHECKPOINTS\n")
    cp = load_checkpoint()
    if cp:
        print(f"\n Recent: {cp['thread_id']} | {time.ctime(cp['time'])}")
        show_state(app, cp['thread_id'])
    else:
        print("\n  None found")

# MAIN 
def main():
    print("="*60)
    print("State Restoration and Multi-Branch Resume".center(60))
    print("="*60)
    print("\nCheckpointing | Interruption | Resume | Multi-branch")
    
    app = create_workflow()
    
    while True:
        print(f"\nMENU\n")
        print("1. New Workflow\n2. Resume\n3. View Checkpoints\n4. Exit")
        
        choice = input("\n (1-4): ").strip()
        
        if choice == "1":
            new_workflow(app)
        elif choice == "2":
            resume_workflow(app)
        elif choice == "3":
            view_checkpoints(app)
        elif choice == "4":
            print("\n Bye!")
            break
        else:
            print("  Invalid")

if __name__ == "__main__":
    try:
        main()
    except ImportError:
        print("\n  pip install langgraph")