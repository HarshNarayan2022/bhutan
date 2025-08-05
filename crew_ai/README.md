# DrukCare
A skeleton for CrewAI agents for providing mental health assistance.
## Tagline: Empowering Mental Well-being with Intelligent and Culturally Sensitive Support.

# 1. About
DrukCare AI is an intelligent chatbot application designed to provide empathetic and personalized mental health assistance, specifically tailored for the context of Bhutan. Leveraging the CrewAI framework, this system orchestrates a team of specialized AI agents to guide users through various stages of support, from crisis detection and profile collection to dynamic mental health assessments and personalized recommendations.

The project aims to offer accessible, initial mental health guidance, respecting user privacy and cultural nuances, while adhering to ethical guidelines.

# 2. Features

1. Crisis Detection: Identifies suicidal ideation or mental health emergencies.
2. Condition Classification: Detects depression, anxiety, substance use, or general mental health concerns.
3. Interactive Assessments: Conducts PHQ-9, GAD-7, and DAST-10 questionnaires and included questionnaire for alcohol use and bipolar syndrome.
4. Personalized Recommendations: Offers suggestions including helplines, therapy options, mindfullness, meditation buddha and   meditation practices.
5. RAG-Driven Retrieval: Retrieves relevant documents using a vector store (PostgreSQL pgvector) hosted on Supabase.
6. User Profile Integration: Adapts recommendations using user history and preferences.

# 3. Workflow

The DrukCare AI operates as a sequential CrewAI process, ensuring a structured and coherent user interaction flow:

1. User inputs a query.
2. Crisis detection checks for emergencies.
3. User profile is retrieved or mocked.
4. Condition classifier suggests a condition and assessment.
5. User confirms and takes the questionnaire.
6. Score is calculated and interpreted.
7. Final recommendation is generated (optionally enhanced via RAG).

![Alt text]("data\flow_chart.png" "Flow diagram")

## Crisis Detection:

Input: User's initial query.

Action: The Crisis Detection Specialist agent analyzes the input for emergency signs. Used the trained model from hugging face as a tool to detect whether the query is crisis or no-crisis.

Output: Crisis or No-crisis

## User Profile Collection:

Input: User's query and status from Crisis Detection.

Action: Queries the user profile from PostGreSQL database. 

Output: A structured user profile in json format.

## Knowledge Retrieval & Query Refinement (RAG):

Input: User's initial query and collected user profile.

Action: The Knowledge Base Manager & Query Refiner agent interprets the user's intent, formulating specific keywords for the vector database. It then retrieves relevant mental health information and identifies a potential condition (e.g., 'depression', 'anxiety').

Output: Relevant mental health recommendations and the identified condition.

## Conditional Assessment:

Input: Identified condition from mental condition classifier crew.

Action: The Mental Health Assessment Specialist agent determines if an assessment is relevant (e.g., PHQ-9 for depression, GAD-7 for anxiety). If relevant, it seeks explicit user consent. If consent is given, it administers the questionnaire step-by-step.

Output: Assessment status (completed, skipped, denied) and results (score, interpretation) if completed.

## Personalized Recommendation:

Input: Original user query, collected user profile, RAG results, and assessment results.

Action: The Personalized Recommendation Engine synthesizes all gathered information to generate highly personalized, empathetic, and actionable mental health recommendations, culturally adapted for Bhutan.

Output: The final comprehensive recommendation to the user.

# 4. Architecture/Components
The application is built using the CrewAI framework, comprising Agents, Tasks, and Tools.

## 4.1. Agents

1. **CrisisDetectionAgent:** Detects urgent crisis signals in user queries.
2. **Mental Condition Classifier Agent:** Identifies the likely mental condition.
3. **Data Retriever Agent:** Fetches user demographic and mental health background.
4. **RecommendationAgent:** Synthesizes all information and provides actionable recommendations.
5. **RAG Agent:** Retrieves external documents to augment the response context (RAG). 

## 4.2. Tasks

