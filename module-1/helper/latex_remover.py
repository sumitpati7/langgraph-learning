import re

def clean_latex_math(text: str) -> str:
    """
    Removes/converts common LaTeX mathematical syntax into
    Rich Markdown compatible text.
    """

    # Replace common LaTeX symbols with Unicode equivalents
    replacements = {
        r"\times": "×",
        r"\cdot": "·",
        r"\div": "÷",
        r"\pm": "±",
        r"\mp": "∓",
        r"\le": "≤",
        r"\leq": "≤",
        r"\ge": "≥",
        r"\geq": "≥",
        r"\neq": "≠",
        r"\ne": "≠",
        r"\approx": "≈",
        r"\infty": "∞",
        r"\sqrt": "√",
        r"\pi": "π",
        r"\alpha": "α",
        r"\beta": "β",
        r"\gamma": "γ",
        r"\theta": "θ",
        r"\lambda": "λ",
        r"\mu": "μ",
        r"\sigma": "σ",
        r"\Delta": "Δ",
        r"\sum": "Σ",
        r"\prod": "Π",
    }

    for latex, symbol in replacements.items():
        text = text.replace(latex, symbol)

    # Remove math delimiters:
    # $$ equation $$
    text = text.replace("$$", "")

    # \( equation \)
    text = text.replace(r"\(", "")
    text = text.replace(r"\)", "")

    # \[ equation \]
    text = text.replace(r"\[", "")
    text = text.replace(r"\]", "")

    # Remove inline math delimiters: $x$
    text = re.sub(r"\$([^$]*)\$", r"\1", text)

    # Convert \boxed{value} -> value
    text = re.sub(
        r"\\boxed\{([^{}]*)\}",
        r"\1",
        text
    )

    # Convert fractions:
    # \frac{a}{b} -> a/b
    text = re.sub(
        r"\\frac\{([^{}]+)\}\{([^{}]+)\}",
        r"\1/\2",
        text
    )

    # Convert superscripts:
    # x^{2} -> x^2
    text = re.sub(
        r"\^\{([^{}]+)\}",
        r"^\1",
        text
    )

    # Convert subscripts:
    # x_{1} -> x_1
    text = re.sub(
        r"_\{([^{}]+)\}",
        r"_\1",
        text
    )

    # Remove remaining LaTeX commands:
    # \command -> command
    text = re.sub(
        r"\\[a-zA-Z]+",
        "",
        text
    )

    # Remove LaTeX braces
    text = text.replace("{", "")
    text = text.replace("}", "")

    # Normalize excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()