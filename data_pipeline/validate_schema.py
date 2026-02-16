from config.feature_schema import FEATURE_SCHEMA

def validate(features):
    for key, dtype in FEATURE_SCHEMA.items():
        if key not in features:
            raise ValueError(f"Missing feature: {key}")
        if not isinstance(features[key], dtype):
            raise TypeError(f"{key} must be {dtype}")

    for key in features:
        if key not in FEATURE_SCHEMA:
            raise ValueError(f"Unexpected feature: {key}")
