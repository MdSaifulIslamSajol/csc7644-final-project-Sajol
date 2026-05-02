import time
import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from src.langgraphagenticai.evaluation.logger import ResponseLogger, extract_token_usage


class DisplayResultStreamlit:
    def __init__(self, usecase, graph, user_message, model_name="unknown"):
        self.usecase = usecase
        self.graph = graph
        self.user_message = user_message
        self.model_name = model_name
        self.logger = ResponseLogger(usecase, model_name)

    def display_result_on_ui(self):
        usecase = self.usecase
        graph = self.graph
        user_message = self.user_message
        print(user_message)

        if usecase == "Basic Chatbot":
            start = time.time()
            final_msg = None
            for event in graph.stream({'messages': ("user", user_message)}):
                for value in event.values():
                    final_msg = value["messages"]
                    with st.chat_message("user"):
                        st.write(user_message)
                    with st.chat_message("assistant"):
                        st.write(value["messages"].content)
            elapsed = time.time() - start

            response_text = final_msg.content if final_msg is not None else ""
            tokens = extract_token_usage(final_msg) if final_msg is not None else {}
            saved = self.logger.save(
                query=user_message,
                response=response_text,
                latency_seconds=elapsed,
                **tokens,
            )
            st.caption(f"Logged: `{saved}` | {elapsed:.2f}s")

        elif usecase == "Chatbot With Web":
            start = time.time()
            initial_state = {"messages": [user_message]}
            res = graph.invoke(initial_state)
            elapsed = time.time() - start

            tool_calls = []
            final_ai = None
            for message in res['messages']:
                if isinstance(message, HumanMessage):
                    with st.chat_message("user"):
                        st.write(message.content)
                elif isinstance(message, ToolMessage):
                    tool_calls.append({"name": getattr(message, "name", "tool"),
                                       "content_preview": (message.content or "")[:200]})
                    with st.chat_message("ai"):
                        st.write("Tool Call Start")
                        st.write(message.content)
                        st.write("Tool Call End")
                elif isinstance(message, AIMessage) and message.content:
                    final_ai = message
                    with st.chat_message("assistant"):
                        st.write(message.content)

            tool_used = len(tool_calls) > 0
            subcategory = "with_tool" if tool_used else "no_tool"
            tokens = extract_token_usage(final_ai) if final_ai else {}
            response_text = final_ai.content if final_ai else ""

            saved = self.logger.save(
                query=user_message,
                response=response_text,
                latency_seconds=elapsed,
                subcategory=subcategory,
                tool_used=tool_used,
                tool_call_count=len(tool_calls),
                tool_calls=tool_calls if tool_calls else None,
                **tokens,
            )
            st.caption(f"Logged: `{saved}` | {elapsed:.2f}s | tool_used={tool_used}")

        elif usecase == "AI News":
            frequency = self.user_message
            start = time.time()
            with st.spinner("Fetching and summarizing news..."):
                result = graph.invoke({"messages": frequency})
                elapsed = time.time() - start
                article_count = len(result.get("news_data", []) or [])
                summary_text = result.get("summary", "")

                try:
                    AI_NEWS_PATH = f"./AINews/{frequency.lower()}_summary.md"
                    with open(AI_NEWS_PATH, "r") as file:
                        markdown_content = file.read()
                    st.markdown(markdown_content, unsafe_allow_html=True)
                except FileNotFoundError:
                    st.error(f"News Not Generated or File not found: {AI_NEWS_PATH}")
                    markdown_content = ""
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    markdown_content = ""

                saved = self.logger.save(
                    query=f"Fetch {frequency} AI news",
                    response=summary_text or markdown_content,
                    latency_seconds=elapsed,
                    subcategory=frequency.lower(),
                    frequency=frequency.lower(),
                    article_count=article_count,
                    target_latency_seconds={"daily": 30, "weekly": 45, "monthly": 60}.get(frequency.lower()),
                    within_target=elapsed <= {"daily": 30, "weekly": 45, "monthly": 60}.get(frequency.lower(), 9999),
                )
                st.caption(
                    f"Logged: `{saved}` | {elapsed:.2f}s | {article_count} articles"
                )
