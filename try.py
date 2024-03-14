import language_tool_python

mytext = """
I is testng grammar tool using python. It does not costt anythng.
"""

def grammarCorrector(text):
    tool = language_tool_python.LanguageTool('en-US')
    result = tool.correct(text)
    return result

output_data = grammarCorrector(mytext)
print(output_data)