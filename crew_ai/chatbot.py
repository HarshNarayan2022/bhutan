import json
from dotenv import load_dotenv
from crewai import Agent, Task, Crew
from pydantic import BaseModel, Field
# from langsmith import traceable
from textwrap import dedent
from typing import Optional

# Load environment variables
load_dotenv()

# ======================= CONFIGURATION =======================
from crew_ai.tools import MentalHealthTools, QueryVectorStoreTool, DataRetrievalTool, CrisisClassifierTool, MentalConditionClassifierTool
from crew_ai.llm_setup import get_llm
from crew_ai.questionnaire import load_questionnaires, conduct_assessment
from crew_ai.config import get_config

# Load config values
config = get_config()

# LLM Initialization
llm = get_llm()

# Tool Setup
mental_health_tools = MentalHealthTools()
crisis_classifier_tool = CrisisClassifierTool()
query_vector_store = QueryVectorStoreTool()
data_retriever_tool = DataRetrievalTool()
mental_condition_classifier_tool = MentalConditionClassifierTool()

# ======================= ASSESSMENT QUESTIONNAIRES =======================
QUESTIONS = load_questionnaires()

# ======================= OUTPUT SCHEMAS =======================
class CrisisDetectionOutput(BaseModel):
    is_crisis: bool = Field(description="True if the query indicates a mental health crisis.")
    explanation: str = Field(description="Reason for classifying as crisis or not.")

class MentalConditionOutput(BaseModel):
    condition: str = Field(description="The diagnosed mental condition or concern.")
    rationale: str = Field(description="Why the classification was made.")

class DataRetrievalOutput(BaseModel):
    id: int = Field(description="User profile ID.")
    name: str = Field(description="User name")
    age: int = Field(description="User age")
    gender: str = Field(description="Gender of user")
    city_region: str = Field(description="City or region of user")
    profession: str = Field(description="Profession of user")
    marital_status: str = Field(description="Marital status of user")
    previous_mental_diagnosis: str = Field(description="Prviously diagnosed mental health conditions of user")
    ethnicity: str = Field(description="Ethnicity of user")

class RecommendationResult(BaseModel):
    recommendation: Optional[str]

# ======================= AGENT FACTORY =======================
def create_agent(role: str, goal: str, backstory: str, tools=None,**kwargs) -> Agent:
    return Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        tools=tools or [],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        **kwargs
    )

# ======================= AGENTS =======================
crisis_detection_agent = create_agent(
    "Crisis Detection Specialist",
    "Identify immediate crisis situations and escalate if needed.",
    "You are a highly empathetic and vigilant AI assistant trained to detect signs of "\
    "severe distress, suicidal ideation, or other mental health emergencies. "\
    "Your primary responsibility is to classify the query as crisis or no-crisis situation using the tool you have. "\
    "If the tool output indicates 'is_crisis=True', then it is a CRISIS situation otherwise it is NO CRISIS situation.",
    tools=[crisis_classifier_tool]
)

mental_condition_classifier_agent = create_agent(
    "Mental Health Condition Classifier",
    "Classify the user\'s mental health concern or condition, specifically aiming to identify the relevant questionnaire based on the condition detected.",
    "You are a meticulous AI specialized in understanding various mental health "\
    "states. You analyze user input and identify keywords for stress, anxiety, depression, substance abuse, bipolar, alcohol use etc. "\
    "and categorize their current concern, with a preference for matching it to a standard assessment "\
    "like PHQ-9 (depression), GAD-7 (anxiety), DAST-10 (substance abuse), AUDIT (Alcohol use) or Bipolar (bipolar syndrome) to 'General Well-being' or 'Other' using the tool you have."\
    """ **Tool Usage:**
        If the confidence score from the tool's result is greater than 0.5, only then classify the query as the condition returned from the tool. 
        Otherwise, classify the query based on your own knowledge.

        If the tool's classification is deemed unreliable (score <= 0.5), analyze the text manually based on your understanding of mental health conditions and identify relevant questionnaires:
        
        - **Depression:** PHQ-9
        - **Anxiety:** GAD-7
        - **Substance Abuse:** DAST-10
        - **Alcohol Use:** AUDIT
        - **Bipolar Syndrome:** Bipolar Disorder Assessment
        - **General Well-being:** Other mental health concerns  
    """,
    tools=[mental_condition_classifier_tool]
)

data_retriever_agent = create_agent(
    "User Profile Data Retriever",
    "Retrieve user profile details using the provided user profile ID. Use the data retrieval tool to fetch the user profile.",
    "You are responsible for fetching the user profile from the database if the user exits in the session. If the user is anonymous, then use the default user profile.",
    tools=[data_retriever_tool]
)

rag_agent = create_agent(
    "Knowledge Base Manager & Query Refiner",
    "Interpret user queries, formulate specific search terms, and manage/query the mental health knowledge base using RAG.'",
    "You are responsible for intelligently understanding user needs, even from vague inputs. "\
    "You will formulate precise search queries or identify relevant mental health keywords "\
    "before efficiently retrieving relevant information from the vector database. "\
    "You ensure that the knowledge base is always up-to-date and accessible for generating "\
    "informed recommendations, and that relevant information is always found, even for general queries.",
    tools=[query_vector_store]               # This tool performs PostgreSQL vector search
)

