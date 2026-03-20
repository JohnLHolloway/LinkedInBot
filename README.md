# LinkedInBot

Discord bot that converts text into LinkedIn corporate jargon and puts everyone in suits.

## Usage

- **@mention with text** → rewrites as corporate LinkedIn speak
- **@mention on an image** → puts everyone in business suits
- **/generate** → pick from multiple modes (corporate, motivational, humble brag, thought leader, suits, etc.)
- **/help** → show available modes

## Setup

1. Copy `.env.example` to `.env` and fill in your tokens
2. `docker compose up -d --build`

## Development

```bash
pip install -r requirements.txt
python -m pytest -q
python bot.py
```
