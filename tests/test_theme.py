import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from deepwick_spec.ansi import runs
from deepwick_spec.check_port import check_port
from deepwick_spec.color import normalize_hex
from deepwick_spec.palette import load_palette
from deepwick_spec.tui import capture, tmux_available

REPO = Path(__file__).resolve().parents[1]
PALETTE = load_palette()
C = PALETTE.colors
requires_lazygit = pytest.mark.skipif(shutil.which("lazygit") is None, reason="requires lazygit")

EXPECTED = {
    "activeBorderColor": [C["blue"], "bold"],
    "inactiveBorderColor": [C["overlay"]],
    "searchingActiveBorderColor": [C["gold"], "bold"],
    "optionsTextColor": [C["blue"]],
    "selectedLineBgColor": [C["selection"]],
    "inactiveViewSelectedLineBgColor": [C["overlay"]],
    "cherryPickedCommitFgColor": [C["background"]],
    "cherryPickedCommitBgColor": [C["teal"]],
    "markedBaseCommitFgColor": [C["background"]],
    "markedBaseCommitBgColor": [C["yellow"]],
    "unstagedChangesColor": [C["red"]],
    "defaultFgColor": [C["foreground"]],
}


def theme():
    return yaml.safe_load((REPO / "deepwick.yml").read_text())["gui"]["theme"]


def test_theme_values():
    assert theme() == EXPECTED


@requires_lazygit
def test_keys_exist_in_lazygits_default_config():
    # BaseLoader: lazygit's default config contains a bare `=` value that safe_load rejects.
    defaults = yaml.load(subprocess.run(["lazygit", "--config"], capture_output=True, text=True, check=True).stdout, Loader=yaml.BaseLoader)
    assert set(theme()) <= set(defaults["gui"]["theme"])


def test_author_color():
    gui = yaml.safe_load((REPO / "deepwick.yml").read_text())["gui"]
    assert normalize_hex(gui["authorColors"]["*"]) == normalize_hex(C["lightBlue"])


@pytest.mark.skipif(not (tmux_available() and shutil.which("lazygit")), reason="requires tmux and lazygit")
def test_lazygit_renders_active_border_blue(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git = ["git", "-C", str(repo), "-c", "user.name=Deepwick", "-c", "user.email=deepwick@example.invalid"]
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    (repo / "a.txt").write_text("a\n")
    subprocess.run([*git, "add", "."], check=True)
    subprocess.run([*git, "commit", "-qm", "Initial commit"], check=True)
    (repo / "a.txt").write_text("b\n")
    extra = tmp_path / "test.yml"
    extra.write_text("disableStartupPopups: true\n")
    text = capture(
        f"lazygit -p {repo}",
        {"LG_CONFIG_FILE": f"{REPO / 'deepwick.yml'},{extra}", "XDG_CONFIG_HOME": str(tmp_path / "config"),
         "XDG_STATE_HOME": str(tmp_path / "state"), "GIT_CONFIG_GLOBAL": "/dev/null"},
        size=(120, 35),
        wait_for="Initial commit",
    )
    styles = runs(text)
    assert any(s["fg"] == C["blue"].lower() and s["bold"] for _, s in styles)
    assert any(s["bg"] == C["selection"].lower() for _, s in styles)


def test_port_conventions():
    assert check_port(REPO, PALETTE.allowed_hex()) == []
