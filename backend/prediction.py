import json
import math
from pathlib import Path

MODEL_PATH = Path(__file__).parent / 'training' / 'model.json'


def predict(lines, queue, minimum, peak):
    portions = sum(line['quantity'] for line in lines)
    weight = sum(line['weight'] * line['quantity'] for line in lines)
    features = [len(lines), portions, weight, queue, int(peak), minimum]
    try:
        model = json.loads(MODEL_PATH.read_text())
        coefficients = model['coefficients']
        if len(coefficients) != len(features):
            raise ValueError('Feature mismatch')
        estimate = model['intercept'] + sum(value * coefficient for value, coefficient in zip(features, coefficients))
        if not math.isfinite(estimate):
            raise ValueError('Invalid prediction')
        source = 'synthetic regression'
    except (OSError, ValueError, KeyError, TypeError):
        estimate = minimum + portions * 2 + queue * 3
        source = 'queue fallback'
    return max(minimum, min(120, math.ceil(estimate))), source
