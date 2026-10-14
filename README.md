# Deepwick for lazygit

Deepwick colors for [lazygit](https://github.com/jesseduffield/lazygit).

> Deepwick is an unofficial theme derived from
> [Polywick Blue](https://vscode.polywickstudio.net) by Polywick Studio (MIT).
> Not affiliated with Polywick Studio.

![Deepwick in lazygit](screenshot.png)

## Install

Copy the `gui:` block from `deepwick.yml` into your lazygit `config.yml`
(`lazygit --print-config-dir` shows where it lives), merging with any `gui:`
settings you already have.

Or keep it separate and load both files:

```sh
mkdir -p "$(lazygit --print-config-dir)"
touch "$(lazygit --print-config-dir)/config.yml"
export LG_CONFIG_FILE="$(lazygit --print-config-dir)/config.yml,/path/to/deepwick.yml"
```

lazygit refuses to start if any file in `LG_CONFIG_FILE` is missing, hence
the `touch`.

## Notes

- Inactive panel borders use Overlay, so they recede; the focused panel is
  Blue and bold.
- All commit authors are Light Blue.

Tested with lazygit 0.62.2.

## License

MIT. See [LICENSE](LICENSE).
