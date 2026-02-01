# mdformat-pandoc

[![PyPI version](https://badge.fury.io/py/mdformat-pandoc.svg)](https://badge.fury.io/py/mdformat-pandoc)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An [mdformat](https://github.com/hukkin/mdformat) plugin for **Pandoc-flavored Markdown**.

## Features

- **Pipe Tables**: Aligns columns and formats content.
- **Fenced Divs**: `::: {.class #id}` with robust nesting.
- **Definition Lists**: Indented definitions.
- **Footnotes**: Inline and block footnotes.
- **Math**: Inline `$E=mc^2$` and display `$$...$$`.
- **Front Matter**: Preserved.

## Installation

```bash
pip install mdformat-pandoc
```

## Usage

```bash
mdformat --extensions pandoc path/to/file.md
```
