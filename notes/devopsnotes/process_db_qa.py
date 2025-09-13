#!/usr/bin/env python3
"""
Script to process db_qa_init.md: format, remove fluff, order questions while preserving topics
"""

import re

def process_db_qa(input_file, output_file):
    """Process DB Q&A file - format, clean, and order while preserving topics"""

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove common fluff patterns
    fluff_patterns = [
        r'If you want, I can expand this.*?Do you want me to do that next\?',
        r'You said:\s*Proceed\s*ChatGPT said:\s*Perfect\.',
        r'Perfect\. Here\'s a comprehensive.*?',
        r'Do you want me to.*?',
        r'I can expand.*?',
        r'continuing from what we\'ve covered.*?',
        r'covering.*?cloud operations specifically\.',
        r'Comprehensive Practical DevOps DB Q&A',
        r'Here\'s a comprehensive.*?migrations\.'
    ]

    # Clean the content
    cleaned_content = content
    for pattern in fluff_patterns:
        cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.DOTALL | re.IGNORECASE)

    # Split into lines for processing
    lines = cleaned_content.split('\n')

    # Process lines to structure the content
    processed_lines = []
    current_topic = None
    question_number = 1

    for line in lines:
        line = line.strip()

        # Skip empty lines at start
        if not line and not processed_lines:
            continue

        # Check if this is a topic header (e.g., "1. Database Operations & Reliability")
        topic_match = re.match(r'^(\d+)\.\s+(.+)$', line)
        if topic_match and not line.startswith('Q:') and len(line) > 30:
            current_topic = line
            processed_lines.append(f"\n## {line}\n")
            question_number = 1  # Reset question numbering for each topic
            continue

        # Check if this is a question
        if line.startswith('Q:'):
            question_text = line[2:].strip()
            processed_lines.append(f"{question_number}. Q: {question_text}")
            question_number += 1
            continue

        # Check if this is an answer
        if line.startswith('A:'):
            answer_text = line[2:].strip()

            # Clean the answer further
            answer_clean_patterns = [
                r'→.*?(?=\s|$)',  # Remove arrow notation
                r'\s+', ' '       # Normalize whitespace
            ]

            for pattern, replacement in [(answer_clean_patterns[0], ''), (answer_clean_patterns[1], ' ')]:
                answer_text = re.sub(pattern, replacement, answer_text)

            answer_text = answer_text.strip()

            if answer_text:
                processed_lines.append(f"A: {answer_text}")
                processed_lines.append("")  # Blank line after each Q&A
            continue

        # Skip lines that are clearly fluff or metadata
        skip_patterns = [
            r'^Perfect\.',
            r'^You said:',
            r'^ChatGPT said:',
            r'^If you want',
            r'^Do you want',
            r'^Here\'s a',
            r'^\d+\+.*practical',
            r'^covering.*specifically'
        ]

        should_skip = any(re.match(pattern, line, re.IGNORECASE) for pattern in skip_patterns)
        if should_skip:
            continue

        # Add other meaningful lines
        if line and len(line) > 3:
            processed_lines.append(line)

    # Write the processed content
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(processed_lines))

    # Count questions by topics
    topics = [line for line in processed_lines if line.startswith('## ')]
    questions = [line for line in processed_lines if re.match(r'^\d+\.\s*Q:', line)]
    answers = [line for line in processed_lines if line.startswith('A:')]

    print(f"Processed DB Q&A file created: {output_file}")
    print(f"Topics: {len(topics)}")
    print(f"Questions: {len(questions)}")
    print(f"Answers: {len(answers)}")

    return len(topics), len(questions), len(answers)

if __name__ == "__main__":
    input_file = "db_qa_init.md"
    output_file = "db_qa_processed.md"

    process_db_qa(input_file, output_file)
    print("DB Q&A processing completed!")