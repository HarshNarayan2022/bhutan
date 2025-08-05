# modules/questionnaire.py
import json
from typing import Dict, Any

# Path to your questionnaire file
QUESTIONNAIRES_FILE = "crew_ai/questionnaire.json"

def load_questionnaires() -> Dict[str, Any]:
    """Load questionnaires from a file or fallback to defaults."""
    try:
        with open(QUESTIONNAIRES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"⚠️ Could not load {QUESTIONNAIRES_FILE}. Using default questions.")
        return create_default_questionnaires()

def create_default_questionnaires() -> Dict[str, Any]:
    """Default fallback questions."""
    return {
        "PHQ-9": [
            "Over the last 2 weeks, how often have you been bothered by any of the following problems? (0-3)",
            "Little interest or pleasure in doing things",
            "Feeling down, depressed, or hopeless",
            "Trouble falling asleep or sleeping too much",
            "Feeling tired or having little energy",
            "Poor appetite or overeating",
            "Feeling bad about yourself",
            "Trouble concentrating",
            "Moving/speaking slowly or being fidgety",
            "Thoughts of self-harm or death"
        ],
        "GAD-7": [
            "Over the last 2 weeks, how often have you been bothered by the following problems? (0-3)",
            "Feeling nervous or on edge",
            "Not being able to stop worrying",
            "Worrying too much",
            "Trouble relaxing",
            "Restlessness",
            "Irritability",
            "Feeling something awful might happen"
        ],
        "DAST-10": [
            "The following questions are about drug use in the past year. Answer Yes or No.",
            "Used drugs not prescribed?",
            "Abused more than one drug at once?",
            "Tried and failed to stop using?",
            "Experienced blackouts or flashbacks?",
            "Felt guilty about drug use?",
            "Had family complain about your use?",
            "Neglected responsibilities?",
            "Committed illegal acts for drugs?",
            "Had withdrawal symptoms?",
            "Had medical problems due to use?"
        ],
        "AUDIT": [
            "Please answer the following questions based on your alcohol use over the past 12 months.",
            "1. How often do you have a drink containing alcohol? (0) Never [Skip to Q9-10], (1) Monthly or less, (2) 2 to 4 times a month, (3) 2 to 3 times a week, (4) 4 or more times a week",
            "2. How many drinks containing alcohol do you have on a typical day when you are drinking? (0) 1 or 2, (1) 3 or 4, (2) 5 or 6, (3) 7, 8, or 9, (4) 10 or more",
            "3. How often do you have six or more drinks on one occasion? (0) Never, (1) Less than monthly, (2) Monthly, (3) Weekly, (4) Daily or almost daily",
            "4. How often during the last year have you found that you were not able to stop drinking once you had started? (0–4 scale as above)",
            "5. How often during the last year have you failed to do what was normally expected from you because of drinking? (0–4 scale as above)",
            "6. How often during the last year have you needed a first drink in the morning to get yourself going after a heavy drinking session? (0–4 scale as above)",
            "7. How often during the last year have you had a feeling of guilt or remorse after drinking? (0–4 scale as above)",
            "8. How often during the last year have you been unable to remember what happened the night before because you had been drinking? (0–4 scale as above)",
            "9. Have you or someone else been injured as a result of your drinking? (0) No, (2) Yes, but not in the last year, (4) Yes, during the last year",
            "10. Has a relative or friend or a doctor or another health worker been concerned about your drinking or suggested you cut down? (0) No, (2) Yes, but not in the last year, (4) Yes, during the last year"
        ],
        "Bipolar": [
            "Have there ever been times when you were not your usual self and...",
            "1. You felt so good or hyper that others thought you were not your normal self or that you got into trouble?",
            "2. You were so irritable that you shouted at people or started arguments?",
            "3. You felt much more self-confident than usual?",
            "4. You got much less sleep than usual and didn’t really miss it?",
            "5. You were much more talkative or spoke faster than usual?",
            "6. You had racing thoughts?",
            "7. You were easily distracted?",
            "8. You were more active or did more things than usual?",
            "9. You were much more social or outgoing than usual?",
            "10. You did risky things that could have caused trouble?",
            "11. Spending money got you or your family into trouble?"
        ]
    }

