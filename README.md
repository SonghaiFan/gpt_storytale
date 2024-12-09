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
pip install -r requirements.txt
```

3. Set up your OpenAI API key:
```bash
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

## Using the Web Interface

1. Start the web server:
```bash
python -m src.web.run
```

2. Open your browser and navigate to `http://localhost:5000`

3. Use the interface to:
   - Select the number of story tracks (1-5)
   - Choose the number of timepoints (2-5)
   - Generate coherent story sequences
   - View the generated stories in an interactive grid

## Monitoring and Logs

The application maintains detailed logs in the `logs` directory:

- `logs/app.log`: General application logs (INFO level and above)
  - Story generation attempts
  - Model initialization
  - Application flow

- `logs/error.log`: Error-specific logs
  - API errors
  - Text generation failures
  - System errors

Monitor logs in real-time:
```bash
tail -f logs/app.log    # For general logs
tail -f logs/error.log  # For error logs
```

## Using Your Own Story Configuration

1. Create a JSON file following the format in `examples/simple_story.json`
2. Run the generator with your config:
```bash
python -m src.examples.generate_story --config path/to/your/config.json
```

## Project Structure

```
gpt_storytale/
├── src/
│   ├── web/              # Web interface
│   │   ├── templates/    # HTML templates
│   │   ├── static/       # CSS and JavaScript
│   │   └── app.py       # Flask application
│   ├── models/          # Core models
│   ├── pipeline/        # Text generation pipeline
│   └── examples/        # Example scripts
├── logs/               # Application logs
├── stories/           # Generated stories
└── examples/          # Example configurations
```

## Features

- Web-based story generation interface
- Multi-track narrative generation
- Temporal coherence across story points
- OpenAI GPT integration
- Detailed logging system
- Configurable story parameters
- Interactive story visualization

## Dependencies

- Flask >= 2.0.0
- OpenAI >= 1.0.0
- Python-dotenv
- Langchain
- Pytest >= 7.0.0

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.



