# 预警授权示例

**这个插件会真的触发警报音、通知与 TTS。** 请确认后再启用。

- `plugin.json` 里 `permissions.alerts: true` 是关键；
- `data.json` 的事件带 `isEew: true` / `active: true` / `eewKind: "警報"`，  
  因此按警报播报；把 `eewKind` 改成 `予報` 或去掉则按预报播报；
- `reportNum` 递增会触发「更新音」；`warnRegionCount` 显著增加会补播警报音；  
  去重规则与官方 EEW 完全一致（共用 `AudioService` 的报号记忆）；
- 测站带 `shindo` / `pga`，会并入主测站流参与阈值音效、震源推算与历史回放；
- 把 `active` 设为 `false` 可以只展示、不进预警链路。

停用插件即可立刻停止。宿主侧总开关 `allowPluginAlerts=false` 可一键让所有插件  
退回只读模式。

完整字段见 [docs/03-protocol.md](../../docs/03-protocol.md) 与  
[docs/05-security.md](../../docs/05-security.md)。