def conduct_assessment(condition: str) -> Dict[str, Any]:
    """Run questionnaire and return answers, score, and interpretation."""
    questions = load_questionnaires().get(condition, [])
    if not questions:
        return {"answers": {}, "score": "N/A", "interpretation": "No questions found."}

    print(f"\n📝 Starting {condition} assessment:\n")
    answers = {}
    for i, q in enumerate(questions[1:], 1):  # skip instructions
        user_input = input(f"Q{i}. {q} ").strip().lower()
        answers[q] = user_input

    score = score_questionnaire(condition, answers)
    interpretation = interpret_score(condition, score)

    return {
        "answers": answers,
        "score": score,
        "interpretation": interpretation
    }

def score_questionnaire(condition: str, answers: Dict[str, str]) -> int:
    """Score PHQ-9, GAD-7, DAST-10 , Bipolar and AUDIT answers."""
    score = 0
    if condition in ["PHQ-9", "GAD-7"]:
        scale = {
            "0": 0, "not at all": 0,
            "1": 1, "several days": 1,
            "2": 2, "more than half the days": 2,
            "3": 3, "nearly every day": 3
        }
        for ans in answers.values():
            cleaned = ans.strip().lower()
            if '-' in cleaned:
                cleaned = cleaned.split("-", 1)[-1].strip()
            score += scale.get(cleaned, 0)
            
    elif condition == "DAST-10":
        for ans in answers.values():
            score += 1 if ans.lower() in ["yes", "y", "true", "1"] else 0

    elif condition == "AUDIT":
        score = 0
        question_keys = [f"Q{i}" for i in range(1,11)]
        skip_to_end = False

        scale_0_to_4 = {
            "never": 0,
            "monthly or less": 1,
            "less than monthly": 1,
            "2 to 4 times a month": 2,
            "5 or 6": 2,
            "monthly": 2,
            "2 to 3 times a week": 3,
            "7, 8, or 9": 3,
            "weekly": 3,
            "4 or more times a week": 4,
            "10 or more": 4,
            "daily or almost daily": 4,
            "1 or 2": 0,
            "3 or 4": 1  
        }

        scale_0_2_4 = {
            "no": 0,
            "yes, but not in the last year": 2,
            "yes, during the last year": 4
        }

        # === Q1 logic (skip if "never") ===
        ans = answers.get("Q1", "").strip().lower()
        print("Answer to Q1:", ans)
        # ans1_clean = ans1_raw.replace("(", "").replace(")", "").replace(",", "").strip()
        if ans == "never":
            skip_to_end = True
            score += 0
        else:
            for key in scale_0_to_4:
                if key in ans:
                    score += scale_0_to_4[key]
                    break

        if skip_to_end:
            for qkey in ["Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8"]:
                answers[qkey] = "Skipped"
            # Score Q9 and Q10 only
            for qkey in ["Q9", "Q10"]:  # Q9, Q10
                ans = answers.get(qkey, "").strip().lower()
                # ans = ans.replace("(", "").replace(")", "").replace(",", "").strip()
                for key in scale_0_2_4:
                    if key in ans:
                        score += scale_0_2_4[key]
                        break
            return score

        # Continue with Q2–Q8
        for qkey in question_keys[1:8]:  # Q2 to Q8
            ans = answers.get(qkey, "").strip().lower()
            # ans = ans.replace("(", "").replace(")", "").replace(",", "").strip()
            for key in scale_0_to_4:
                if key in ans:
                    score += scale_0_to_4[key]
                    break

        # Score Q9, Q10
        for qkey in ["Q9","Q10"]:
            ans = answers.get(qkey, "").strip().lower()
            # ans = ans.replace("(", "").replace(")", "").replace(",", "").strip()
            for key in scale_0_2_4:
                if key in ans:
                    score += scale_0_2_4[key]
                    break

        return score

    elif condition == "Bipolar":
        for ans in answers.values():
            score += 1 if ans.strip().lower() in ["yes", "y", "true", "1"] else 0

    return score

