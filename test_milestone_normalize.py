from app.utils.change_tracker import ChangeTracker

# Create a ChangeTracker instance
tracker = ChangeTracker('.')

# Test different milestone formats
print("Testing milestone normalization...")

# Directory name format
dir_format = "sprint_1__test_milestone"
print(f"Directory format: '{dir_format}' → '{tracker._normalize_milestone_value(dir_format)}'")

# Object format
obj_format = {"title": "Sprint 1: Test Milestone"}
print(f"Object format: '{obj_format}' → '{tracker._normalize_milestone_value(obj_format)}'")

# Check if they match after normalization
dir_normalized = tracker._normalize_milestone_value(dir_format)
obj_normalized = tracker._normalize_milestone_value(obj_format)

print(f"Do normalized values match? {dir_normalized == obj_normalized}")
print(f"Directory normalized: '{dir_normalized}'")
print(f"Object normalized: '{obj_normalized}'") 