recommendation_agent = create_agent(
    "Personalized Recommendation Generator",
    "Provide tailored mental health recommendations based on all gathered information, including questionnaire interpretation.",
    "You are a compassionate and knowledgeable AI dedicated to offering "\
    "actionable and personalized advice. You synthesize user queries, "\
    "profile data, assessment answers, and the interpretation from assessments "\
    "to deliver helpful recommendations, including suggesting professional help when appropriate.",
    tools=[mental_health_tools.get_bhutanese_helplines],
    reasoning=True
)

# ======================= TASKS =======================
crisis_detection_task = Task(
    description="Analyze the user's current query: '{user_query}' to determine if it indicates a mental health crisis or emergency."\
        "Use the crisis detection tool to analyze the text. "\
        "Look for indicators such as: suicidal ideation, self-harm, immediate danger, severe distress, emergency situations. ",
    expected_output="Strict JSON with keys is_crisis (bool) and explanation (string). No markdown, no commentary.",
    output_json=CrisisDetectionOutput,
    input_variables=["user_query"],
    agent=crisis_detection_agent
)

mental_condition_classification_task = Task(
    description="Analyze the user's query '{user_query}' and user profile '{user_profile}' to classify their mental health condition.",
    expected_output="Strict JSON with keys condition (string) and rationale fields (string).",
    output_json=MentalConditionOutput,
    input_variables=["user_query", "user_profile"],
    agent=mental_condition_classifier_agent
)

data_retriever_task = Task(
    description="Fetch user profile data in structured JSON."\
        "Use Data Retrieval tool to retrieve the user profile information with input as '{user_profile_id}'.",
    expected_output="User demographic and background profile as Strict JSON.",
    input_variables=["user_query", "user_profile_id"],
    output_json = DataRetrievalOutput,    
    agent=data_retriever_agent
)

rag_task = Task(
    description=dedent("""
        Retrieve top 3 relevant documents for the query: '{user_query}' and condition: '{classified_condition}'
        
        Guidelines:
        1. Analyze the '{user_query}'. If it is general or vague (e.g., 'I'm feeling down', 'I need some advice'), 
            use your intelligence to formulate a more specific query or identify potential mental health keywords 
            (e.g., 'stress', 'anxiety', 'depression', 'general well-being') that reflect the user's potential 
            underlying condition. Prioritize keywords present in the vector database's . If the query is already specific, use it directly.
        2. The output should be relevant information blocks from the knowledge base.
            based on the refined query.
    """),
    expected_output="A JSON object with a list of relevant texts under key 'docs'",
    input_variables=["user_query", "classified_condition"],
    agent=rag_agent
)

recommendation_task = Task(
    description=dedent("""
        Generate comprehensive, personalized mental health recommendations based on all available information:
        - User query: '{user_query}'
        - User profile: '{user_profile}'
        - Identified condition: '{classified_condition}'
        - Assessment results: '{assessment_answers}' with interpretation: '{interpretation}'
        - Crisis status: '{is_crisis}'
    
    
        Guidelines:
        1. Provide culturally sensitive recommendations aligned with Bhutanese values and Gross National Happiness principles.
        2. Include actionable, practical steps the user can take.
        3. Consider the user's specific profile (age, background, history).
        4. Summarize the retrieved documents in your context.
        4. Use this summary to support your recommendation. Reference specific sources used from your context'.
        6. If assessment was completed, incorporate the interpretation. DO NOT reveal the assessment results to the user.
        7. For crisis situations, prioritize immediate safety and professional help.
        8. Use compassionate, encouraging language.
        9. Suggest community resources, traditional practices, and professional help as appropriate.
        10. Only provide helplines when specifically needed for crisis situations.
        
        Structure your response as a comprehensive recommendation that addresses the user's specific needs.
    """),
    expected_output="A comprehensive, personalized, and empathetic mental health recommendation tailored to the user's specific situation.",
    agent=recommendation_agent,
    context=[rag_task],
    output_json=RecommendationResult,
    input_variables=["user_query", "user_profile","classified_condition", "assessment_answers", "interpretation", "is_crisis"],
)

# ======================= CREWS =======================
crisis_management_crew = Crew(agents=[crisis_detection_agent], tasks=[crisis_detection_task], verbose=True)
mental_condition_crew = Crew(agents=[mental_condition_classifier_agent], tasks=[mental_condition_classification_task], verbose=True)
data_retrieval_crew = Crew(agents=[data_retriever_agent], tasks=[data_retriever_task], verbose=True)
recommendation_crew = Crew(agents=[rag_agent, recommendation_agent], tasks=[rag_task, recommendation_task], full_output=True, output_log_file=True, verbose=True)

# ======================= EXPORTABLE API =======================
def run_crisis_check(user_query: str) -> dict:
    result = crisis_management_crew.kickoff({"user_query": user_query})
    return result.json_dict

