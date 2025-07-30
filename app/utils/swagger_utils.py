import os
import yaml
from flasgger import swag_from

'''
Load Swagger documentation from a YAML file

Args:
    file_path (str): Relative path to the YAML file from the app directory
    
Returns:
    function: Decorated function with Swagger documentation
'''
def yaml_from_file(file_path):
    # Get the absolute path to the YAML file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    yaml_path = os.path.join(base_dir, file_path)
    
    # Check if the file exists
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"Swagger YAML file not found: {yaml_path}")
    
    # Load the YAML file
    with open(yaml_path, 'r') as f:
        yaml_doc = yaml.safe_load(f)
    
    # Return the swag_from decorator with the loaded YAML
    return swag_from(yaml_doc)