def interpret_score(condition: str, score: int) -> str:
    """Interpret the score based on condition."""
    if condition == "PHQ-9":
        if score <= 4: return "Minimal depression"
        elif score <= 9: return "Mild depression"
        elif score <= 14: return "Moderate depression"
        elif score <= 19: return "Moderately severe depression"
        return "Severe depression"

    if condition == "GAD-7":
        if score <= 4: return "Minimal anxiety"
        elif score <= 9: return "Mild anxiety"
        elif score <= 14: return "Moderate anxiety"
        return "Severe anxiety"

    if condition == "DAST-10":
        if score == 0: return "No problems reported"
        elif score <= 2: return "Low level of problems"
        elif score <= 5: return "Moderate problems"
        elif score <= 8: return "Substantial problems"
        return "Severe problems"
    
    if condition == "AUDIT":
        if score <= 7: return "Lower risk, usually no action needed."
        elif score >= 8 and score <= 14: return "Hazardous or harmful alcohol use. Brief advice or counseling may be appropriate."
        elif score >= 15 and score <= 19: return "Harmful alcohol use. Brief counseling and continued monitoring recommended."
        elif score >= 20: return "Likely alcohol dependence. Referral for specialist assessment and treatment is recommended."
        else:
            return "Score out of typical AUDIT range."

    if condition == "Bipolar":
        if score >= 7: return "Likely signs of bipolar disorder"
        return "Unlikely bipolar symptoms"


    return "Score interpreted"

def calculate_phq9_score(responses):
    """Calculate PHQ-9 depression score from responses"""
    if len(responses) != 9:
        return {"score": 0, "severity": "Invalid", "risk": "Low"}
    
    score = sum(responses)
    
    if score <= 4:
        severity = "Minimal depression"
        risk = "Low"
    elif score <= 9:
        severity = "Mild depression"
        risk = "Low"
    elif score <= 14:
        severity = "Moderate depression"
        risk = "Moderate"
    elif score <= 19:
        severity = "Moderately severe depression"
        risk = "High"
    else:
        severity = "Severe depression"
        risk = "High"
    
    # Check for suicidal ideation (question 9)
    if responses[8] > 0:
        risk = "High"
        severity += " (with suicidal ideation)"
    
    return {
        "score": score,
        "severity": severity,
        "risk": risk,
        "max_score": 27
    }

def calculate_gad7_score(responses):
    """Calculate GAD-7 anxiety score from responses"""
    if len(responses) != 7:
        return {"score": 0, "severity": "Invalid", "risk": "Low"}
    
    score = sum(responses)
    
    if score <= 4:
        severity = "Minimal anxiety"
        risk = "Low"
    elif score <= 9:
        severity = "Mild anxiety"
        risk = "Low"
    elif score <= 14:
        severity = "Moderate anxiety"
        risk = "Moderate"
    else:
        severity = "Severe anxiety"
        risk = "High"
    
    return {
        "score": score,
        "severity": severity,
        "risk": risk,
        "max_score": 21
    }

def calculate_dast10_score(responses):
    """Calculate DAST-10 substance use score from responses"""
    if len(responses) != 10:
        return {"score": 0, "severity": "Invalid", "risk": "Low"}
    
    score = sum(responses)
    
    if score == 0:
        severity = "No problems reported"
        risk = "Low"
    elif score <= 2:
        severity = "Low level of problems"
        risk = "Low"
    elif score <= 5:
        severity = "Moderate problems"
        risk = "Moderate"
    elif score <= 8:
        severity = "Substantial problems"
        risk = "High"
    else:
        severity = "Severe problems"
        risk = "High"
    
    return {
        "score": score,
        "severity": severity,
        "risk": risk,
        "max_score": 10
    }

