import numpy as np

def fuzzify_distance(x):
    """
    Fuzzify the input relative distance (0–100%).
    Membership sets: low, average, high.
    Returns: a dictionary with degrees of membership.
    Example: {"low": 0.7, "average": 0.3, "high": 0.0}
    """
    return {}

def fuzzify_speed(x):
    """
    Fuzzify the input speed (0–30).
    Membership sets: low, high.
    Returns: a dictionary with degrees of membership.
    Example: {"low": 0.2, "high": 0.8}
    """
    return {}

def apply_rules(distance, speed):
    """
    Apply fuzzy rules based on fuzzified distance and speed.
    Rules:
      1. If distance is low OR speed is high → hard brake
      2. If distance is high → mild brake
      3. If distance is average AND speed is high → controlled brake
      4. If distance is average AND speed is low → mild brake
    Returns: a dictionary with rule strengths.
    Example: {"mild": 0.4, "controlled": 0.2, "hard": 0.7}
    """
    return {}

def defuzzify(rules, step=2):
    """
    Perform defuzzification (e.g., centroid method).
    Input: dictionary of aggregated rule strengths.
    Returns: a crisp braking value between 0–100%.
    """
    return 0

def braking_system(distance_input, speed_input):
    """
    Main function that ties everything together.
    1. Fuzzify distance and speed.
    2. Apply fuzzy rules.
    3. Defuzzify results.
    Prints and returns the final braking percentage.
    """
    distance_mf = fuzzify_distance(distance_input)
    speed_mf = fuzzify_speed(speed_input)
    rules = apply_rules(distance_mf, speed_mf)
    brake_val = defuzzify(rules)
    print(f"Distance={distance_input}, Speed={speed_input} → Brake={brake_val:.2f}%")
    print("Distance MFs:", distance_mf)
    print("Speed MFs:", speed_mf)
    print("Rule strengths:", rules)

# Example test call
braking_system(25, 20)
