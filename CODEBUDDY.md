# camoufox-profile-manager Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-11-07

## Active Technologies

- uv, Python 3.9+ (backend), ES6+ JavaScript (frontend), HTML5, CSS3 (001-web-ui-migration)
- Flask 3.0+ REST API, TailwindCSS (CDN), localStorage (002-webui-enhancements)
- 国际化系统：翻译函数 t() + JSON 字典 (002-webui-enhancements)
- 主题系统：CSS 变量 + body class (002-webui-enhancements)

## Project Structure

```text
.venv/
backend/
  ├── models.py          # 数据模型（Profile, ProxyConfig）
  ├── session_manager.py # 会话管理（Camoufox 启动/停止）
  ├── validators.py      # 数据验证
  └── app.py            # Flask API 端点
frontend/
  ├── index.html        # 单页应用
  ├── app.js           # 前端逻辑（状态管理、API 调用）
  ├── style.css        # 样式（主题变量）
  └── translations/    # 国际化文件
      └── en.json      # 英文翻译字典
tests/
  # 手动测试（符合项目宪法）
```

## Commands

```bash
# 启动应用
uv run run.py

# 手动测试步骤
# 1. 主题切换：点击左下角主题按钮，验证颜色变化
# 2. 语言切换：点击语言按钮，验证文本翻译
# 3. 代理配置：选择协议，启用开关，验证保存和启动
# 4. 全屏模式：勾选全屏，验证输入框禁用和分辨率传递
# 5. Session 状态：启动后关闭浏览器，验证 UI 自动更新
```

## Code Style

### Python (Backend)
- 使用 dataclass 定义模型
- 验证器返回 (bool, str) 元组
- API 端点返回标准 JSON 错误格式
- 向后兼容性：from_dict 处理缺失字段

### JavaScript (Frontend)
- 使用原生 ES6+（无框架）
- 状态管理：中心化 state 对象
- 翻译函数：`t("中文原文")` 返回当前语言文本
- localStorage 存储：theme (light/dark), language (zh/en)
- 全屏检测：`window.screen.width/height`

### CSS
- 使用 CSS 变量定义主题颜色
- body.dark 类切换主题
- 保持 TailwindCSS CDN 方式

## Recent Changes

- 001-web-ui-migration: Added Python 3.9+ (backend), ES6+ JavaScript (frontend), HTML5, CSS3
- 002-webui-enhancements: 添加主题切换、国际化、代理协议、全屏修复

<!-- MANUAL ADDITIONS START -->

## 使用 UV

本项目使用 UV 作为包管理器、虚拟环境管理器和依赖安装器。
- 依赖安装：`uv pip install -r requirements.txt`
- 程序运行：`uv run run.py`
禁止直接使用 `pip` 和 `python` 命令。

<!-- MANUAL ADDITIONS END -->
