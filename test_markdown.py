#!/usr/bin/env python3
"""Simple test script to verify markdown to ADF conversion."""

import sys
import json
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from jira_cli.utils.markdown_to_adf import markdown_to_adf, text_to_adf


def test_markdown_to_adf():
    """Test basic markdown to ADF conversion."""
    print("Testing Markdown to ADF Conversion...")
    
    # Test cases
    test_cases = [
        {
            "name": "Simple paragraph",
            "markdown": "This is a simple paragraph.",
            "expected_type": "doc"
        },
        {
            "name": "Heading",
            "markdown": "# Main Title\n\nThis is content under the heading.",
            "expected_type": "doc"
        },
        {
            "name": "Bold and italic",
            "markdown": "This has **bold text** and *italic text*.",
            "expected_type": "doc"
        },
        {
            "name": "Code block",
            "markdown": "```python\nprint('Hello, World!')\n```",
            "expected_type": "doc"
        },
        {
            "name": "Inline code",
            "markdown": "Use the `print()` function to output text.",
            "expected_type": "doc"
        },
        {
            "name": "List",
            "markdown": "- Item 1\n- Item 2\n- Item 3",
            "expected_type": "doc"
        },
        {
            "name": "Link",
            "markdown": "Check out [Google](https://google.com) for search.",
            "expected_type": "doc"
        },
        {
            "name": "Mixed content",
            "markdown": """# Project Update

This is an **important** update about our project.

## Key Points

- Feature A is `completed`
- Feature B is *in progress*
- [Documentation](https://example.com) has been updated

```bash
git commit -m "Add new features"
```

> Remember to test everything before deployment!
""",
            "expected_type": "doc"
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        try:
            print(f"\n{i}. Testing: {test_case['name']}")
            print(f"   Markdown: {repr(test_case['markdown'][:50])}...")
            
            result = markdown_to_adf(test_case['markdown'])
            
            # Basic validation
            assert result['type'] == test_case['expected_type'], f"Expected type {test_case['expected_type']}, got {result['type']}"
            assert 'version' in result, "Missing version field"
            assert 'content' in result, "Missing content field"
            assert isinstance(result['content'], list), "Content should be a list"
            
            print(f"   ✓ SUCCESS - Generated {len(result['content'])} content blocks")
            success_count += 1
            
        except Exception as e:
            print(f"   ✗ FAILED - {str(e)}")
    
    print(f"\n=== Results ===")
    print(f"Passed: {success_count}/{len(test_cases)} tests")
    
    if success_count == len(test_cases):
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False


def demo_adf_output():
    """Show example ADF output."""
    print("\n" + "="*50)
    print("DEMO: ADF Output Examples")
    print("="*50)
    
    examples = [
        "# Epic: User Authentication\n\nImplement secure user authentication system.",
        "## Story: Login Form\n\n- Create login UI\n- Add form validation\n- **Priority**: High",
        "### Sub-task: Backend API\n\n```javascript\n// Login endpoint\napp.post('/login', (req, res) => {\n  // TODO: implement\n});\n```"
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\nExample {i}:")
        print(f"Markdown:\n{example}")
        print("\nADF Output:")
        result = markdown_to_adf(example)
        print(json.dumps(result, indent=2))
        print("-" * 30)


if __name__ == "__main__":
    print("Jira CLI Markdown to ADF Test")
    print("=" * 40)
    
    # Run tests
    success = test_markdown_to_adf()
    
    # Show demo if tests pass
    if success:
        demo_adf_output()
    
    sys.exit(0 if success else 1)