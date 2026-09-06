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
| `--judge`    | `-j`  | string  | None    | Comma-separated judge model ids, overriding the config      |
| `--help`     | `-h`  | -       | -       | Show help message and exit                                 |

### Configuration File Structure

- **`models`** (array): List of model identifiers to test
- **`urls`** (array): List of website URLs to clone
- **`judges`** (array, optional): Judge models forming the scoring panel. `judge` (a single string) is accepted as shorthand.

Both `models` and `urls` arrays are required if using a config file. If no config file is provided, the script uses built-in default values.

### Judging

Each clone is scored by a **panel** of judges rather than a single model, and every judge's score is kept in its own column alongside the mean. Averaging across labs dilutes any one judge's preference for its own family, and keeping the per-judge scores means that bias can be measured rather than assumed away.

Note that the default panel overlaps the default roster (`gemini-3.8-flash` and `grok-4.6` both compete and judge). With frontier models spanning nearly every major lab there is no strong panel left fully outside the roster, so the overlap is recorded rather than hidden: compare a judge's scores for its own family against the other judges' to quantify it.

### Default Configuration

If no config file is specified, the benchmark uses these defaults:

**Models:**

- openai/gpt-6-astra-pro
- anthropic/claude-opus-5
- google/gemini-3.8-flash
- x-ai/grok-4.6
- qwen/qwen3.8-max-0902
- moonshotai/kimi-k3
- z-ai/glm-5v-turbo

**Judges:**

- google/gemini-3.8-flash
- x-ai/grok-4.6
- openai/gpt-6-astra

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
- **Total Tasks**: The benchmark runs `number_of_models × number_of_urls` total tasks, each costing one clone call plus one call per judge
- **Example**: 7 models × 20 URLs = 140 tasks = 140 clone calls + 420 judge calls

### Output

The benchmark saves results to:

- **Screenshots**: `data/og/` and `data/clone/` directories (organized by model)
- **Results**: `data/results.csv` containing scores and metadata

Key columns:

| Column | Meaning |
| --- | --- |
| `judge_score` | Mean across the judges that returned a usable score |
| `judge_score::<model>` | That judge's individual score, `NaN` if it failed |
| `judge_response::<model>` | That judge's full written analysis |
| `judge_models` | The panel used for the row |
| `error` | Why a row scored 0, e.g. a response missing the required blocks |

A model that ignores the mandatory `<HTML>`/`<CSS>` output format scores 0 with the reason recorded in `error`, rather than being dropped from the results.

#### Output Result Structure

```
data/
├── og/ # Original website screenshots
├── clone/ # AI-generated clone screenshots
└── results.csv # Benchmark results and scores
```

## Todos:

- [x] Test simple web ui cloning with simple image inputs.
- [ ] Evolve the test tasks to provide the llm assets like images and icons to use.
- [ ] Run training experiments on a small vlm with RL and judge reward.
