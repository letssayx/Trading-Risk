import os
import re

print("Searching for the bad revision '3658cdc76243' in alembic/versions...")
versions_dir = "alembic/versions"
target_revision = "merge_016_and_5218b"
bad_revision = "3658cdc76243"

found = False
if os.path.exists(versions_dir):
    for filename in os.listdir(versions_dir):
        if filename.endswith(".py"):
            filepath = os.path.join(versions_dir, filename)
            with open(filepath, "r") as f:
                content = f.read()

            if bad_revision in content:
                found = True
                print(f"Found bad revision in {filename}, fixing...")
                # Replace in down_revision
                new_content = re.sub(
                    r"(down_revision\s*=\s*[\"'])" + bad_revision + r"([\"'])",
                    r"\g<1>" + target_revision + r"\g<2>",
                    content
                )
                with open(filepath, "w") as f:
                    f.write(new_content)
                print(f"Successfully fixed {filename}!")

if not found:
    print("No files found referencing the bad revision '3658cdc76243' in the codebase.")
    print("This means the issue is likely strictly in your database's alembic_version table.")
    print("Please run this SQL command against your PostgreSQL database to fix it:")
    print("UPDATE alembic_version SET version_num = 'merge_016_and_5218b';")
else:
    print("Files have been fixed! Try running `alembic upgrade head` again.")