def run_condition_classification(user_query: str, user_profile: str) -> dict:
    condition_result = mental_condition_crew.kickoff({
        "user_query": user_query,
        "user_profile": user_profile
    })
    return condition_result.json_dict

def run_user_profile_retrieval(user_query: str, user_profile_id: str) -> dict:
    data_result = data_retrieval_crew.kickoff({
        "user_query": user_query,
        "user_profile_id": user_profile_id
    })
    return data_result.json_dict

def run_recommendations(user_query: str, user_profile: str, condition: str, answers: str, interpretation: str, is_crisis: str):
    recommendation_result = recommendation_crew.kickoff({
        "user_query": user_query,
        "user_profile": user_profile,
        "classified_condition": condition,
        "assessment_answers": answers,
        "interpretation": interpretation,
        "is_crisis": is_crisis
    })
    return recommendation_result.json_dict

# ======================= FULL CHAT FLOW =======================
# @traceable(name= "Druckare Chatbot full flow")
def full_chat_flow(user_query: str, user_id: str = "anon_user"):
    print("📄 Fetching user profile...")
    dummy_profile = {
        "id": user_id,
        "age": "",
        "location": "",
        "history": "",
        "preferences": "Prefers meditation"
    }

    print("🔍 Checking for crisis...")
    crisis_result = run_crisis_check(user_query)
    print("📦 Crew result:", crisis_result)

    is_crisis = crisis_result.get("is_crisis", False)
    explanation = crisis_result.get("explanation", "")

    if is_crisis:
        print(f"🚨 Crisis Detected: {explanation}")
        rec = run_recommendations(
            user_query, 
            user_profile=json.dumps(dummy_profile), 
            condition="Crisis", 
            answers="{}", 
            interpretation="N/A", 
            is_crisis="true"
        )
        # task_outputs = rec.tasks_output
        # retrieved_docs_crisis = task_outputs[0]

        print("\n🆘 Crisis Support Recommendation:\n", rec)
        return {
            "recommendation": rec["recommendation"],
            "score_interpretation": interpretation,
            "condition": condition,
            "is_crisis": is_crisis,
            "crisis_explanation": explanation,
            # "retrieved_docs": retrieved_docs_crisis
        }
    else:
        print("No crisis detected")

    print("🔎 Classifying condition...")
    condition_result = run_condition_classification(user_query, json.dumps(dummy_profile))
    condition = condition_result.get("condition").lower()
    questionnaire_name = config["CONDITION_TO_QUESTIONNAIRE"].get(condition)

    print(f"🧠 Detected condition: {condition}")
    if questionnaire_name not in QUESTIONS:
        print("Skipping assessment as condition is general or unknown.")
        score = "N/A"
        answers = {}
        interpretation = "Not applicable"
    else:
        # Ask for user confirmation 
        confirm = input(f"👉 We recommend a brief '{questionnaire_name}' assessment (e.g., {condition.upper()} questionnaire). Do you want to proceed? (yes/no): ").strip().lower()

        if confirm != 'yes':
            print("🚫 Assessment skipped by user.")
            score = 'N/A'
            answers = {}
            interpretation = "User chose not to proceed with the assessment."
        else:
            # Show instructions
            print("\n📝 Instructions:")
            print("You will now be presented with a few questions related to your mental health condition.")
            if questionnaire_name in ["PHQ-9", "GAD-7"]:
                print("Please answer each question honestly, based on how you've felt over the **last 2 weeks**.")
                print("Use the following scale to respond:")
                print("  0 - Not at all")
                print("  1 - Several days")
                print("  2 - More than half the days")
                print("  3 - Nearly every day")
            elif questionnaire_name == "DAST-10":
                print("Answer each question with Yes or No based on your past year's experience.")
            elif questionnaire_name == "AUDIT":
                print("Answer using options like: Never, 1-2, 3-4, Weekly, Yes, No, etc., as applicable.")
            elif questionnaire_name == "Bipolar":
                print("Answer each question with Yes or No based on your past mood and energy patterns.")
            
            input("\nPress Enter to begin the questionnaire...")

            # Proceed with assessment
            assessment = conduct_assessment(questionnaire_name)
            answers = assessment["answers"]
            score = assessment["score"]
            interpretation = assessment["interpretation"]
    
    print("💡 Generating recommendations...")
    final_rec = run_recommendations(
        user_query,
        json.dumps(dummy_profile),
        condition,
        json.dumps(answers),
        interpretation,
        is_crisis="false"
    )

    # task_outputs = final_rec.tasks_output
    # retrieved_docs = task_outputs[0]
    
    return {
        "recommendation": final_rec["recommendation"],
        "score_interpretation": interpretation,
        "condition": condition,
        "is_crisis": is_crisis,
        "crisis_explanation": explanation,
    #     "retrieved_docs": retrieved_docs
    }


if __name__ == "__main__":
    query = input("👤 Enter your mental health query: ")
    final_output = full_chat_flow(query)
    print("Final Output:\n", final_output)

