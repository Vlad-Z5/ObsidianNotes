#!/usr/bin/env python3
"""
Improved script to process db_qa_init.md: format, remove fluff, order questions while preserving topics
"""

import re

def process_db_qa_improved(input_file, output_file):
    """Process DB Q&A file - format, clean, and order while preserving topics"""

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove common fluff patterns more aggressively
    fluff_patterns = [
        r'If you want, I can expand this.*?Do you want me to do that next\?',
        r'You said:\s*Proceed\s*ChatGPT said:\s*Perfect\.',
        r'Perfect\. Here\'s a comprehensive.*?migrations\.',
        r'Do you want me to.*?',
        r'I can expand.*?specifically\.',
        r'continuing from what we\'ve covered.*?',
        r'covering.*?cloud operations specifically\.',
        r'Comprehensive Practical DevOps DB Q&A',
        r'Here\'s a comprehensive.*?'
    ]

    # Clean the content
    cleaned_content = content
    for pattern in fluff_patterns:
        cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.DOTALL | re.IGNORECASE)

    # Split into lines
    lines = cleaned_content.split('\n')

    processed_lines = []
    current_topic = None
    question_counter = 1
    global_question_counter = 1

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines at the start
        if not line and not processed_lines:
            i += 1
            continue

        # Detect topic headers - look for standalone numbered sections with descriptive names
        # e.g., "1. Database Operations & Reliability"
        if (re.match(r'^(\d+)\.\s+[A-Z][a-zA-Z\s&]+$', line) and
            len(line) > 20 and
            not line.startswith('Q:') and
            '?' not in line):

            current_topic = line
            processed_lines.append(f"\n## {line}\n")
            question_counter = 1  # Reset numbering for each topic
            i += 1
            continue

        # Process questions - handle both "Q:" format and direct questions
        if line.startswith('Q:'):
            question_text = line[2:].strip()
            processed_lines.append(f"{question_counter}. Q: {question_text}")
            question_counter += 1
            global_question_counter += 1

            # Look for the answer on the next line(s)
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                if next_line.startswith('A:'):
                    answer_text = next_line[2:].strip()

                    # Clean the answer
                    answer_text = re.sub(r'\s+', ' ', answer_text)

                    if answer_text:
                        processed_lines.append(f"A: {answer_text}")
                        processed_lines.append("")  # Blank line
                    break
                elif not next_line:  # Empty line, keep looking
                    i += 1
                else:
                    # No answer found, break
                    i -= 1  # Step back to process this line again
                    break
            i += 1
            continue

        # Skip fluff lines
        skip_patterns = [
            r'^Perfect\.',
            r'^You said:',
            r'^ChatGPT said:',
            r'^If you want',
            r'^Do you want',
            r'^Here\'s a',
            r'^\d+\+.*practical',
            r'^covering.*specifically',
            r'^I can expand',
            r'^continuing from'
        ]

        should_skip = any(re.match(pattern, line, re.IGNORECASE) for pattern in skip_patterns)
        if should_skip:
            i += 1
            continue

        i += 1

    # Write the processed content
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(processed_lines))

    # Count results
    topics = len([line for line in processed_lines if line.startswith('## ')])
    questions = len([line for line in processed_lines if re.match(r'^\d+\.\s*Q:', line)])
    answers = len([line for line in processed_lines if line.startswith('A:')])

    print(f"Improved DB Q&A file created: {output_file}")
    print(f"Topics: {topics}")
    print(f"Questions: {questions}")
    print(f"Answers: {answers}")

if __name__ == "__main__":
    input_file = "db_qa_init.md"
    output_file = "db_qa_clean.md"

    process_db_qa_improved(input_file, output_file)
    print("Improved DB Q&A processing completed!")