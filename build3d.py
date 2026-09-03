#!/usr/bin/env python3
"""Inject the shared DATA payload from index.html into 3d.src.html -> 3d.html.

Keeping one payload means the 2D and 3D pages can never disagree about the
numbers, which is the whole reason the 3D page is generated rather than edited.
"""
src = open("3d.src.html").read()
page = open("index.html").read()
i = page.index("const DATA = ")
j = page.index(";\nconst REDUCED")
out = src.replace("__DATA__", page[i + len("const DATA = "):j])
assert "__DATA__" not in out, "payload not injected"
open("3d.html", "w").write(out)
print(f"built 3d.html ({len(out)//1024} KB)")
