"""
Export the trained XGBoost model to ONNX format for on-device inference.
Run this once: python scripts/export_to_onnx.py
Output: models/cost_overrun_model.onnx

Approach: Use XGBoost's native JSON export, rename feature names to f0-f4,
reload into a fresh booster, then convert via onnxmltools.
"""
import joblib
import numpy as np
import os
import json
import tempfile

def export_xgboost_to_onnx():
    model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'cost_overrun_model.pkl')
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}")
    
    model = joblib.load(model_path)
    print(f"Loaded model: {type(model).__name__}")
    
    # Get original feature names
    original_names = [str(n) for n in getattr(model, 'feature_names_in_', [f'f{i}' for i in range(5)])]
    name_to_fid = {name: f'f{i}' for i, name in enumerate(original_names)}
    print(f"Feature mapping: {name_to_fid}")
    
    # Export booster to JSON, rename features, reload
    booster = model.get_booster()
    
    # Save to temp JSON file
    tmp_json = os.path.join(tempfile.gettempdir(), 'xgb_export.json')
    booster.save_model(tmp_json)
    
    with open(tmp_json, 'r') as f:
        model_dict = json.load(f)
    
    # Rename all feature references in the JSON
    json_str = json.dumps(model_dict)
    for orig_name, new_name in sorted(name_to_fid.items(), key=lambda x: -len(x[0])):
        # Replace in split references (as JSON string values)
        json_str = json_str.replace(f'"split":"{orig_name}"', f'"split":"{new_name}"')
    
    # Also fix feature_names array in learner
    model_dict = json.loads(json_str)
    if 'learner' in model_dict:
        learner = model_dict['learner']
        if 'feature_names' in learner:
            learner['feature_names'] = [f'f{i}' for i in range(len(learner['feature_names']))]
    
    # Save modified JSON and load into fresh booster
    tmp_modified = os.path.join(tempfile.gettempdir(), 'xgb_modified.json')
    with open(tmp_modified, 'w') as f:
        json.dump(model_dict, f)
    
    import xgboost as xgb
    new_booster = xgb.Booster()
    new_booster.load_model(tmp_modified)
    
    # Wrap in XGBClassifier for onnxmltools
    new_model = xgb.XGBClassifier()
    new_model._Booster = new_booster
    # Set required attributes via internal dict
    new_model.__dict__['_le'] = None
    new_model.__dict__['n_classes_'] = 2
    new_model.__dict__['_classes'] = np.array([0, 1])
    new_model.__dict__['objective'] = 'binary:logistic'
    
    # Convert to ONNX
    from onnxmltools import convert_xgboost
    from onnxmltools.convert.common.data_types import FloatTensorType
    
    initial_type = [('float_input', FloatTensorType([None, 5]))]
    
    onnx_model = convert_xgboost(
        new_model,
        initial_types=initial_type,
        target_opset=12,
    )
    
    # Save ONNX
    output_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'cost_overrun_model.onnx')
    with open(output_path, 'wb') as f:
        f.write(onnx_model.SerializeToString())
    
    file_size_kb = os.path.getsize(output_path) / 1024
    print(f"\nONNX model saved: {output_path}")
    print(f"File size: {file_size_kb:.1f} KB")
    
    # Verify
    print("\nVerifying ONNX model...")
    import onnxruntime as rt
    sess = rt.InferenceSession(output_path)
    
    test_input = np.array([[0.30, 0.35, 0.45, 45.0, 0.0]], dtype=np.float32)
    
    original_prob = model.predict_proba(test_input)[0][1]
    
    input_name = sess.get_inputs()[0].name
    all_outputs = [o.name for o in sess.get_outputs()]
    onnx_results = sess.run(all_outputs, {input_name: test_input})
    
    # Extract probability
    prob_output = onnx_results[1]  # index 1 = probabilities
    if isinstance(prob_output, list) and isinstance(prob_output[0], dict):
        onnx_prob = prob_output[0].get(1, 0.5)
    elif isinstance(prob_output, np.ndarray):
        onnx_prob = prob_output[0][1] if prob_output.ndim == 2 else float(prob_output)
    else:
        onnx_prob = 0.5
    
    print(f"Original XGBoost:  {original_prob:.4f}")
    print(f"ONNX prediction:   {onnx_prob:.4f}")
    print(f"Difference:        {abs(original_prob - onnx_prob):.6f}")
    
    status = "VERIFIED" if abs(original_prob - onnx_prob) < 0.01 else "WARNING"
    print(f"\nEXPORT {status}")
    
    # Save feature order reference
    feature_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'feature_order.json')
    with open(feature_path, 'w') as f:
        json.dump({'features': original_names, 'mapping': name_to_fid}, f, indent=2)
    
    # Cleanup
    for tmp in [tmp_json, tmp_modified]:
        if os.path.exists(tmp):
            os.remove(tmp)
    
    return output_path

if __name__ == '__main__':
    export_xgboost_to_onnx()
