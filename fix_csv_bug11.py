# If it is treating it as a regex, it means the preceding context is broken!
# Maybe an unbalanced quote or bracket?
with open("test_clean.js", "r") as f:
    js = f.read()

# Let's run a linter or simply inspect the lines before it.
for i in range(250, 275):
    print(f"{i}: {js.split(chr(10))[i]}")
