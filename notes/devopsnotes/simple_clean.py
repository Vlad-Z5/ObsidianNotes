#!/usr/bin/env python3
"""
Simple targeted cleaning to remove specific fluff patterns
"""

import re

def simple_clean(input_file, output_file):
    """Simple cleaning targeting specific fluff patterns"""

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Define specific fluff patterns to remove
    fluff_patterns = [
        r' I can keep going and expand this all the way to 100\+ questions[^.]*\.',
        r' Do you want me to continue to #100\?[^.]*\.',
        r' You said:\s*Proceed\s*ChatGPT said:\s*Perfect\.[^.]*\.',
        r' If you want, I can continue[^.]*\.',
        r' Do you want me to proceed with that\?',
        r' Do you want me to continue with that\?',
        r' Do you want me to make that next\?',
        r' I can also create[^.]*\.',
        r' This brings us to \d+[^.]*\.',
        r' We\'ve now covered[^.]*\.',
        r' At this point[^.]*\.',
        r' to #100\? Perfect\. Let\'s continue expanding your practical CI/CD interview Q&A from #66 onward, keeping it highly realistic, scenario-driven, and DevOps-focused\.',
        r' Perfect\. Let\'s continue[^.]*DevOps-focused\.',
        r' continuing from #\d+ onward[^.]*\.',
        r' from #\d+ all the way to[^.]*\.',
        r' going into extreme[^.]*\.',
        r' covering[^.]*interview[^.]*\.',
        r' giving you a[^.]*Q&A[^.]*\.',
        r' create a[^.]*master-level[^.]*\.',
        r' DevOps interview[^.]*\.',
        r' me to continue\.',
        r' me to proceed\.'
    ]

    # Apply each pattern
    cleaned_content = content
    for pattern in fluff_patterns:
        cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.DOTALL | re.IGNORECASE)

    # Clean up double spaces and extra periods
    cleaned_content = re.sub(r'  +', ' ', cleaned_content)
    cleaned_content = re.sub(r'\.+', '.', cleaned_content)

    # Write the result
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)

    # Count questions and answers
    question_count = len(re.findall(r'^\d+\.\s*Q:', cleaned_content, re.MULTILINE))
    answer_count = len(re.findall(r'^A:', cleaned_content, re.MULTILINE))

    print(f"Simple clean Q&A file created: {output_file}")
    print(f"Questions: {question_count}, Answers: {answer_count}")

if __name__ == "__main__":
    input_file = "cicd_qa_only.md"
    output_file = "cicd_qa_simple_clean.md"

    simple_clean(input_file, output_file)
    print("Simple cleaning completed!")