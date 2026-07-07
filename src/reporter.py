from pathlib import Path

from jinja2 import Environment, FileSystemLoader

VIEWS_DIR = Path(__file__).resolve().parent.parent / "views"

_env = Environment(loader=FileSystemLoader(str(VIEWS_DIR)))


def render_report(videos):
    template = _env.get_template("trending_report.html")
    return template.render(videos=videos)
