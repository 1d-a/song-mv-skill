# song-mv-skill

把一首歌做成竖屏歌曲 MV（1080×1920，30fps，原曲音轨），用于抖音、快手、B 站。
**画面里没有人物**：靠物件、风景、天气、文字、镜头运动和踩点特效来讲歌词里的故事，并且唱歌的部分画面也要持续变化。

## 流程

1. 输入：歌曲音频、歌词、开场标题、副标题
2. 自动对齐歌词，每个字按实际演唱时间出现（faster-whisper + 拼音对齐）
3. 按歌词写分镜 `storyboard.json`（关键词自动起草，再人工/AI 精修）
4. 出三种方案图（水墨江湖 / 蜡笔童画 / 剪纸月夜），每种 8 张关键帧，也可以附带短片段
5. 选定一种方案后渲染完整视频，分段缓存，中断后可以接着渲染

## 快速开始

```bash
./setup.sh
mkdir -p projects/mysong && cp 歌.mp3 projects/mysong/song.mp3 && cp 歌词.txt projects/mysong/lyrics.txt
cat > projects/mysong/project.json <<'J'
{"audio": "song.mp3", "lyrics_file": "lyrics.txt", "title": "木剑破衫", "subtitle": "一把木剑 一身破衫",
 "credits": "词曲 · 演唱", "seal": "神仙在此"}
J
PY=.venv/bin/python
$PY -m mvkit.align projects/mysong                 # -> lyrics.json（逐字时间）
$PY -m mvkit.storyboard projects/mysong --draft    # -> storyboard.draft.json，修改后另存为 storyboard.json
$PY -m mvkit.storyboard projects/mysong            # 检查分镜：列出时间线，报告没有画面变化的段落
$PY -m mvkit.preview projects/mysong --clip 8      # -> out/方案A_水墨江湖.jpg … 以及 8 秒片段
$PY -m mvkit.render projects/mysong --style paper  # 完整成片 -> out/<标题>_剪纸月夜.mp4
```

加 `--start 0 --dur 33` 只渲染前 33 秒；用 `--stills 12,20,31 --sheet x.png` 抽几帧快速查看效果。

## 三种方案

| key | 名称 | 画面 | 歌词 |
|---|---|---|---|
| `ink` | 水墨江湖 | 宣纸、层叠水墨山视差、流雾、红日，场景切换时有墨笔扫过 | 竖排毛笔字，逐字晕开 |
| `crayon` | 蜡笔童画 | 蜡笔绘本，每个 scene 翻一页，线条抖动 | 底部蜡笔手写字加下划线进度 |
| `paper` | 剪纸月夜 | 层叠剪纸月夜、悬崖吊桥村舍、炊烟、霜花，景深推拉 | 红色剪纸字块翻转落下 |

## 分镜语法（storyboard.json）

```json
{"scenes": [{"start": 0, "mood": "default"}, {"start": "L3-0.2", "mood": "night"}],
 "events": [
  {"type": "prop", "shape": "sword", "start": "L1-0.4", "lift": "L2.2", "end": "L3.end"},
  {"type": "prop", "shape": "glyph", "text": "哈", "action": "swarm", "start": "L1", "end": "L1.end", "hits": "chars:L1"},
  {"type": "thunder", "start": "L7.3"},
  {"type": "fireworks", "start": "L8", "end": "L8.end+1", "hits": "chars:L8"}]}
```

- 时间可以写秒数，也可以引用歌词：`L3` 是第 3 行开始，`L3.2` 是第 3 行第 2 个字，`L3.end` 是第 3 行结束。还可以用 `T0`（第一句）、`drop`（鼓点进来）、`end`，都能加减偏移，例如 `L3.2+0.4`
- `hits`（触发时刻）：可以写时间列表，也可以写 `chars:L5`（第 5 行每个字）、`beats:A~B`（区间内每拍）、`strong:A~B`（区间内重拍）
- mood：`default` / `day` / `dawn` / `dusk` / `night` / `storm`，决定纸色、天色和日月
- event 类型：`prop`（sword / pouch / cloak / fire / glyph，动作 rise / sway / drop / swarm）、`clouds`、`dim`、`village`、`thread`、`burst`、`thunder`、`scatter`、`fireworks`、`lanterns`、`stamp`、`weather`（rain / snow / petals / embers）、`zoom`、`lyricfx`（副歌/高潮歌词特效，tone = bold / fragile / tragic / rise / final，目前蜡笔童画支持）

完整示例见 `examples/mujian/`（《木剑破衫》的全曲分镜）。Agent 的操作规范见 `.agents/skills/song-mv/SKILL.md`。

字体（fonts/）来自开源字体：马善政毛笔、刘建毛草、志莽行书、站酷小薇、思源宋体/黑体、霞鹜文楷。
