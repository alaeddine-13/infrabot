import re
from typing import List, Optional


def extract_code_blocks(text: str, title: Optional[str] = None) -> List[str]:
    """
    Extract code blocks from text that match the pattern ```{title}\n<content>```

    Args:
        text (str): The input text containing code blocks
        title (Optional[str]): If provided, only extract blocks with this title

    Returns:
        List[str]: List of extracted code block contents
    """
    # Pattern explanation:
    # ```           - Match opening triple backticks
    # ([^\n]*)     - Capture any characters except newline (the title)
    # \n           - Match newline
    # (.*?)        - Capture any characters (non-greedy) (the content)
    # ```          - Match closing triple backticks
    pattern = r"```([^\n]*)\n(.*?)```"

    # Use re.DOTALL to make dot match newlines
    matches = re.finditer(pattern, text, re.DOTALL)

    results = []
    for match in matches:
        block_title = match.group(1).strip()
        content = match.group(2).strip()

        # If title is specified, only include blocks with matching title
        if title is None or block_title.lower() == title.lower():
            results.append(content)

    return results


# Test the function
if __name__ == "__main__":
    sample_text = """```terraform
provider "aws" {
  region = "us-west-2"
}
```

```remarks
This is a remark
```"""

    # Test case 1: Extract all blocks
    print("All blocks:")
    blocks = extract_code_blocks(sample_text)
    for i, block in enumerate(blocks, 1):
        print(f"\nBlock {i}:")
        print(block)

    # Test case 2: Extract only terraform blocks
    print("\nTerraform blocks only:")
    terraform_blocks = extract_code_blocks(sample_text, "terraform")
    for i, block in enumerate(terraform_blocks, 1):
        print(f"\nBlock {i}:")
        print(block)

    # Test case 3: Extract only remarks blocks
    print("\nRemarks blocks only:")
    remarks_blocks = extract_code_blocks(sample_text, "remarks")
    for i, block in enumerate(remarks_blocks, 1):
        print(f"\nBlock {i}:")
        print(block)
