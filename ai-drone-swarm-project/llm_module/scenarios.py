"""
Shared test/evaluation scenarios.
Responsible: Member 3

Each scenario has a drone message, optional recent swarm messages (context),
and a hand-written expectation:
    risk:    acceptable risk levels
    actions: acceptable actions
These expectations are what a sensible operator would want, NOT what the
rules happen to output, so they can also measure the rule engine.
"""

T = "2026-01-15T12:30:{:02d}Z"


def msg(drone, obj, dist, direction, conf, loc=(34.5000, -118.2000, 15.0), sec=0):
    return {
        "drone_id": drone, "timestamp": T.format(sec), "object": obj,
        "distance": dist, "direction": direction, "confidence": conf, "location": list(loc),
    }


SCENARIOS = [
    # --- Imminent collisions -------------------------------------------------
    {"name": "tree_very_close", "message": msg("drone_1", "tree", 8, "front", 0.89),
     "expect": {"risk": ["high"], "actions": ["avoid_obstacle"]}},
    {"name": "building_close", "message": msg("drone_1", "building", 6, "front", 0.95),
     "expect": {"risk": ["high"], "actions": ["avoid_obstacle"]}},
    {"name": "bird_close_low_conf", "message": msg("drone_2", "bird", 4, "above", 0.35),
     "expect": {"risk": ["high"], "actions": ["avoid_obstacle"]}},
    {"name": "fire_close", "message": msg("drone_3", "fire", 9, "below", 0.90),
     "expect": {"risk": ["high"], "actions": ["avoid_obstacle"]}},

    # --- Hazards ---------------------------------------------------------------
    {"name": "smoke_far", "message": msg("drone_3", "smoke", 40, "right", 0.80),
     "expect": {"risk": ["high"], "actions": ["notify_swarm", "hover_and_monitor"]}},
    {"name": "fire_far_confident", "message": msg("drone_2", "fire", 60, "left", 0.93),
     "expect": {"risk": ["high"], "actions": ["notify_swarm", "hover_and_monitor"]}},
    {"name": "smoke_uncertain", "message": msg("drone_1", "smoke", 50, "front", 0.55),
     "expect": {"risk": ["medium", "high"], "actions": ["investigate", "hover_and_monitor", "notify_swarm"]}},
    {"name": "fire_very_low_conf", "message": msg("drone_4", "fire", 70, "right", 0.20),
     "expect": {"risk": ["low", "medium"], "actions": ["continue_mission", "investigate"]}},

    # --- People ----------------------------------------------------------------
    {"name": "person_far", "message": msg("drone_2", "person", 25, "left", 0.92),
     "expect": {"risk": ["medium"], "actions": ["notify_swarm", "hover_and_monitor"]}},
    {"name": "person_uncertain", "message": msg("drone_4", "person", 35, "back", 0.50),
     "expect": {"risk": ["low", "medium"], "actions": ["investigate", "hover_and_monitor"]}},

    # --- Obstacles at safe distance --------------------------------------------
    {"name": "car_mid", "message": msg("drone_1", "car", 20, "right", 0.85),
     "expect": {"risk": ["low", "medium"], "actions": ["adjust_course", "continue_mission"]}},
    {"name": "truck_far", "message": msg("drone_2", "truck", 80, "front", 0.77),
     "expect": {"risk": ["low"], "actions": ["adjust_course", "continue_mission"]}},
    {"name": "tree_mid", "message": msg("drone_3", "tree", 18, "front", 0.88),
     "expect": {"risk": ["medium"], "actions": ["adjust_course"]}},

    # --- Nothing important / bad input -----------------------------------------
    {"name": "unknown_far", "message": msg("drone_1", "unknown", 100, "front", 0.30),
     "expect": {"risk": ["low"], "actions": ["continue_mission"]}},
    {"name": "missing_fields", "message": {"drone_id": "drone_5", "object": "car"},
     "expect": {"risk": ["low", "medium"], "actions": ["continue_mission", "adjust_course", "investigate"]}},
    {"name": "broken_values", "message": {"drone_id": "drone_5", "object": None, "distance": "far",
                                          "direction": None, "confidence": "high"},
     "expect": {"risk": ["low", "medium"], "actions": ["continue_mission", "investigate"]}},

    # --- Swarm context: other drones' reports should matter ---------------------
    {"name": "smoke_confirmed_by_swarm",
     "message": msg("drone_1", "smoke", 45, "front", 0.55, loc=(34.5000, -118.2000, 15.0), sec=30),
     "context": [msg("drone_2", "smoke", 30, "left", 0.85, loc=(34.5003, -118.2002, 15.0), sec=20),
                 msg("drone_3", "fire", 50, "right", 0.80, loc=(34.5005, -118.1998, 15.0), sec=25)],
     "expect": {"risk": ["high"], "actions": ["notify_swarm", "hover_and_monitor"]}},
    {"name": "person_seen_by_many",
     "message": msg("drone_4", "person", 40, "left", 0.60, loc=(34.5010, -118.2010, 20.0), sec=40),
     "context": [msg("drone_1", "person", 30, "front", 0.90, loc=(34.5011, -118.2008, 20.0), sec=35),
                 msg("drone_2", "person", 35, "right", 0.88, loc=(34.5009, -118.2012, 20.0), sec=38)],
     "expect": {"risk": ["medium", "high"], "actions": ["notify_swarm", "hover_and_monitor"]}},
    {"name": "unrelated_swarm_reports",
     "message": msg("drone_1", "car", 70, "back", 0.80, sec=50),
     "context": [msg("drone_2", "tree", 30, "front", 0.90, sec=45),
                 msg("drone_3", "building", 60, "left", 0.85, sec=48)],
     "expect": {"risk": ["low"], "actions": ["adjust_course", "continue_mission"]}},
]
