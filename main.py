

def parse_batch_prompts(text: str) -> list:
    """Parse input text into multiple prompts based on numbered list or delimiters."""
    import re
    # Check for numbered list (e.g., 1., 2., etc.)
    pattern = r'\d+\s*\.?\s*'
    prompts = re.split(pattern, text)
    prompts = [p.strip() for p in prompts if p.strip()]
    if len(prompts) > 1:
        return prompts
    # If not a numbered list, check for other delimiters like '---' or multiple newlines
    if '---' in text:
        prompts = text.split('---')
        prompts = [p.strip() for p in prompts if p.strip()]
        if len(prompts) > 1:
            return prompts
    if '\n\n' in text:
        prompts = text.split('\n\n')
        prompts = [p.strip() for p in prompts if p.strip()]
        if len(prompts) > 1:
            return prompts
    # Default to single prompt if no batch detected
    return [text.strip()]
