import joblib
import os
import pandas as pd
import json
from datetime import datetime
import numpy as np

class MLPredictor:
    def __init__(self, model_path='ml/saved_models'):
        self.model_path = model_path
        self.load_best_model()
        self.load_encoders()
        
    def load_best_model(self):
        try:
            with open(os.path.join(self.model_path, 'best_model.json'), 'r') as f:
                info = json.load(f)
                best_name = info['best_model']
                self.model = joblib.load(os.path.join(self.model_path, f'{best_name}.pkl'))
                self.model_name = best_name
        except:
            self.model = None
            print("No model found. Please train first.")
            
    def load_encoders(self):
        try:
            self.encoders = {}
            for col in ['kondisi_saat_ini', 'jenis', 'merk', 'tipe']:
                self.encoders[f'le_{col}'] = joblib.load(os.path.join(self.model_path, f'le_{col}.pkl'))
        except:
            print("Encoders not found.")

    def predict(self, vehicle_data):
        # vehicle_data is a dict or object
        if not self.model:
            return 0
            
        current_year = datetime.now().year
        umur = current_year - vehicle_data['tahun_perolehan']
        
        # Safe encoding
        encoded_values = {}
        for col in ['kondisi_saat_ini', 'jenis', 'merk', 'tipe']:
            try:
                le = self.encoders[f'le_{col}']
                val = str(vehicle_data.get(col, ''))
                # Handle unknown labels
                if val in le.classes_:
                    encoded_values[f'{col}_encoded'] = le.transform([val])[0]
                else:
                    # Fallback to most frequent or default (0)
                    encoded_values[f'{col}_encoded'] = 0 
            except:
                encoded_values[f'{col}_encoded'] = 0

        features = pd.DataFrame([[
            umur, 
            vehicle_data['harga_perolehan'],
            vehicle_data['jarak_tempuh'],
            encoded_values['kondisi_saat_ini_encoded'],
            encoded_values['jenis_encoded'],
            encoded_values['merk_encoded'],
            encoded_values['tipe_encoded']
        ]], columns=['umur', 'harga_perolehan', 'jarak_tempuh', 'kondisi_saat_ini_encoded', 'jenis_encoded', 'merk_encoded', 'tipe_encoded'])
        
        prediction = self.model.predict(features)[0]
        return max(0, prediction) # No negative value
