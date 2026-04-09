from config import THRESHOLDS

def classify_event(sensor_type, value):
    threshold = THRESHOLDS.get(sensor_type)

    if sensor_type == "proximity":
        if value == 1:
            return "CRITICAL", "Restricted zone breach detected"
        return "LOW", "No intrusion detected"

    if threshold is None:
        return "LOW", "Unknown sensor type"

    if value >= threshold * 1.20:
        return "CRITICAL", f"{sensor_type} at critical level"
    if value >= threshold:
        return "HIGH", f"{sensor_type} crossed threshold"
    if value >= threshold * 0.80:
        return "MEDIUM", f"{sensor_type} approaching threshold"
    return "LOW", f"{sensor_type} within safe range"