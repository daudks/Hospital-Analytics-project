# create_dummy_model.py
from sklearn.ensemble import RandomForestClassifier
import numpy as np
import joblib

# Dummy dataset
X = np.random.rand(100, 5)
y = np.random.randint(0, 2, 100)

model = RandomForestClassifier()
model.fit(X, y)

joblib.dump(model, 'model.pkl')
print("Dummy model created!")
