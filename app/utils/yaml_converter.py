"""
JSON ve YAML formatları arasında dönüşüm sağlayan modül.
"""
import yaml
from typing import Dict, Any, List


def dict_to_yaml(data: Dict[str, Any]) -> str:
    """Sözlük verisini YAML formatına dönüştürür.
    
    Args:
        data: Dönüştürülecek sözlük
        
    Returns:
        YAML formatında metin
    """
    return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)


def yaml_to_dict(yaml_content: str) -> Dict[str, Any]:
    """YAML formatındaki metni sözlüğe dönüştürür.
    
    Args:
        yaml_content: YAML formatında metin
        
    Returns:
        Dönüştürülmüş sözlük
    """
    return yaml.safe_load(yaml_content) or {}


def compare_yaml_json(yaml_content: str, json_data: Dict[str, Any]) -> List[str]:
    """YAML ve JSON verilerini karşılaştırır.
    
    Args:
        yaml_content: YAML formatında metin
        json_data: JSON verisi
        
    Returns:
        Farklılıkların listesi
    """
    yaml_data = yaml_to_dict(yaml_content)
    
    differences = []
    _compare_dicts(yaml_data, json_data, "", differences)
    
    return differences


def _compare_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any], path: str, differences: List[str]) -> None:
    """Compare two dictionaries and find differences.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary
        path: Current path
        differences: List of differences
    """
    # Check all keys in dict1
    for key in dict1:
        current_path = f"{path}.{key}" if path else key
        
        # Key not in dict2
        if key not in dict2:
            differences.append(f"Key only exists in YAML: {current_path}")
            continue
        
        # Value exists in both dictionaries, check types
        if type(dict1[key]) != type(dict2[key]):
            differences.append(f"Type mismatch: {current_path} - YAML: {type(dict1[key]).__name__}, JSON: {type(dict2[key]).__name__}")
            continue
        
        # Nested dictionaries
        if isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
            _compare_dicts(dict1[key], dict2[key], current_path, differences)
        # Lists
        elif isinstance(dict1[key], list) and isinstance(dict2[key], list):
            _compare_lists(dict1[key], dict2[key], current_path, differences)
        # Other values
        elif dict1[key] != dict2[key]:
            differences.append(f"Value different: {current_path} - YAML: {dict1[key]}, JSON: {dict2[key]}")
    
    # Check keys in dict2 that are not in dict1
    for key in dict2:
        if key not in dict1:
            current_path = f"{path}.{key}" if path else key
            differences.append(f"Key only exists in JSON: {current_path}")


def _compare_lists(list1: List[Any], list2: List[Any], path: str, differences: List[str]) -> None:
    """Compare two lists and find differences.
    
    Args:
        list1: First list
        list2: Second list
        path: Current path
        differences: List of differences
    """
    # Check list lengths
    if len(list1) != len(list2):
        differences.append(f"List lengths different: {path} - YAML: {len(list1)}, JSON: {len(list2)}")
    
    # Compare common indices
    for i in range(min(len(list1), len(list2))):
        current_path = f"{path}[{i}]"
        
        # Check types
        if type(list1[i]) != type(list2[i]):
            differences.append(f"Type mismatch: {current_path} - YAML: {type(list1[i]).__name__}, JSON: {type(list2[i]).__name__}")
            continue
        
        # Nested dictionaries
        if isinstance(list1[i], dict) and isinstance(list2[i], dict):
            _compare_dicts(list1[i], list2[i], current_path, differences)
        # Nested lists
        elif isinstance(list1[i], list) and isinstance(list2[i], list):
            _compare_lists(list1[i], list2[i], current_path, differences)
        # Other values
        elif list1[i] != list2[i]:
            differences.append(f"Value different: {current_path} - YAML: {list1[i]}, JSON: {list2[i]}")


def merge_yaml_json(yaml_content: str, json_data: Dict[str, Any]) -> Dict[str, Any]:
    """YAML ve JSON verilerini birleştirir.
    
    Args:
        yaml_content: YAML formatında metin
        json_data: JSON verisi
        
    Returns:
        Birleştirilmiş veri
    """
    yaml_data = yaml_to_dict(yaml_content)
    
    # Add JSON data to YAML data
    merged_data = _merge_dicts(yaml_data, json_data)
    
    return merged_data


def _merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """İki sözlüğü birleştirir.
    
    Args:
        dict1: Birinci sözlük
        dict2: İkinci sözlük
        
    Returns:
        Birleştirilmiş sözlük
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        # Both dictionaries have the key and both are dictionaries
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_dicts(result[key], value)
        # Both dictionaries have the key and both are lists
        elif key in result and isinstance(result[key], list) and isinstance(value, list):
            result[key] = _merge_lists(result[key], value)
        # Other cases
        else:
            result[key] = value
    
    return result


def _merge_lists(list1: List[Any], list2: List[Any]) -> List[Any]:
    """İki listeyi birleştirir.
    
    Args:
        list1: Birinci liste
        list2: İkinci liste
        
    Returns:
        Birleştirilmiş liste
    """
    # Simple merge: keep list1 and add missing elements from list2
    result = list1.copy()
    
    # If lists contain dictionaries and have an ID field, merge by ID
    if all(isinstance(item, dict) for item in list1 + list2):
        # Find ID field
        id_fields = ["id", "ID", "Id", "name", "Name"]
        id_field = None
        
        for field in id_fields:
            if all(field in item for item in list1 + list2):
                id_field = field
                break
        
        # If ID field found, merge by ID
        if id_field:
            result_ids = [item[id_field] for item in result]
            
            for item2 in list2:
                item2_id = item2[id_field]
                
                # If ID already exists in result, update
                if item2_id in result_ids:
                    index = result_ids.index(item2_id)
                    
                    if isinstance(result[index], dict) and isinstance(item2, dict):
                        result[index] = _merge_dicts(result[index], item2)
                # Otherwise, add
                else:
                    result.append(item2)
                    result_ids.append(item2_id)
            
            return result
    
    # If ID merge cannot be done, add missing elements from list2
    for item in list2:
        if item not in result:
            result.append(item)
    
    return result


def json_to_yaml(json_data: Dict[str, Any]) -> str:
    """JSON verisini YAML formatına dönüştürür.
    
    Args:
        json_data: JSON verisi
        
    Returns:
        YAML formatında metin
    """
    return dict_to_yaml(json_data)


def yaml_to_json(yaml_content: str) -> Dict[str, Any]:
    """YAML formatındaki metni JSON verisine dönüştürür.
    
    Args:
        yaml_content: YAML formatında metin
        
    Returns:
        JSON verisi
    """
    return yaml_to_dict(yaml_content) 