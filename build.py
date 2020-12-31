import os
from pathlib import Path

os.system("python show.py")
os.system("pandoc .\README.md -o index.html")

with open("index.html") as f:
    contents = f.read()

with open("plot1.html") as f:
    plot1 = f.read()
with open("plot2.html") as f:
    plot2 = f.read()

contents = contents.replace("<p>[PLOTS]</p>", plot1 + plot2)

with open("pandoc.css") as f:
    style = f.read()

contents = contents.replace("</head>", "\n<style>\n" + style + "\n</style>\n</head>")

with open("index.html", "w") as f:
    f.write(contents)

Path("plot1.html").unlink()
Path("plot2.html").unlink()
