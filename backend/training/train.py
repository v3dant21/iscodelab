import json
from pathlib import Path
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split

random = np.random.default_rng(42)
features = np.column_stack([random.integers(1, 6, 2400), random.integers(1, 15, 2400), random.integers(5, 100, 2400), random.integers(0, 20, 2400), random.integers(0, 2, 2400), random.integers(15, 30, 2400)])
targets = features @ np.array([0.8, 1.2, 0.08, 1.8, 4.0, 0.8]) + 3 + random.normal(0, 3, 2400)
train_x, test_x, train_y, test_y = train_test_split(features, targets, random_state=42)
model = Ridge(alpha=1).fit(train_x, train_y)
artifact = {'intercept': float(model.intercept_), 'coefficients': model.coef_.tolist(), 'synthetic_mae_minutes': float(mean_absolute_error(test_y, model.predict(test_x))), 'seed': 42, 'samples': 2400, 'notice': 'Synthetic data only. Not validated in a real kitchen.'}
Path(__file__).with_name('model.json').write_text(json.dumps(artifact, indent=2) + '\n')
print(artifact)
