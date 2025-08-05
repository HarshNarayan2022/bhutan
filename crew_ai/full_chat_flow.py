import streamlit as st
import json
import time
from dotenv import load_dotenv

load_dotenv()

from crew_ai.chatbot import run_user_profile_retrieval, run_recommendations, run_crisis_check, run_condition_classification
from crew_ai.config import get_config

config = get_config()

def full_chat_flow(contextual_query: str, user_query: str, user_id: str = "anon_user"):

    with st.chat_message("user"):
        st.write(st.session_state.chat_history[-1]["content"])

    with st.chat_message("assistant"):
        st.write("📄 Processing your query...")

    # Retrieve user profile
    if st.session_state.user_profile is None:
        st.session_state.user_profile = run_user_profile_retrieval(user_query, user_id)

    crisis_result = run_crisis_check(contextual_query)
    is_crisis = crisis_result.get("is_crisis", False)
    explanation = crisis_result.get("explanation", "")

    # Store crisis detection in session state
    st.session_state.crisis_detected = is_crisis
    st.session_state.crisis_explanation = explanation

    if is_crisis:
        with st.chat_message("assistant"):
            st.error(f"🚨 Crisis detected: {explanation}")
            st.info("We're prioritizing your safety. Connecting you with the best support now...")
        rec = run_recommendations(
                contextual_query, 
                json.dumps(st.session_state.user_profile), 
                condition="Crisis", 
                answers="{}", 
                interpretation="N/A", 
                is_crisis="true"
            )
        
        # task_outputs = rec.tasks_output
        # retrieved_docs_crisis = task_outputs[0]

        with st.chat_message("assistant"):
            st.write("🆘 Crisis Support Recommendation:")
            def stream_answer():
                for word in rec["recommendation"].split(" "):
                    yield word + " "
                    time.sleep(0.1)
            st.write_stream(stream_answer)

        return rec
        
        # return {
        #     "recommendation": rec["recommendation"],
        #     "condition": "crisis",
        #     "is_crisis": True,
        #     "crisis_explanation": explanation,
        #     "score_interpretation": "Not applicable",
        #     # "retrieved_docs": retrieved_docs_crisis
        # }

    with st.chat_message("assistant"):
        st.write("✅ No immediate crisis detected.")
        st.write("🔍 Let's understand your mental health condition...")

    condition_result = run_condition_classification(contextual_query, json.dumps(st.session_state.user_profile))
    condition = condition_result.get("condition", "general").split(" ")[0].lower()
    condition_explanation = condition_result.get("rationale", "")
    questionnaire_name = config["CONDITION_TO_QUESTIONNAIRE"].get(condition)

    # Store condition detection in session state
    st.session_state.detected_condition = condition
    st.session_state.condition_explanation = condition_explanation

    with st.chat_message("assistant"):
        st.success(f"🧠 Based on your message, we identified: **{condition.upper()}**")
        if not questionnaire_name:
            st.info("No questionnaire available for this condition.")
            interpretation = "Not applicable"
        else:
            st.info(f"We recommend a brief **{questionnaire_name}** assessment to understand your situation better.")
            st.session_state.assessment_needed = True
            st.session_state.temp_user_query = user_query
            st.session_state.temp_condition = condition
            st.session_state.questionnaire_name = questionnaire_name
            return None

    final_rec = run_recommendations(
        contextual_query,
        json.dumps(st.session_state.user_profile),
        condition,
        json.dumps({}),
        "N/A",
        is_crisis="false"
    )

    # task_outputs = final_rec.tasks_output
    # retrieved_docs = task_outputs[0]

    with st.chat_message("assistant"):
        st.write("💡 Here's your personalized mental health recommendation:")
        def stream_answer():
            for word in final_rec["recommendation"].split(" "):
                yield word + " "
                time.sleep(0.1)
        st.write_stream(stream_answer)
    
    return final_rec
    # return {
    #     "recommendation": final_rec["recommendation"],
    #     "score_interpretation": interpretation,
    #     "condition": condition,
    #     "is_crisis": False,
    #     "crisis_explanation": explanation,
    #     # "retrieved_docs": retrieved_docs
    # }
