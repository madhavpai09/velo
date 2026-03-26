#!/usr/bin/env python3
"""Remove duplicate auth endpoints from server.py"""

with open('serverapp/server.py', 'r') as f:
    lines = f.readlines()

# Find the locations of the duplicate endpoints
# First set at lines 303, 331, 376
# Second set at lines 423, 451, 496
# We want to keep the first set and remove lines 423-541 (everything until @app.post("/driver/register"))

# Find the line number of @app.post("/driver/register") after the duplicates
driver_register_line = None
for i, line in enumerate(lines):
    if '@app.post("/driver/register")' in line and i > 420:
        driver_register_line = i
        break

if driver_register_line:
    # Look back to find where the duplicates start (the blank lines before @app.post("/api/auth/refresh"))
    duplicate_start = None
    for i in range(420, 425):
        if '@app.post("/api/auth/refresh"' in lines[i]:
            # Find the blank lines before this
            j = i - 1
            while j > 415 and lines[j].strip() == '':
                j -= 1
            duplicate_start = j + 1
            break
    
    if duplicate_start:
        # Remove lines from duplicate_start to driver_register_line
        new_lines = lines[:duplicate_start] + lines[driver_register_line:]
        with open('serverapp/server.py', 'w') as f:
            f.writelines(new_lines)
        print(f"✅ Removed duplicate auth endpoints (lines {duplicate_start}-{driver_register_line-1})")
        print(f"   File size: {len(lines)} -> {len(new_lines)} lines")
    else:
        print("❌ Could not find duplicate start")
else:
    print("❌ Could not find /driver/register endpoint")
