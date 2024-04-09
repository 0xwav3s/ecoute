import re

# Pattern to match lowercase, uppercase letters, and numbers
pattern = r"[a-zA-Z0-9]+"

# Sample text
text1 = ".\n(.)"  # Match
text2 = "Okay, interesting."  # No match

# Check for the pattern
match1 = re.search(pattern, text1)
match2 = re.search(pattern, text2)

if match1:
  print(f"'{text1}' contains only letters and numbers.")
else:
  print(f"'{text1}' might not contain only letters and numbers.")

if match2:
  print(f"'{text2}' contains only letters and numbers (unexpected).")  # Adjust message for unexpected matches
else:
  print(f"'{text2}' does not contain only letters and numbers (as expected).")