def calculate_audit_score(responses):
    """Calculate AUDIT alcohol use score from responses"""
    if len(responses) != 10:
        return {"score": 0, "severity": "Invalid", "risk": "Low"}
    
    score = sum(responses)
    
    if score <= 7:
        severity = "Lower risk"
        risk = "Low"
        recommendation = "No action needed"
    elif score <= 14:
        severity = "Hazardous or harmful alcohol use"
        risk = "Moderate"
        recommendation = "Brief advice or counseling may be appropriate"
    elif score <= 19:
        severity = "Harmful alcohol use"
        risk = "High"
        recommendation = "Brief counseling and continued monitoring recommended"
    else:
        severity = "Likely alcohol dependence"
        risk = "High"
        recommendation = "Referral for specialist assessment and treatment recommended"
    
    return {
        "score": score,
        "severity": severity,
        "risk": risk,
        "recommendation": recommendation,
        "max_score": 40
    }

def calculate_bipolar_score(responses):
    """Calculate Bipolar screening score from responses"""
    if len(responses) != 11:
        return {"score": 0, "severity": "Invalid", "risk": "Low"}
    
    score = sum(responses)
    
    if score >= 7:
        severity = "Likely signs of bipolar disorder"
        risk = "High"
        recommendation = "Further assessment recommended"
    else:
        severity = "Unlikely bipolar symptoms"
        risk = "Low"
        recommendation = "No immediate concerns"
    
    return {
        "score": score,
        "severity": severity,
        "risk": risk,
        "recommendation": recommendation,
        "max_score": 11
    }

def get_assessment_recommendations(scores):
    """Generate overall assessment recommendations based on all scores"""
    high_risk_areas = []
    moderate_risk_areas = []
    recommendations = []
    
    # Analyze each domain
    for domain, result in scores.items():
        if isinstance(result, dict) and 'risk' in result:
            if result['risk'] == 'High':
                high_risk_areas.append(domain.upper())
            elif result['risk'] == 'Moderate':
                moderate_risk_areas.append(domain.upper())
    
    # Overall status
    if high_risk_areas:
        overall_status = "High Risk - Professional Support Recommended"
        recommendations.append("We strongly recommend consulting with a mental health professional")
        recommendations.append("Consider scheduling an appointment with your doctor or a counselor")
    elif moderate_risk_areas:
        overall_status = "Moderate Risk - Consider Professional Guidance"
        recommendations.append("Consider speaking with a counselor or mental health professional")
        recommendations.append("Monitor your symptoms and seek help if they worsen")
    else:
        overall_status = "Low Risk - Continue Self-Care"
        recommendations.append("Continue practicing good mental health habits")
        recommendations.append("Stay connected with supportive friends and family")
    
    # Specific recommendations
    if 'phq9' in scores and scores['phq9'].get('risk') == 'High':
        recommendations.append("For depression: Consider therapy, medication evaluation, or support groups")
        
    if 'gad7' in scores and scores['gad7'].get('risk') == 'High':
        recommendations.append("For anxiety: Practice relaxation techniques, consider counseling")
        
    if 'dast10' in scores and scores['dast10'].get('risk') in ['High', 'Moderate']:
        recommendations.append("For substance use: Consider addiction counseling or support programs")
        
    if 'audit' in scores and scores['audit'].get('risk') in ['High', 'Moderate']:
        recommendations.append("For alcohol use: Consider reducing consumption or seeking guidance")
        
    if 'bipolar' in scores and scores['bipolar'].get('risk') == 'High':
        recommendations.append("For mood symptoms: Psychiatric evaluation recommended")
    
    # Emergency recommendations
    if 'phq9' in scores and len(scores['phq9'].get('severity', '').split('suicidal')) > 1:
        recommendations.insert(0, "🚨 IMMEDIATE: If you're having thoughts of self-harm, please contact emergency services (112/110) or the National Mental Health Helpline (1717)")
    
    return {
        "overall_status": overall_status,
        "high_risk_areas": high_risk_areas,
        "moderate_risk_areas": moderate_risk_areas,
        "recommendations": recommendations,
        "summary": f"Assessment completed. Areas of concern: {', '.join(high_risk_areas + moderate_risk_areas) if high_risk_areas or moderate_risk_areas else 'None identified'}"
    }
