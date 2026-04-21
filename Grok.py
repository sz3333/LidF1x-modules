import re

# Previous code...

# Change line 1178 from {"html": True} to {"html": False}
# Before line 1191, add:
html_text = re.sub(r'<br\s*/?>', '\n', html_text)
html_text = re.sub(r'</?(?:div|span|ul|li|table|tbody|thead|tfoot|tr|td|th)[^>]*>', '', html_text)

# Following code...

return html_text