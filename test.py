from solution import longestCommonPrefix

assert longestCommonPrefix(["ab", "a"]) == "a"
assert longestCommonPrefix([""]) == ""
assert longestCommonPrefix(["a"]) == "a"
assert longestCommonPrefix(["", "b"]) == ""
assert longestCommonPrefix(["flower", "flower", "flower"]) == "flower"
assert longestCommonPrefix(["flower", "flow", "flight"]) == "fl"
assert longestCommonPrefix(["dog", "racecar", "car"]) == ""
print("All tests passed!")
