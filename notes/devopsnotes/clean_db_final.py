#!/usr/bin/env python3
"""
Final script to clean DB Q&A file and preserve topic structure
"""

import re

def clean_db_final(input_file, output_file):
    """Clean DB Q&A file with topic preservation"""

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove major fluff sections first
    major_fluff = [
        r'If you want, I can expand this into a "200\+ practical DevOps DB Q&A list".*?Do you want me to do that next\?',
        r'You said:\s*Proceed\s*ChatGPT said:\s*Perfect\..*?Here\'s a comprehensive.*?migrations\.',
        r'Perfect\. Here\'s a comprehensive.*?migrations\.',
        r'Here\'s a comprehensive, practical DevOps database Q&A list, continuing from what we\'ve covered\. I\'ll focus on RDBMS, NoSQL, cloud-managed DBs, operations, monitoring, security, scaling, and migrations\.',
        r'Comprehensive Practical DevOps DB Q&A'
    ]

    cleaned_content = content
    for pattern in major_fluff:
        cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.DOTALL | re.IGNORECASE)

    # Split into lines and process
    lines = cleaned_content.split('\n')
    processed_lines = []
    question_number = 1

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines at the start
        if not line and not processed_lines:
            i += 1
            continue

        # Detect topic headers - numbered sections like "1. Database Operations & Reliability"
        topic_match = re.match(r'^(\d+)\.\s+([A-Z][a-zA-Z\s&/]+)$', line)
        if (topic_match and
            len(line) > 15 and
            not line.startswith('Q:') and
            '?' not in line and
            not re.match(r'^\d+\.\s*Q:', line)):

            processed_lines.append(f"\n## {line}")
            processed_lines.append("")
            question_number = 1  # Reset for each topic
            i += 1
            continue

        # Process questions
        if line.startswith('Q:'):
            question_text = line[2:].strip()
            processed_lines.append(f"{question_number}. Q: {question_text}")
            question_number += 1

            # Look for answer
            i += 1
            found_answer = False
            while i < len(lines):
                next_line = lines[i].strip()
                if next_line.startswith('A:'):
                    answer_text = next_line[2:].strip()
                    # Clean answer
                    answer_text = re.sub(r'\s+', ' ', answer_text)
                    if answer_text:
                        processed_lines.append(f"A: {answer_text}")
                        processed_lines.append("")
                    found_answer = True
                    break
                elif next_line and not next_line.startswith('Q:'):
                    i += 1
                else:
                    break

            if not found_answer:
                i -= 1  # Step back if no answer found
            i += 1
            continue

        i += 1

    # Write cleaned content
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(processed_lines))

    # Count results
    topics = len([line for line in processed_lines if line.startswith('## ')])
    questions = len([line for line in processed_lines if re.match(r'^\d+\.\s*Q:', line)])
    answers = len([line for line in processed_lines if line.startswith('A:')])

    print(f"Final clean DB Q&A file: {output_file}")
    print(f"Topics: {topics}")
    print(f"Questions: {questions}")
    print(f"Answers: {answers}")

if __name__ == "__main__":
    input_file = "db_qa_init.md"
    output_file = "db_qa_final.md"

    clean_db_final(input_file, output_file)
    print("Final DB cleaning completed!")