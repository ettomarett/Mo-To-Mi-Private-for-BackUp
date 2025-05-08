from setuptools import setup, find_packages

setup(
    name="agentskeleton",
    version="0.1.0",
    description="Framework for building and managing AI agents",
    author="Your Name",
    packages=find_packages(include=['agentskeleton', 'agentskeleton.*', 
                                  'agents', 'agents.*',
                                  'core', 'core.*',
                                  'mcp_framework', 'mcp_framework.*']),
    install_requires=[
        "google-adk",
        "python-dotenv",
        "requests",
        "azure-ai-inference>=1.0.0b9",
        "tiktoken>=0.5.2",
        # Additional dependencies
        "pytest",
        "asyncio",
        "typing",
    ],
    python_requires='>=3.8',
) 