# oh-my-bilibili

一个简洁的 Bilibili 视频信息获取与下载库。

支持输入：
- `BV` 号
- `AV` 号
- B 站视频 URL
- `b23.tv` 短链

支持行为：
- 只获取视频信息（标题、简介、UP、时长等）
- 下载视频到指定路径（目录或文件路径）

## 安装

```bash
uv pip install .
```

## 快速开始

```python
from oh_my_bilibili import fetch

# 1) 仅获取视频信息
info = fetch("BV1xx411c7mD", cookie="")
print(info.title)
print(info.desc)
print(info.url)

# 2) 下载到目录（自动命名文件）
result = fetch(
    "https://www.bilibili.com/video/BV1xx411c7mD",
    cookie="SESSDATA=...",
    save_path="./downloads",
)
print(result.path)
print(result.quality_label)
```

## API

### `fetch(video, save_path=None, cookie="", prefer_quality=80, timeout=30.0, overwrite=True)`

- 当 `save_path is None` 时：返回 `VideoInfo`
- 当 `save_path` 有值时：返回 `DownloadResult`

### `get_video_info(video, cookie="", timeout=30.0)`

返回 `VideoInfo`。

### `download(video, save_path, cookie="", prefer_quality=80, timeout=30.0, overwrite=True)`

返回 `DownloadResult`。

## ffmpeg 依赖

Bilibili 通常返回 DASH 分离流（视频流 + 音频流），需要本地 `ffmpeg` 进行合并。  
若未安装 `ffmpeg`，会抛出 `FFmpegNotFoundError`。

## 异常

- `InvalidVideoIdentifierError`: 输入无法解析为 BV/AV/URL
- `ApiResponseError`: B 站接口失败或返回异常
- `DownloadError`: 下载或处理流程失败
- `FFmpegError` / `FFmpegNotFoundError`: ffmpeg 合并阶段失败
