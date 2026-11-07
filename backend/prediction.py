import json
import math
from pathlib import Path

MODEL_PATH = Path(__file__).parent / 'training' / 'model.json'


# Bounds of the synthetic training set. Outside them, extrapolation alone is unsafe.
TRAINING_BOUNDS = [(1, 5), (1, 14), (5, 99), (0, 19), (0, 1), (15, 29)]


def observed_floor(durations):
    """Conservative observed p90, not a calibrated probability/confidence claim.

    Require 20 recent valid measurements; never invent history or lower a promise.
    """
    valid = sorted(value for value in durations if math.isfinite(value) and value > 0)
    return math.ceil(valid[math.ceil(len(valid) * .9) - 1]) if len(valid) >= 20 else None


def predict(lines, queue, minimum, peak):
    portions = sum(line['quantity'] for line in lines)
    weight = sum(line['weight'] * line['quantity'] for line in lines)
    features = [len(lines), portions, weight, queue, int(peak), minimum]
    fallback = minimum + portions * 2 + queue * 3
    try:
        model = json.loads(MODEL_PATH.read_text())
        if not isinstance(model, dict):
            raise ValueError('Invalid model')
        coefficients = model['coefficients']
        if not isinstance(coefficients, list) or len(coefficients) != len(features):
            raise ValueError('Feature mismatch')
        if any(type(value) not in (int, float) or not math.isfinite(value) for value in [model['intercept'], *coefficients]):
            raise ValueError('Invalid model parameters')
        if any(value < 0 for value in coefficients):
            raise ValueError('More kitchen work must not reduce the estimate')
        estimate = model['intercept'] + sum(value * coefficient for value, coefficient in zip(features, coefficients))
        if not math.isfinite(estimate):
            raise ValueError('Invalid prediction')
        if estimate <= 0:
            raise ValueError('Invalid prediction')
        source = 'synthetic regression'
        if any(not low <= value <= high for value, (low, high) in zip(features, TRAINING_BOUNDS)):
            estimate = max(estimate, fallback)
            source = 'synthetic regression; outside training range, queue safeguard'
    except (OSError, ValueError, KeyError, TypeError, OverflowError):
        estimate = fallback
        source = 'queue fallback'
    return max(minimum, math.ceil(estimate)), source
