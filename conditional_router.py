from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
import re

class CustomerInquiryState(TypedDict):
    customer_name: str
    inquiry: str
    department: str
    priority: str
    order_number: str
    resolution: str
    confidence: float

def analyze_inquiry(state: CustomerInquiryState) -> CustomerInquiryState:
    print(f"ANALYZING: {state['customer_name']} - {state['inquiry']}")
    
    inquiry = state["inquiry"].lower()
    
    # Extract order number
    order_match = re.search(r'#?\b(\d{6,8})\b', state["inquiry"])
    order_number = order_match.group(1) if order_match else "None"
    
    # Determine department
    if any(w in inquiry for w in ["refund", "return", "money back", "cancel"]):
        department, priority, confidence = "refunds", "high", 0.95
    elif any(w in inquiry for w in ["track", "shipping", "delivery", "arrive"]):
        department, priority, confidence = "shipping", "medium", 0.90
    elif any(w in inquiry for w in ["defective", "broken", "not working", "damaged"]):
        department, priority, confidence = "technical", "high", 0.92
    elif any(w in inquiry for w in ["account", "login", "password", "reset"]):
        department, priority, confidence = "account", "medium", 0.88
    elif any(w in inquiry for w in ["payment", "charge", "billing", "invoice"]):
        department, priority, confidence = "billing", "high", 0.93
    else:
        department, priority, confidence = "general", "low", 0.70
    
    print(f"Department: {department.upper()} | Priority: {priority.upper()} | Order: {order_number}")
    
    return {
        "department": department,
        "priority": priority,
        "order_number": order_number,
        "confidence": confidence
    }


def route_to_department(state: CustomerInquiryState) -> Literal["refunds", "shipping", "technical", "account", "billing", "general"]:
    print(f" ROUTING TO: {state['department'].upper()} Department\n")
    return state["department"]


def refunds_department(state: CustomerInquiryState) -> CustomerInquiryState:
    print(" REFUNDS DEPARTMENT\n")
    order = state.get("order_number", "Unknown")
    
    if order != "None":
        resolution = f"Hello {state['customer_name']},\n\nRefund approved for order #{order}.\n Processing time: 5-7 days\n Reference: REF-{order}\n"
    else:
        resolution = f"Hello {state['customer_name']},\n\nPlease provide your order number to process the refund."
    
    print(resolution)
    return {"resolution": resolution}


def shipping_department(state: CustomerInquiryState) -> CustomerInquiryState:
    print(" SHIPPING DEPARTMENT\n")
    order = state.get("order_number", "Unknown")
    
    if order != "None":
        resolution = f"Hello {state['customer_name']},\n\nOrder #{order} Status:\n Out for Delivery\n Expected: Tomorrow by 8 PM\n Track: TRACK-{order}"
    else:
        resolution = f"Hello {state['customer_name']},\n\nPlease provide your order number to track your shipment."
    
    print(resolution)
    return {"resolution": resolution}

def technical_department(state: CustomerInquiryState) -> CustomerInquiryState:
    print(" TECHNICAL SUPPORT\n")
    order = state.get("order_number", "Unknown")
    
    resolution = f"Hello {state['customer_name']},\n\nTechnical case opened: TECH-{order}\n Priority: HIGH\n Specialist will contact you within 2 hours\n Direct: 1-800-TECH-HELP"
    
    print(resolution)
    return {"resolution": resolution}


def account_department(state: CustomerInquiryState) -> CustomerInquiryState:
    """Handles account issues"""
    print(" ACCOUNT SERVICES\n")
    
    resolution = f"Hello {state['customer_name']},\n\nAccount assistance:\n Reset: www.store.com/reset-password\n 24/7 Support: 1-800-ACCOUNT\n Live Chat: Available Now"
    
    print(resolution)
    return {"resolution": resolution}


def billing_department(state: CustomerInquiryState) -> CustomerInquiryState:
    print(" BILLING DEPARTMENT\n")
    order = state.get("order_number", "Unknown")
    
    resolution = f"Hello {state['customer_name']},\n\nBilling review initiated:\n Transaction: PAY-{order}\n Investigation: 24-48 hours\n Hotline: 1-800-BILLING"
    
    print(resolution)
    return {"resolution": resolution}


def general_department(state: CustomerInquiryState) -> CustomerInquiryState:
    print(" GENERAL SUPPORT\n")
    
    resolution = f"Hello {state['customer_name']},\n\nThank you for contacting us!\n\nHow can I assist with: '{state['inquiry']}'?\n\nFor specific issues:\n• Refunds: Press 1\n• Shipping: Press 2\n• Technical: Press 3"
    
    print(resolution)
    return {"resolution": resolution}

def create_support_router():
    workflow = StateGraph(CustomerInquiryState)
    
    # Add nodes
    workflow.add_node("analyzer", analyze_inquiry)
    workflow.add_node("refunds", refunds_department)
    workflow.add_node("shipping", shipping_department)
    workflow.add_node("technical", technical_department)
    workflow.add_node("account", account_department)
    workflow.add_node("billing", billing_department)
    workflow.add_node("general", general_department)
    
    # Set entry and routing
    workflow.set_entry_point("analyzer")
    workflow.add_conditional_edges("analyzer", route_to_department, {
        "refunds": "refunds", "shipping": "shipping", "technical": "technical",
        "account": "account", "billing": "billing", "general": "general"
    })
    
    # All departments end workflow
    for dept in ["refunds", "shipping", "technical", "account", "billing", "general"]:
        workflow.add_edge(dept, END)
    
    return workflow.compile()


def run_application():
  
    print("E-COMMERCE CUSTOMER SUPPORT SYSTEM".center(70))
    print("\n Departments:")
    print("   Refunds |  Shipping |  Technical |  Account |  Billing |  General")
    
    app = create_support_router()
    
    while True:
        print("=" * 70)
        customer_name = input(" Customer Name (or 'quit'): ").strip()
        
        if customer_name.lower() in ['quit', 'exit', 'q']:
            print("\n Thank you for using the support system!")
            break
        
        if not customer_name:
            print("  Please enter a customer name.")
            continue
        
        inquiry = input(" Inquiry: ").strip()
        
        if not inquiry:
            print("  Please enter an inquiry.")
            continue
        
        # Create initial state
        initial_state = {
            "customer_name": customer_name,
            "inquiry": inquiry,
            "department": "",
            "priority": "",
            "order_number": "",
            "resolution": "",
            "confidence": 0.0
        }
        
        # Process inquiry
        print("\n Processing...")
        final_state = app.invoke(initial_state)
        
        # Display summary
        print(f"TICKET SUMMARY: {final_state['department'].upper()} | Priority: {final_state['priority'].upper()}")
        print(f"Order: {final_state.get('order_number', 'N/A')} | Confidence: {final_state['confidence']:.0%}")


if __name__ == "__main__":
    try:
        run_application()
    except ImportError:
        print("\nERROR: Install langgraph with: pip install langgraph")