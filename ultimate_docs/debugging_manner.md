# Strategic Debugging Approach for Complex Systems

## Overview

This document details the debugging approach used to identify and fix the system prompt override issue in our multi-agent framework. This methodology can be applied to similar complex systems where data flows through multiple components.

## Key Principles

1. **Strategic Print Statements**: Place debug prints at critical transformation points, not just at function entries/exits
2. **Variable State Tracking**: Track the state of important variables through their lifecycle
3. **Truncated Output**: For large strings, show meaningful portions rather than flooding logs
4. **Context Preservation**: Include identifying information in debug statements
5. **Before/After Comparisons**: Show values before and after transformations

## Implementation in Code

### 1. Strategic Placement of Debug Prints

Debug prints were added at key points in the data flow:

```python
# When a conversation is initialized
if not conversation.system_prompt:
    conversation.set_system_prompt(create_default_system_prompt())
    print(f"DEBUG: New conversation created with default system prompt")
else:
    print(f"DEBUG: Using existing conversation with system prompt: {conversation.system_prompt[:50]}...")

# Before system prompt augmentation
current_system_prompt = conversation.system_prompt
print(f"DEBUG: Original system prompt before augmentation: {current_system_prompt[:50]}...")

# After system prompt augmentation
conversation.set_system_prompt(augmented_prompt)
print(f"DEBUG: Augmented system prompt: {augmented_prompt[:50]}...")
```

### 2. String Truncation for Readability

For large strings like system prompts, showing the first N characters provides sufficient context without overwhelming logs:

```python
print(f"DEBUG: Using existing conversation with system prompt: {conversation.system_prompt[:50]}...")
```

The `[:50]` slice shows just the first 50 characters, followed by "..." to indicate truncation.

### 3. Labeling Debug Output

All debug statements are clearly labeled with "DEBUG:" and a descriptive message about what's being shown:

```python
print(f"DEBUG: Original system prompt before augmentation: {current_system_prompt[:50]}...")
```

This makes it easy to search logs and understand context.

## Benefits of This Approach

1. **Non-intrusive**: Debug statements don't alter program flow or behavior
2. **Targeted**: Only adds prints where needed, not everywhere
3. **Informative**: Provides just enough information to diagnose issues
4. **Maintainable**: Can be left in code for future debugging or conditionally disabled

## Application to the System Prompt Issue

This debugging approach revealed:

1. The system prompt was correctly set initially
2. It was later completely replaced by a call to `create_default_system_prompt()`
3. The custom prompt was lost during processing

The debug output clearly showed the value changing from the custom prompt to the default prompt, leading directly to the solution: preserving the original prompt and only augmenting it.

## Best Practices for Complex System Debugging

1. **Follow the Data**: Track important values as they flow through the system
2. **Focus on Transformations**: Pay special attention to points where data is modified
3. **Show Context**: Include enough information to understand what you're seeing
4. **Before/After Comparisons**: Show values before and after critical operations
5. **Use Source Control**: Make debugging changes in a way that can be easily managed in source control

## Implementing Debug Output Management

For production systems, consider adding a debug flag or logging level:

```python
if DEBUG:
    print(f"DEBUG: Original system prompt: {current_system_prompt[:50]}...")
```

Or use a proper logging system:

```python
import logging
logging.debug(f"Original system prompt: {current_system_prompt[:50]}...")
```

## Conclusion

Strategic debug prints are an essential tool for understanding complex systems. By following the data flow and showing values at critical transformation points, you can quickly identify issues that would be difficult to spot through code inspection alone. 