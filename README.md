# GPT Storytale

Create controllable story sequences with transformers that can be used in user-evaluation studies of text-to-visualisation pipelines.

&#x1F4D3; Accompanying paper: _<paper title; link to arXiv >_

&#x1F58B; By: [Add author names and affiliations here]

![Overview of the Graph-to-Text-Pipeline](figs/overview.png)

## Getting started

GPT Storytale has been tested on python 3.10. You will need to install the required packages. Using a virtual environment is recommended. e.g.
```bash
python3 -m venv myvenv          # set up the virtual env
source myvenv/bin/activate      # activate the virtual env (Linux) (On Windows: myvenv\Scripts\activate)
pip install -r requirements.txt # install the required packages
```

You will also need to set up your OpenAI API key. You can do this by creating a `.env` file in the root directory of the project and adding the following line:
```bash
OPENAI_API_KEY=your-api-key
```
(see `.env-template` for an example)

## Usage

To run the GPT Storytale system:

1. Generate a story sequence:
```bash
python src/generate_story.py --input your_input.json --output output_folder
```

2. Evaluate the generated sequences:
```bash
python src/evaluate.py --story_path output_folder
```

For detailed examples and parameter options, see the [examples](examples/) directory.

## Project Structure

```
GPT Storytale/
├── src/                # Source code
├── examples/           # Example inputs and outputs
├── tests/             # Test files
├── figs/              # Figures and diagrams
└── requirements.txt   # Project dependencies
```

## Features

- Generate coherent story sequences using transformer models
- Controllable narrative parameters
- Support for multiple story genres and styles
- Evaluation metrics for generated sequences
- Easy integration with visualization pipelines

## Acknowledgements

This project builds upon several open-source tools and libraries:

- [OpenAI GPT](https://openai.com/api/) - For text generation
- [Transformers](https://huggingface.co/transformers/) - Hugging Face's transformer models
- [NumPy](https://numpy.org/) - For numerical computations
- [Pandas](https://pandas.pydata.org/) - For data manipulation

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a new branch for your feature
3. Submit a pull request with a clear description of your changes

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.



