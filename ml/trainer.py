import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder
import joblib
import os
import json
from datetime import datetime

class MLTrainer:
    def __init__(self, model_path='ml/saved_models'):
        self.model_path = model_path
        if not os.path.exists(self.model_path):
            os.makedirs(self.model_path)
            
        # Base models for GridSearch
        self.models = {
            'LinearRegression': {
                'model': LinearRegression(),
                'params': {}
            },
            'RandomForest': {
                'model': RandomForestRegressor(random_state=42),
                'params': {
                    'n_estimators': [100, 200],
                    'max_depth': [None, 10, 20],
                    'min_samples_split': [2, 5]
                }
            },
            'XGBoost': {
                'model': XGBRegressor(objective='reg:squarederror', random_state=42),
                'params': {
                    'n_estimators': [100, 200],
                    'learning_rate': [0.01, 0.1],
                    'max_depth': [3, 5, 7]
                }
            }
        }
        
    def preprocess_data(self, df):
        # Feature Engineering
        # Calculate Age
        current_year = datetime.now().year
        df['umur'] = current_year - df['tahun_perolehan']
        
        # Encode Categorical
        encoders = {}
        categorical_cols = ['kondisi_saat_ini', 'jenis', 'merk', 'tipe']
        
        for col in categorical_cols:
            le = LabelEncoder()
            # Handle potential missing values or enforce string type
            df[f'{col}_encoded'] = le.fit_transform(df[col].astype(str))
            encoders[f'le_{col}'] = le
            
            # Save encoder
            joblib.dump(le, os.path.join(self.model_path, f'le_{col}.pkl'))
        
        # Select Features
        features = ['umur', 'harga_perolehan', 'jarak_tempuh'] + [f'{col}_encoded' for col in categorical_cols]
        target = 'nilai_pasar_real'
        
        return df[features], df[target]

    def train_all(self, data_path=None, df=None):
        if df is None and data_path:
            df = pd.read_excel(data_path)
        
        if df is None:
            return None
            
        X, y = self.preprocess_data(df)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        results = {}
        best_score = -float('inf')
        best_model_name = ''
        
        print("Training models...")
        
        for name, config in self.models.items():
            print(f"Optimizing {name}...")
            
            if config['params']:
                grid = GridSearchCV(config['model'], config['params'], cv=3, scoring='r2', n_jobs=-1)
                grid.fit(X_train, y_train)
                model = grid.best_estimator_
                print(f"  Best params for {name}: {grid.best_params_}")
            else:
                model = config['model']
                model.fit(X_train, y_train)
                
            preds = model.predict(X_test)
            
            mae = mean_absolute_error(y_test, preds)
            rmse = np.sqrt(mean_squared_error(y_test, preds))
            r2 = r2_score(y_test, preds)
            
            results[name] = {
                'MAE': mae,
                'RMSE': rmse,
                'R2': r2
            }
            
            # Save every model
            joblib.dump(model, os.path.join(self.model_path, f'{name}.pkl'))
            
            if r2 > best_score:
                best_score = r2
                best_model_name = name
                
        # Save best model reference
        with open(os.path.join(self.model_path, 'best_model.json'), 'w') as f:
            json.dump({'best_model': best_model_name, 'metrics': results}, f)
            
        return results

if __name__ == "__main__":
    # Enhanced dummy training data generation for testing
    np.random.seed(42)
    n_samples = 5000
    
    data = {
        'tahun_perolehan': np.random.randint(2015, 2024, n_samples),
        'harga_perolehan': np.random.randint(150000000, 800000000, n_samples),
        'kondisi_saat_ini': np.random.choice(['Baik', 'Rusak Ringan', 'Rusak Berat'], n_samples),
        'jarak_tempuh': np.random.randint(5000, 150000, n_samples),
        'jenis': np.random.choice(['Mobil', 'Motor'], n_samples),
        'merk': np.random.choice(['Toyota', 'Honda', 'Mitsubishi', 'Suzuki'], n_samples),
        'tipe': np.random.choice(['Avanza', 'Civic', 'Pajero', 'Ertiga'], n_samples)
    }
    
    df = pd.DataFrame(data)
    
    # Simulate somewhat realistic depreciation logic
    # Base depreciation
    depreciation_rate = 0.10 
    
    # Brand factor (Brand Value)
    brand_factor = df['merk'].map({'Toyota': 0.95, 'Honda': 0.92, 'Mitsubishi': 0.90, 'Suzuki': 0.85})
    
    # Condition factor
    condition_factor = df['kondisi_saat_ini'].map({'Baik': 1.0, 'Rusak Ringan': 0.7, 'Rusak Berat': 0.4})
    
    age = 2024 - df['tahun_perolehan']
    
    df['nilai_pasar_real'] = df['harga_perolehan'] * (1 - depreciation_rate) ** age
    df['nilai_pasar_real'] = df['nilai_pasar_real'] * brand_factor * condition_factor
    
    # Add very small noise for high accuracy demonstration
    df['nilai_pasar_real'] += np.random.normal(0, 5000, n_samples)
    
    trainer = MLTrainer()
    results = trainer.train_all(df=df)
    print("\nTraining Results:")
    print(json.dumps(results, indent=2))
