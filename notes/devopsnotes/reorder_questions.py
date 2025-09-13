#!/usr/bin/env python3
"""
Script to reorder questions in sequential order in cicd_qa file
"""

import re

def reorder_questions(input_file, output_file):
    """Reorder questions to be in sequential numerical order"""

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all Q&A pairs
    qa_pairs = []

    # Split content by question patterns
    parts = re.split(r'(\d+\.\s*Q:)', content)

    current_qa = ""
    for i, part in enumerate(parts):
        if re.match(r'\d+\.\s*Q:', part):
            # This is a question marker
            if current_qa.strip():
                qa_pairs.append(current_qa.strip())
            current_qa = part
        elif part.strip():
            # This is content following a question
            current_qa += part

    # Add the last Q&A pair
    if current_qa.strip():
        qa_pairs.append(current_qa.strip())

    # Extract question number, question text, and answer for sorting
    structured_pairs = []

    for qa in qa_pairs:
        # Extract question number
        match = re.match(r'(\d+)\.\s*Q:\s*([^\n]+)', qa)
        if match:
            original_num = int(match.group(1))
            question_text = match.group(2).strip()

            # Extract answer
            answer_match = re.search(r'A:\s*([^\n].*?)(?=\n\d+\.\s*Q:|\Z)', qa, re.DOTALL)
            if answer_match:
                answer_text = answer_match.group(1).strip()
            else:
                # Look for answer differently
                lines = qa.split('\n')
                answer_lines = []
                found_answer = False
                for line in lines:
                    if line.strip().startswith('A:'):
                        found_answer = True
                        answer_lines.append(line.strip()[2:].strip())
                    elif found_answer and line.strip() and not re.match(r'\d+\.\s*Q:', line):
                        answer_lines.append(line.strip())
                    elif found_answer and re.match(r'\d+\.\s*Q:', line):
                        break

                answer_text = ' '.join(answer_lines).strip()

            if answer_text:
                structured_pairs.append({
                    'original_num': original_num,
                    'question': question_text,
                    'answer': answer_text
                })

    # Sort by original number to maintain logical order
    structured_pairs.sort(key=lambda x: x['original_num'])

    # Generate new sequential content
    output_lines = []

    for i, pair in enumerate(structured_pairs, 1):
        output_lines.append(f"{i}. Q: {pair['question']}")
        output_lines.append(f"A: {pair['answer']}")
        output_lines.append("")  # Blank line between pairs

    # Write to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

    print(f"Reordered {len(structured_pairs)} questions sequentially in {output_file}")

if __name__ == "__main__":
    input_file = "cicd_qa.md"
    output_file = "cicd_qa_ordered.md"

    reorder_questions(input_file, output_file)
    print("Question reordering completed!")