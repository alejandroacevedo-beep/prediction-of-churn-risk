from customer_health_platform import (
    CustomerSuccessAgent,
    LLMConfig,
    AnalysisMode,
)

__all__ = [
    "CustomerSuccessAgent",
    "LLMConfig",
    "AnalysisMode",
    "run_agent",
    "analyze_message_sentiment",
    "explain_and_plan",
    "draft_outreach_message",
]

import json
from typing import Dict, List


def analyze_message_sentiment(messages: List[Dict]) -> List[Dict]:
    agent = CustomerSuccessAgent()
    return agent.analyze_message_sentiment(messages)


def explain_and_plan(
    profile: Dict, risk_result: Dict, sentiment_messages: List[Dict]
) -> Dict:
    agent = CustomerSuccessAgent()
    return agent.explain_and_plan(profile, risk_result, sentiment_messages)


def draft_outreach_message(
    profile: Dict, risk_result: Dict, plan: Dict
) -> Dict:
    agent = CustomerSuccessAgent()
    return agent.draft_outreach_message(profile, risk_result, plan)


def run_agent(
    profile_dict: Dict,
    signals_messages: List[Dict],
    risk_result: Dict,
    include_draft: bool = True,
) -> Dict:
    agent = CustomerSuccessAgent()
    sentiment_messages = agent.analyze_message_sentiment(signals_messages)
    plan = agent.explain_and_plan(profile_dict, risk_result, sentiment_messages)

    outreach = None
    if include_draft:
        outreach = agent.draft_outreach_message(profile_dict, risk_result, plan)

    return {
        "risk_result": risk_result,
        "sentiment_messages": sentiment_messages,
        "summary": plan.get("summary"),
        "key_risks": plan.get("key_risks"),
        "priority_actions": plan.get("priority_actions"),
        "draft_outreach": outreach,
    }


if __name__ == "__main__":
    from dataclasses import asdict
    from churn_scoring import compute_churn_risk, get_demo_profile, get_demo_signals

    profile = get_demo_profile()
    signals = get_demo_signals()
    risk_result = compute_churn_risk(profile, signals)

    profile_dict = profile.to_dict()
    messages_dict = [asdict(message) for message in signals.messages]
    for message in messages_dict:
        message["sent_on"] = str(message["sent_on"])

    output = run_agent(profile_dict, messages_dict, risk_result)
    print(json.dumps(output, indent=2, default=str))
