# Clone UI Bench

A LLM as a Judge bench to evaluate web UI cloning ability using a multimodal judge.

![alt text](./resources/image.png)

## Requirements

- Python 3.12+
- uv
- API keys for the AI models you want to test

## Installation

1. Install dependencies:

```bash
uv pip install .
```

2. Set up environment variables in `.env` file with your API keys.

## Usage

### Basic Usage

Run the benchmark with default settings (3 parallel requests, using built-in models and URLs):

```<bash
python -m src.main
```

### Command Line Arguments

The script accepts the following command line arguments:

| Argument     | Short | Type    | Default | Description                                                |
| ------------ | ----- | ------- | ------- | ---------------------------------------------------------- |
| `--parallel` | `-p`  | integer | 3       | Number of parallel requests to run simultaneously          |
| `--config`   | `-c`  | string  | None    | Path to JSON configuration file containing models and URLs |
| `--help`     | `-h`  | -       | -       | Show help message and exit                                 |

### Configuration File Structure

- **`models`** (array): List of model identifiers to test
- **`urls`** (array): List of website URLs to clone

Both `models` and `urls` arrays are required if using a config file. If no config file is provided, the script uses built-in default values.

### Default Configuration

If no config file is specified, the benchmark uses these defaults:

**Models:**

- anthropic/claude-sonnet-4
- anthropic/claude-opus-4.1
- google/gemini-2.5-flash-image-preview
- google/gemini-2.5-pro
- z-ai/glm-4.5v
- openai/gpt-5
- openai/gpt-5-mini
- openai/o3-pro
- bytedance/ui-tars-1.5-7b
- x-ai/grok-4
- baidu/ernie-4.5-vl-424b-a47b
- qwen/qwen3-vl-235b-a22b-instruct
- qwen/qwen3-vl-235b-a22b-thinking

**URLs:**

- https://stripe.com
- https://airbnb.com
- https://github.com
- https://dribbble.com
- https://medium.com
- https://spotify.com
- https://netflix.com
- https://apple.com
- https://google.com
- https://twitter.com
- https://linkedin.com
- https://instagram.com
- https://youtube.com
- https://amazon.com
- https://slack.com
- https://discord.com
- https://figma.com
- https://notion.so
- https://vercel.com
- https://tailwindcss.com

### Performance Considerations

- **Parallel Requests**: Higher parallel request counts can speed up execution but may hit API rate limits or consume more system resources
- **Total Tasks**: The benchmark runs `number_of_models × number_of_urls` total tasks
- **Example**: 13 models × 20 URLs = 260 total tasks

### Output

The benchmark saves results to:

- **Screenshots**: `data/og/` and `data/clone/` directories (organized by model)
- **Results**: `data/results.csv` containing scores and metadata

#### Output Result Structure

```
data/
├── og/ # Original website screenshots
├── clone/ # AI-generated clone screenshots
└── results.csv # Benchmark results and scores
```
