#!/usr/bin/env python3
"""
Directly add questions to test_advisor_working.py
Simple approach: read file, find end of test_questions list, add new questions
"""

import sys
from pathlib import Path

# Fix Windows encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

project_root = Path(__file__).parent
test_file = project_root / "test_advisor_working.py"

# Read current file
with open(test_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find where test_questions list ends (look for closing bracket after test_questions)
end_idx = None
for i, line in enumerate(lines):
    if 'test_questions = [' in line:
        # Found start, now find the matching closing bracket
        bracket_count = 0
        for j in range(i, len(lines)):
            bracket_count += lines[j].count('[')
            bracket_count -= lines[j].count(']')
            if bracket_count == 0 and ']' in lines[j]:
                end_idx = j
                break
        break

if end_idx is None:
    print("Could not find end of test_questions list")
    # Try simpler approach - look for line with just ']'
    for i in range(800, 810):
        if i < len(lines) and lines[i].strip() == ']':
            end_idx = i
            print(f"Found closing bracket at line {i+1} using fallback method")
            break

if end_idx is None:
    print("Still could not find end of test_questions list")
    sys.exit(1)

print(f"Found test_questions list ending at line {end_idx + 1}")

# Count current questions
current_count = 0
for i in range(99, end_idx + 1):  # Start from line 99 where test_questions begins
    if i < len(lines) and '("' in lines[i]:
        current_count += 1

print(f"Current questions: {current_count}")

# Generate new questions to add (focusing on getting to 1000)
new_questions = []

# Formula calculation questions with specific numbers (200+)
for torque in [300, 350, 400, 450, 500, 550, 600, 650, 700]:
    for rpm in [5000, 5500, 6000, 6500, 7000, 7500]:
        new_questions.append(f'    ("Calculate horsepower from {torque} ft-lb at {rpm} RPM", "Should calculate HP = ({torque} × {rpm}) / 5252"),')

for hp in [400, 450, 500, 550, 600, 650, 700, 750, 800]:
    for rpm in [5000, 5500, 6000, 6500, 7000]:
        new_questions.append(f'    ("Calculate torque from {hp} HP at {rpm} RPM", "Should calculate T = ({hp} × 5252) / {rpm}"),')

# Boost conversions (50+)
for psi in [5, 7, 10, 12, 15, 18, 20, 22, 25, 28, 30, 35]:
    bar = round(psi / 14.5, 2)
    new_questions.append(f'    ("Convert {psi} PSI boost to bar", "Should calculate {psi} / 14.5 = {bar} bar"),')

for bar in [0.3, 0.5, 0.7, 1.0, 1.2, 1.5, 1.8, 2.0, 2.2, 2.5]:
    psi = round(bar * 14.5, 1)
    new_questions.append(f'    ("Convert {bar} bar boost to PSI", "Should calculate {bar} × 14.5 = {psi} PSI"),')

# Injector sizing calculations (100+)
for hp in [400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900]:
    for bsfc in [0.5, 0.55, 0.6, 0.65, 0.7]:
        for injectors in [4, 6, 8]:
            for duty in [0.75, 0.8, 0.85]:
                size = round((hp * bsfc) / (duty * injectors), 1)
                new_questions.append(f'    ("Calculate injector size for {hp} HP, {bsfc} BSFC, {injectors} injectors, {int(duty*100)}% duty", "Should calculate size ≈ {size} lb/hr"),')

# CFM calculations (50+)
for cid in [300, 350, 400, 450, 500]:
    for rpm in [5000, 5500, 6000, 6500, 7000]:
        for ve in [0.80, 0.85, 0.90, 0.95, 1.0]:
            cfm = round((cid * rpm * ve) / 3456, 0)
            new_questions.append(f'    ("Calculate CFM for {cid} CID engine at {rpm} RPM with {int(ve*100)}% VE", "Should calculate CFM ≈ {int(cfm)}"),')

# VE calculations (50+)
for cfm in [400, 450, 500, 550, 600, 650, 700]:
    for cid in [300, 350, 400, 450, 500]:
        for rpm in [5000, 5500, 6000, 6500, 7000]:
            ve = round((cfm * 3456) / (cid * rpm), 2)
            if 0.5 <= ve <= 1.2:  # Reasonable VE range
                new_questions.append(f'    ("Calculate VE if engine flows {cfm} CFM at {rpm} RPM, {cid} CID", "Should calculate VE ≈ {ve}"),')

# Drivetrain loss calculations (30+)
for rwhp in [300, 350, 400, 450, 500, 550, 600]:
    for loss_pct in [12, 15, 18, 20, 22]:
        crank = round(rwhp / (1 - loss_pct/100), 0)
        new_questions.append(f'    ("Calculate crank HP if wheel HP is {rwhp} with {loss_pct}% drivetrain loss", "Should calculate ≈ {int(crank)} HP"),')

# Power to weight (30+)
for hp in [400, 450, 500, 550, 600, 650, 700]:
    for weight in [2500, 3000, 3500, 4000]:
        ratio = round(hp / (weight / 1000), 2)
        new_questions.append(f'    ("Calculate power to weight ratio for {hp} HP, {weight} lb car", "Should calculate {ratio} HP/1000lb"),')

# Fuel flow calculations (50+)
for injectors in [4, 6, 8]:
    for size in [40, 50, 60, 70, 80, 90, 100]:
        for duty in [0.5, 0.6, 0.7, 0.8, 0.85]:
            flow = round(injectors * size * duty, 1)
            new_questions.append(f'    ("Calculate total fuel flow for {injectors} injectors, {size} lb/hr each, {int(duty*100)}% duty", "Should calculate ≈ {flow} lb/hr"),')

# Air density calculations (30+)
for temp_f in [50, 60, 70, 80, 90, 100]:
    for pressure in [28.5, 29.0, 29.5, 30.0, 30.5]:
        new_questions.append(f'    ("Calculate air density at {temp_f}°F, {pressure} inHg", "Should calculate air density"),')

# Limit to reasonable number to avoid file being too large
new_questions = new_questions[:800]  # Add 800 new questions

print(f"Generated {len(new_questions)} new questions")
print(f"Total will be: {current_count + len(new_questions)} questions")

# Insert new questions before closing bracket
new_lines = lines[:end_idx] + new_questions + ['\n'] + lines[end_idx:]

# Write back
with open(test_file, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"✓ Added {len(new_questions)} questions to test file")
print(f"✓ Total questions now: {current_count + len(new_questions)}")

