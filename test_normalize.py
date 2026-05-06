from app.utils.change_tracker import ChangeTracker

# Create a test instance
tracker = ChangeTracker('.')

# Test different formats and see if they normalize to the same value
print("Testing milestone normalization...")

# Directory format
dir_format = "sprint_1__auth_ve_db_setup"
dir_normalized = tracker._normalize_milestone_value(dir_format)
print(f"Directory format: '{dir_format}' → '{dir_normalized}'")

# Dictionary format as it would come from the API
dict_format = {"title": "Sprint 1: Auth ve DB Setup"}
dict_normalized = tracker._normalize_milestone_value(dict_format)
print(f"Dictionary format: '{dict_format}' → '{dict_normalized}'")

# Test if they match
print(f"Do they match? {dir_normalized == dict_normalized}")

# Test other variations
variants = [
    "sprint_1:auth_ve_db_setup",  # No space after colon
    "sprint_1:_auth_ve_db_setup", # Underscore after colon
    "Sprint 1: Auth ve DB Setup", # Normal format with proper capitalization
    "sprint 1: auth ve db setup"  # Lowercase format
]

print("\nTesting variants:")
for variant in variants:
    variant_normalized = tracker._normalize_milestone_value(variant)
    print(f"Variant: '{variant}' → '{variant_normalized}'")
    print(f"  Matches directory format? {variant_normalized == dir_normalized}")
    print(f"  Matches dictionary format? {variant_normalized == dict_normalized}") 