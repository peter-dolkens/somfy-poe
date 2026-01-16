# Contributing to Somfy PoE Home Assistant Integration

Thank you for your interest in contributing! This document provides guidelines and information for contributors.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a branch** for your feature/fix
4. **Make your changes**
5. **Test thoroughly**
6. **Submit a pull request**

## Development Setup

### Requirements

- Python 3.10 or newer
- Home Assistant development environment
- Access to Somfy PoE motors for testing

### Installation for Development

```bash
# Clone your fork
git clone https://github.com/yourusername/somfy-poe.git
cd somfy-poe/implementations/homeassistant

# Install dependencies
pip install -r requirements.txt

# Run tests
python3 test_connection.py <motor_ip> <pin>
```

### Testing with Home Assistant

1. Copy `custom_components/somfy_poe` to your Home Assistant config directory
2. Enable debug logging:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.somfy_poe: debug
   ```
3. Restart Home Assistant
4. Test the integration thoroughly

## Code Style

### Python

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use type hints where appropriate
- Maximum line length: 88 characters (Black formatter)
- Use meaningful variable and function names

### Documentation

- Use docstrings for all public functions and classes
- Include parameter descriptions and return types
- Add comments for complex logic
- Update README if adding new features

### Example

```python
async def move_to_position(self, position: float) -> bool:
    """
    Move motor to specific position.

    Args:
        position: Target position 0-100 (0=open, 100=closed)

    Returns:
        True if command was successful, False otherwise
    """
    if not self.is_connected:
        return False

    # Implementation...
```

## Testing

### Manual Testing Checklist

Before submitting a PR, test these scenarios:

- [ ] Motor discovery via mDNS works
- [ ] Manual configuration works
- [ ] Authentication with PIN succeeds
- [ ] All motor commands work (open, close, stop, position)
- [ ] Position reporting is accurate
- [ ] Reconnection after network interruption
- [ ] Multiple motors can be added
- [ ] Integration survives Home Assistant restart
- [ ] Config flow validation works correctly

### Test Script

Use the provided test script:

```bash
python3 test_connection.py 192.168.1.150 1234
```

## Submitting Changes

### Pull Request Process

1. **Update documentation** if needed
2. **Add entry to CHANGELOG** (if exists)
3. **Test thoroughly** with real hardware
4. **Provide clear description** of changes
5. **Reference any issues** being fixed

### PR Description Template

```markdown
## Description
Brief description of what this PR does

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Code refactoring
- [ ] Performance improvement

## Testing
Describe how you tested these changes

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Tested with real hardware
- [ ] No breaking changes (or documented)
```

## Areas for Contribution

### High Priority

- **Testing**: Test with different motor models and firmware versions
- **Documentation**: Improve setup guides and troubleshooting
- **Error Handling**: Better error messages and recovery
- **Discovery**: Improve mDNS discovery reliability

### Feature Ideas

- Support for motor groups
- Push notifications from motors
- Position presets (favorite positions)
- Schedule management
- Integration with Home Assistant scenes
- Battery-powered motor support
- Multi-language support

### Bug Fixes

Check the [Issues](https://github.com/yourusername/somfy-poe/issues) page for known bugs.

## Code of Conduct

### Be Respectful

- Be welcoming to newcomers
- Be patient with questions
- Assume good intentions
- Disagree respectfully

### Communication

- Use clear, concise language
- Provide constructive feedback
- Ask questions if unclear
- Help others learn

## Protocol Changes

If you need to make changes to the protocol implementation:

1. Reference the [API documentation](../../SOMFY_POE_API_DOCUMENTATION.md)
2. Test thoroughly with real hardware
3. Document any deviations or new findings
4. Consider backward compatibility

## Security

### Reporting Security Issues

**Do not** open public issues for security vulnerabilities.

Instead, email: security@example.com (replace with actual email)

### Security Considerations

- Never hardcode credentials
- Validate all user input
- Use secure defaults
- Document security implications
- Follow Home Assistant security guidelines

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

## Questions?

- Check existing [Issues](https://github.com/yourusername/somfy-poe/issues)
- Start a [Discussion](https://github.com/yourusername/somfy-poe/discussions)
- Review the [documentation](README.md)

## Recognition

Contributors will be recognized in:
- README.md
- Release notes
- GitHub contributors page

Thank you for contributing to make this integration better! 🎉
