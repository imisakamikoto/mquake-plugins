# 最小插件模板

```bash
cp -r templates/minimal my-plugin
# 改 my-plugin/plugin.json 里的 id / name
python tools/mqe.py validate my-plugin
python tools/mqe.py pack my-plugin
```

只有三样东西：`plugin.json`（清单）、`data.json`（数据）、`README.md`。
不加任何权限、不联网、不启进程，全平台可用。
