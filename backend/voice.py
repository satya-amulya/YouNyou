import agents

EMOTION_VOICE_PARAMS = {
    "proud":      {"pitch": 1.1, "rate": 1.0, "volume": 1.0, "pause_before": 0},
    "thrilled":   {"pitch": 1.2, "rate": 1.05, "volume": 1.0, "pause_before": 0},
    "hopeful":    {"pitch": 1.05, "rate": 0.95, "volume": 0.9, "pause_before": 200},
    "determined": {"pitch": 1.0, "rate": 0.98, "volume": 1.0, "pause_before": 300},
    "anxious":    {"pitch": 0.95, "rate": 1.1, "volume": 0.95, "pause_before": 0},
    "stressed":   {"pitch": 0.9, "rate": 1.15, "volume": 1.0, "pause_before": 0},
    "regretful":  {"pitch": 0.85, "rate": 0.88, "volume": 0.85, "pause_before": 500},
    "neutral":    {"pitch": 1.0, "rate": 1.0, "volume": 0.9, "pause_before": 0},
}

def build_voice_event(event_type: str, context: dict, mood: str) -> dict:
    scripts = {
        "task_done_fast": f"They just finished '{context.get('task')}' faster than planned.",
        "task_done_slow": f"They finished '{context.get('task')}' but took longer than estimated.",
        "task_missed": f"They did NOT complete '{context.get('task')}' today.",
        "deadline_passed": f"The goal '{context.get('goal')}' deadline has passed.",
        "daily_morning": f"Morning check-in for '{context.get('goal')}'.",
    }

    prompt = scripts.get(event_type, "Say something encouraging.")
    script = agents._call(prompt)  # uses whichever agents.py is active (mock or real)

    params = EMOTION_VOICE_PARAMS.get(mood, EMOTION_VOICE_PARAMS["neutral"])

    return {
        "script": script,
        "mood": mood,
        "voice_params": params,
        "event_type": event_type,
    }