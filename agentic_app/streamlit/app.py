import streamlit as st
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Add src to path
sys.path.insert(0, '/Users/bowenl/work/test-codex/agentic_app/src')

# Import from refactored modules
from agent import Agent
from client import SambaNovaClient
from tools import get_registry

st.set_page_config(page_title="SambaNova Agent", page_icon="robot", layout="wide")

# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'model' not in st.session_state:
    st.session_state.model = "MiniMax-M2.5"


def init_agent():
    """Initialize or get the agent from session state."""
    if st.session_state.agent is None:
        client = SambaNovaClient()
        client.set_model(st.session_state.model)
        st.session_state.agent = Agent(client, use_memory=True)
    return st.session_state.agent


# Page header
st.title("SambaNova Agentic App")
st.markdown("An AI agent with tools and memory powered by SambaNova")

# Sidebar with settings
with st.sidebar:
    st.header("Settings")
    st.session_state.model = st.selectbox(
        "Model",
        ["MiniMax-M2.5", "Meta-Llama-3.3-70B-Instruct"],
        index=0
    )
    
    if st.button("Update Agent"):
        st.session_state.agent = None
        st.rerun()
    
    st.divider()
    st.subheader("Available Tools")
    
    # Get tools from registry
    registry = get_registry()
    tools_list = registry.list_tools()
    
    for tool in tools_list:
        st.markdown(f"**{tool['name']}**")
        st.caption(tool["description"])
    
    st.divider()
    st.subheader("Memory")
    
    with st.expander("Remember Something"):
        key = st.text_input("Key")
        value = st.text_area("Value")
        if st.button("Save to Memory"):
            if key and value:
                agent = init_agent()
                result = agent.memory.remember(key, value)
                st.success(result)
    
    with st.expander("Recall from Memory"):
        recall_key = st.text_input("Key to Recall")
        if st.button("Recall"):
            if recall_key:
                agent = init_agent()
                result = agent.memory.recall(key=recall_key)
                st.text_area("Result", result, height=100)
    
    with st.expander("Search Memory"):
        search_query = st.text_input("Search Query")
        if st.button("Search Memory"):
            if search_query:
                agent = init_agent()
                result = agent.memory.recall(query=search_query)
                st.text_area("Results", result, height=100)
    
    st.divider()
    st.subheader("Conversations")
    
    if st.button("New Conversation"):
        new_name = st.text_input("Conversation Name (optional)")
        agent = init_agent()
        result = agent.new_conversation(new_name if new_name else None)
        st.session_state.messages = []
        st.success(result)
    
    agent = init_agent()
    convs = agent.list_conversations()
    if convs:
        st.write("Recent Conversations:")
        for conv in convs[:5]:
            st.markdown(f"- {conv['name']} ({conv['created_at'][:10]})")
    
    st.divider()
    
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Main chat area
st.subheader("Chat")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask me anything..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get agent response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            agent = init_agent()
            response = agent.run(prompt)
            st.markdown(response)
    
    # Add assistant message
    st.session_state.messages.append({"role": "assistant", "content": response})

# Example prompts
st.markdown("---")
st.subheader("Example Prompts")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Write a Python function"):
        st.session_state.messages.append({
            "role": "user",
            "content": "Write a Python function to calculate fibonacci numbers"
        })
        st.rerun()

with col2:
    if st.button("Search the web"):
        st.session_state.messages.append({
            "role": "user",
            "content": "Search the web for latest AI news"
        })
        st.rerun()

with col3:
    if st.button("Run a calculation"):
        st.session_state.messages.append({
            "role": "user",
            "content": "Calculate sqrt(144) * 2 + 50"
        })
        st.rerun()
