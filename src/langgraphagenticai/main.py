import streamlit as st
from src.langgraphagenticai.ui.streamlitui.loadui import LoadStreamlitUI
from src.langgraphagenticai.LLMS.groqllm import GroqLLM
from src.langgraphagenticai.graph.graph_builder import GraphBuilder
from src.langgraphagenticai.ui.streamlitui.display_result import DisplayResultStreamlit


_STATE_COLORS = {
    "idle":       "#22c55e",  # green
    "processing": "#eab308",  # yellow
    "error":      "#ef4444",  # red
}


def _style_chat_input(slot, state: str):
    color = _STATE_COLORS.get(state, _STATE_COLORS["idle"])
    slot.markdown(
        f"""
        <style>
        [data-testid="stChatInput"] > div:first-child,
        [data-testid="stChatInput"] [data-baseweb="textarea"] {{
            border: 2px solid {color} !important;
            box-shadow: 0 0 0 2px {color}33 !important;
            border-radius: 10px !important;
            transition: border-color 0.25s ease, box-shadow 0.25s ease;
        }}
        [data-testid="stChatInput"] textarea {{
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
        }}
        [data-testid="stChatInput"] textarea:focus {{
            outline: none !important;
            border: none !important;
            box-shadow: none !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def load_langgraph_agenticai_app():
    """
    Loads and runs the LangGraph AgenticAI application with Streamlit UI.
    """

    ##Load UI
    ui = LoadStreamlitUI()
    user_input = ui.load_streamlit_ui()

    # Slot for dynamically restyled chat-input border
    css_slot = st.empty()
    _style_chat_input(css_slot, "idle")  # default green

    if not user_input:
        _style_chat_input(css_slot, "error")
        st.error("Error: Failed to load user input from the UI.")
        return

    # Text input for user message
    if st.session_state.IsFetchButtonClicked:
        user_message = st.session_state.timeframe
    else:
        user_message = st.chat_input("Enter your message:")

    # Spinner sits right above the chat-input
    spinner_slot = st.empty()

    if user_message:
        try:
            _style_chat_input(css_slot, "processing")
            with spinner_slot.container():
                st.markdown(
                    "<div style='text-align:center; color:#eab308; font-weight:600;'>"
                    "LLM is processing your request..."
                    "</div>",
                    unsafe_allow_html=True,
                )

            ## Configure The LLM's
            obj_llm_config = GroqLLM(user_contols_input=user_input)
            model = obj_llm_config.get_llm_model()

            if not model:
                _style_chat_input(css_slot, "error")
                spinner_slot.empty()
                st.error("Error: LLM model could not be initialized")
                return

            # Initialize and set up the graph based on use case
            usecase = user_input.get("selected_usecase")

            if not usecase:
                _style_chat_input(css_slot, "error")
                spinner_slot.empty()
                st.error("Error: No use case selected.")
                return

            ## Graph Builder
            graph_builder = GraphBuilder(model)
            try:
                graph = graph_builder.setup_graph(usecase)
                print(user_message)
                model_name = user_input.get("selected_groq_model", "unknown")
                DisplayResultStreamlit(usecase, graph, user_message, model_name).display_result_on_ui()

                # success
                spinner_slot.empty()
                _style_chat_input(css_slot, "idle")

            except Exception as e:
                spinner_slot.empty()
                _style_chat_input(css_slot, "error")
                st.error(f"Error: Graph set up failed- {e}")
                return

        except Exception as e:
            spinner_slot.empty()
            _style_chat_input(css_slot, "error")
            st.error(f"Error: Graph set up failed- {e}")
            return
