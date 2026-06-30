from __future__ import annotations

from typing import TypedDict, Literal, Optional, List
from langgraph.graph import StateGraph, END


#  Define a Typed State Object
class SupportState(TypedDict, total=False):
    # Input
    user_message: str

    # Computed fields
    intent: Literal["billing", "bug", "how_to", "unknown"]
    entities: List[str]

    # Draft + final
    draft_reply: str
    final_reply: str

    # Debug / tracing
    steps: List[str]
    confidence: float


def add_step(state: SupportState, note: str) -> SupportState:
    steps = state.get("steps", [])
    steps.append(note)
    state["steps"] = steps
    return state


#  Nodes (each node reads/writes typed state)
def classify_intent(state: SupportState) -> SupportState:
    msg = state["user_message"].lower()

    if any(k in msg for k in ["invoice", "refund", "payment", "billing"]):
        intent: SupportState["intent"] = "billing"
        confidence = 0.85
    elif any(k in msg for k in ["error", "crash", "bug", "stack trace"]):
        intent = "bug"
        confidence = 0.90
    elif any(k in msg for k in ["how do i", "how to", "steps", "guide"]):
        intent = "how_to"
        confidence = 0.80
    else:
        intent = "unknown"
        confidence = 0.50

    state["intent"] = intent
    state["confidence"] = confidence
    state["entities"] = extract_entities(state["user_message"])
    return add_step(state, f"classify_intent -> {intent} (conf={confidence})")


def extract_entities(text: str) -> List[str]:

    # Pull capitalized words and obvious product keywords
    tokens = text.replace(",", " ").replace(".", " ").split()
    entities = [t for t in tokens if t[:1].isupper() and len(t) > 2]
    for kw in ["LangGraph", "LangChain", "TaskFlow", "API", "Docker"]:
        if kw.lower() in text.lower() and kw not in entities:
            entities.append(kw)
    return entities


def draft_reply(state: SupportState) -> SupportState:
    intent = state.get("intent", "unknown")
    entities = state.get("entities", [])

    if intent == "billing":
        reply = (
            "Got it — billing issue. Please share your order/invoice ID and the last 4 digits of the card "
            "(never the full number). I'll help confirm the charge/refund status."
        )
    elif intent == "bug":
        reply = (
            "Sorry about the bug. Please share the exact error message and steps to reproduce. "
            "If you can, include your environment (OS, Python version) and a minimal snippet."
        )
    elif intent == "how_to":
        reply = (
            "Sure — I can walk you through it. Tell me what you're trying to achieve and your current setup, "
            "and I'll give step-by-step instructions."
        )
    else:
        reply = (
            "Thanks — I'm not fully sure yet. Can you clarify what you're trying to do and what went wrong?"
        )

    if entities:
        reply += f"\n\n(Detected keywords: {', '.join(entities)})"

    state["draft_reply"] = reply
    return add_step(state, "draft_reply -> created")


def finalize(state: SupportState) -> SupportState:
    # In a real workflow you might apply tone, compliance checks, or formatting rules here.
    state["final_reply"] = state.get("draft_reply", "")
    return add_step(state, "finalize -> final_reply set")


#  Build the graph
def build_graph():
    g = StateGraph(SupportState)

    g.add_node("classify_intent", classify_intent)
    g.add_node("draft_reply", draft_reply)
    g.add_node("finalize", finalize)

    g.set_entry_point("classify_intent")
    g.add_edge("classify_intent", "draft_reply")
    g.add_edge("draft_reply", "finalize")
    g.add_edge("finalize", END)

    return g.compile()


def main():
    app = build_graph()

    print("Typed State Object")
    print("Type something and press Enter. Type 'exit' to quit.\n")

    while True:
        user = input("You: ").strip()
        if not user:
            continue
        if user.lower() in {"exit", "quit"}:
            print("Bye!")
            break

        initial_state: SupportState = {
            "user_message": user,
            "steps": [],
        }

        result: SupportState = app.invoke(initial_state)

        print("\n--- FINAL REPLY ---")
        print(result.get("final_reply", ""))

        print("\n--- STATE (typed fields) ---")
        for k in ["intent", "confidence", "entities", "steps"]:
            print(f"{k}: {result.get(k)}")
        print()


if __name__ == "__main__":
    main()
