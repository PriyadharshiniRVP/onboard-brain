import streamlit as st
import requests

st.set_page_config(page_title="Onboarding Brain", page_icon="")
st.title(" Onboarding Brain")
st.caption("Ask me anything about Acme Corp — I'll show you how I found the answer.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # If this message has a path, show it in an expander
        if msg.get("path"):
            with st.expander("How I found this"):
                for step in msg["path"]:
                    st.markdown(f"**Tool:** `{step['tool']}`")
                    st.markdown(f"**Args:** `{step['args']}`")
                    st.json(step["result"])

# Chat input
if prompt := st.chat_input("How do I deploy to production?"):
    # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call the FastAPI backend
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    "http://127.0.0.1:8000/ask",
                    json={"text": prompt},
                    timeout=60
                )
                response.raise_for_status()
                data = response.json()
                answer = data.get("answer", "No answer returned.")
                path = data.get("path", [])

                st.markdown(answer)

                # Show the path
                if path:
                    with st.expander(" How I found this"):
                        for step in path:
                            st.markdown(f"**Tool:** `{step['tool']}`")
                            st.markdown(f"**Args:** `{step['args']}`")
                            st.json(step["result"])

                # Save to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "path": path
                })

            except Exception as e:
                st.error(f"Error: {e}")