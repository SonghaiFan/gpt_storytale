# GPT Storytale

Create controllable story sequences with transformers that can be used in user-evaluation studies of text-to-visualisation pipelines.

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/[username]/gpt-storytale.git
cd gpt-storytale
```

2. Set up a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

3. Set up your OpenAI API key:
```bash
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

4. Run the example story generator:
```bash
python -m src.examples.generate_story
```

## Using Your Own Story Configuration

1. Create a JSON file following the format in `examples/simple_story.json`
2. Run the generator with your config:
```bash
python -m src.examples.generate_story --config path/to/your/config.json
```

[Rest of the README content...]



