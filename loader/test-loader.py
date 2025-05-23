import os
import random
import string
import sys

# This is a test script that creates a random file in the cards directory.
# This would be replaced with an actual script the loads cards from the API
# or any other source.

root_dir = sys.argv[1]
print(f"Working from {root_dir}")

# Create the "cards" directory if it doesn't exist
cards_dir = os.path.join(root_dir, "cards")
os.makedirs(cards_dir, exist_ok=True)

# Generate a random filename (8 characters long)
random_filename = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
file_path = os.path.join(cards_dir, random_filename + ".txt")

# Generate a random alphanumeric string (16 characters long)
random_content = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

# Write the random string to the file
with open(file_path, "w") as f:
    f.write(random_content)

print(f"File {file_path} created with content: {random_content}")
