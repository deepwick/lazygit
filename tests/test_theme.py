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
    "authorColors": {"*": C["lightBlue"]},
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
    assert normalize_hex(theme()["authorColors"]["*"]) == normalize_hex(C["lightBlue"])


def theme_copy(tmp_path):
    # lazygit rewrites outdated config files in place; never hand it the repo's copy.
    copy = tmp_path / "deepwick.yml"
    shutil.copy(REPO / "deepwick.yml", copy)
    return copy


def lazygit_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git = ["git", "-C", str(repo), "-c", "user.name=Deepwick", "-c", "user.email=deepwick@example.invalid"]
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    (repo / "a.txt").write_text("a\n")
    subprocess.run([*git, "add", "."], check=True)
    subprocess.run([*git, "commit", "-qm", "Initial commit"], check=True)
    return repo


@pytest.mark.skipif(not (tmux_available() and shutil.which("lazygit")), reason="requires tmux and lazygit")
def test_lazygit_needs_no_config_migration(tmp_path):
    copy = theme_copy(tmp_path)
    extra = tmp_path / "test.yml"
    extra.write_text("disableStartupPopups: true\n")
    capture(
        f"lazygit -p {lazygit_repo(tmp_path)}",
        {"LG_CONFIG_FILE": f"{copy},{extra}", "XDG_CONFIG_HOME": str(tmp_path / "config"),
         "XDG_STATE_HOME": str(tmp_path / "state"), "GIT_CONFIG_GLOBAL": "/dev/null"},
        size=(120, 35),
        wait_for="Initial commit",
    )
    assert copy.read_text() == (REPO / "deepwick.yml").read_text()


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
        {"LG_CONFIG_FILE": f"{theme_copy(tmp_path)},{extra}", "XDG_CONFIG_HOME": str(tmp_path / "config"),
         "XDG_STATE_HOME": str(tmp_path / "state"), "GIT_CONFIG_GLOBAL": "/dev/null"},
        size=(120, 35),
        wait_for="Initial commit",
    )
    styles = runs(text)
    assert any(s["fg"] == C["blue"].lower() and s["bold"] for _, s in styles)
    assert any(s["bg"] == C["selection"].lower() for _, s in styles)


def test_port_conventions():
    assert check_port(REPO, PALETTE.allowed_hex()) == []


@pytest.mark.skipif(not (tmux_available() and shutil.which("lazygit")), reason="requires tmux and lazygit")
def test_readme_install_block_works_on_clean_config(tmp_path):
    import re

    readme = (REPO / "README.md").read_text()
    block = re.search(r"Or keep it separate.*?```sh\n(.*?)```", readme, re.S).group(1)
    block = block.replace("/path/to/deepwick.yml", str(theme_copy(tmp_path)))
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    git = ["git", "-C", str(repo), "-c", "user.name=Deepwick", "-c", "user.email=deepwick@example.invalid"]
    (repo / "a.txt").write_text("a\n")
    subprocess.run([*git, "add", "."], check=True)
    subprocess.run([*git, "commit", "-qm", "Initial commit"], check=True)
    script = tmp_path / "install.sh"
    script.write_text(block + f"\nexec lazygit -p {repo}\n")
    env = {"XDG_CONFIG_HOME": str(tmp_path / "config"), "XDG_STATE_HOME": str(tmp_path / "state"), "GIT_CONFIG_GLOBAL": "/dev/null"}
    text = capture(f"bash {script}", env, size=(120, 35), wait_for="Status")  # first-run popup may cover panels
    assert "Status" in text