1. *Crisis detection task:* The crisis condition will be detected using the ‘crisis classifier tool’ . This task is performed by the Crisis Detection agent. Input will be the ‘user_query’.
2. *Mental condition classifier task:* This will classify the mental health condition from the ‘user_query’ (say anxiety, depression, substance abuse etc) and recommend the questionnaire (for example, if the detected mental health condition is ‘anxiety’, ‘GAD-7’ questionnaire is recommended to the user). This is made optional for the user. This task is performed by Mental Condition Classifier Agent.
3. *Data retriever task:* This will retrieve the user profile provided the ‘user_profile_id’ from the database. This task is performed by Data Retriever Agent. It has access to the tool to help accomplish the desired task.
4. *Rag task:* This first retrieves the keywords from the user query, refines the user query if needed and fetches the documents from the vector DB using semantic search.
5. *Recommendation task:* This is for providing a comprehensive recommendation based on the user profile, condition detected, assessment results and the retrieved documents from vector database. This also has the tool to fetch the helplines for handling crisis situations and also for severe mental health conditions. The agent performing this task is Recommendation Agent.

## 4.3. Crews

1. **Crisis_management_crew** (crisis detection agent): Runs crisis detection logic.
2. **Mental_condition_crew** (mental condition classifier agent): Classifies user's mental health condition.
3. **Data_retrieval_crew** (data retriever agent): Retrieves and formats user profile data.
4. **Recommendation_crew** (rag agent + recommendation agent): Generates final recommendations using inputs from other agents and RAG. 


## 4.4 Tools

1. *Bhutanese Helplines:* Provides a predefined list of mental health helplines relevant to Bhutan.

2. *Vector Database Operations:* Retrieval from vector database for mental health recommendations. Uses 'sentence-transformers/   all-MiniLM-L6-v2' model for embedding queries.

3. *Data Retrieval:* To fetch the user profiles from PostGreSQL database. Now it contains some dummy user profiles. The features include: age, gender, city_region, profession, marital status, previous mental diagnosis, ethnicity. 

4. *Crisis Classifier:* Uses 'sentinet/suicidality' model to detect the crisis condition. Note: lmsdmn/crisis-detection-model model has been finetuned on the specific dataset. If this model is needed to be used, we need to define a new tool for it.

# 5. Usage

1. Create a python virtual environment.

2. Install the dependencies from requirements.txt by running the below command in your terminal:

        pip install -r requirements.txt

3. Then, run the below command in your terminal: 

        python chatbot.py

The console output will show the detailed steps of how agents interact, tools are used, and the final recommendations are generated for each simulated user input.

## 5.1. LLM API Key Setup
Crucially, DrukCare AI relies on a Language Model (LLM) to function.

You need to set up your LLM provider's API key. For example, if you are using OpenAI:

1. Obtain an API key from your chosen LLM provider (e.g., OpenAI API Keys).

2. Set it as an environment variable:

    export OPENAI_API_KEY="YOUR_API_KEY_HERE" # On macOS/Linux
    Or for Windows (in Command Prompt):
        set OPENAI_API_KEY="YOUR_API_KEY_HERE"
    In PowerShell:
        $env:OPENAI_API_KEY="YOUR_API_KEY_HERE"

Alternatively, you can hardcode it in your script (for local testing, not recommended for production):

    os.environ["OPENAI_API_KEY"] = "YOUR_API_KEY_HERE"

3. Make sure your selected LLM matches the model_name you are using.

## 5.2 Setting up connection to Supabase

Setup the SUPABASE_DB_URI in your environment in .env file. SUPABASE_DB_URI can be requested from Alaa or Adelia. 

## 5.3 Langsmith setup for Tracing and Monitoring

Prerequisites:

1.	LangSmith Account and Project: Ensure you have a LangSmith account and a project where your LLM runs are being traced. Setting LANGSMITH_TRACING=true and LANGSMITH_PROJECT environment variables usually handles this.
2.	API Key: Have your LANGSMITH_API_KEY ready.
3.	LLM Provider API Key: Since your evaluator will be an LLM, you'll need the API key for the LLM provider you plan to use for the evaluation (e.g., OPENAI_API_KEY, ANTHROPIC_API_KEY). You'll need to add these as "Secrets" in LangSmith (Settings -> Secrets -> Add Secret).


# Disclaimer

This DrukCare AI chatbot is designed for informational and initial supportive purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of a qualified mental health professional for any questions you may have regarding a medical condition. If you are in a crisis situation, please contact the provided helplines immediately.

# License

Will be updated later.
