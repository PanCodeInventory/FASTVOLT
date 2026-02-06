# 发布指南（中文）

本文档说明如何创建带有 Windows 可执行文件的新版本。

## 创建发布版本

发布过程通过 GitHub Actions 自动化。按照以下步骤操作：

### 1. 准备发布

1. 确保所有更改已提交并测试通过
2. 如需要，更新版本信息
3. 将更改合并到主分支

### 2. 创建版本标签

标签应遵循语义化版本控制（例如：`v1.0.0`、`v1.1.0`、`v2.0.0`）。

**使用 Git 命令行：**

```bash
# 创建并推送标签
git tag -a v1.0.0 -m "发布版本 1.0.0"
git push origin v1.0.0
```

**使用 GitHub 网页界面：**

1. 访问 GitHub 上的仓库
2. 点击右侧栏的 "Releases"（发布）
3. 点击 "Create a new release"（创建新发布）
4. 点击 "Choose a tag"（选择标签）
5. 输入版本标签（例如 `v1.0.0`）并点击 "Create new tag"（创建新标签）
6. 填写发布标题和描述
7. 点击 "Publish release"（发布）

### 3. 自动构建过程

当您推送以 `v` 开头的标签时，GitHub Actions 工作流将自动：

1. 设置带有 Python 3.10 的 Windows 环境
2. 从 `requirements.txt` 安装所有依赖项
3. 使用 PyInstaller 构建可执行文件
4. 创建 ZIP 压缩包（`FASTVOLT-Windows.zip`）
5. 将 ZIP 文件作为发布资产上传
6. 生成发布说明

### 4. 验证发布

1. 转到仓库的 "Actions"（操作）选项卡
2. 检查 "Build and Release EXE" 工作流是否成功完成
3. 转到 "Releases"（发布）页面
4. 验证 `FASTVOLT-Windows.zip` 已附加到发布版本

## 手动触发工作流

您也可以手动触发构建工作流而不创建发布：

1. 转到 "Actions"（操作）选项卡
2. 选择 "Build and Release EXE" 工作流
3. 点击 "Run workflow"（运行工作流）
4. 选择分支并点击 "Run workflow"（运行工作流）

这将构建可执行文件并将其作为工件上传（而非发布）。

## 本地测试

在创建发布之前，您可以在本地测试构建：

### Windows
```batch
build.bat
```

### Linux/macOS
```bash
chmod +x build.sh
./build.sh
```

可执行文件将位于 `dist/` 目录中。

## 故障排除

### GitHub Actions 中构建失败

1. 检查 "Actions" 选项卡中的工作流日志
2. 常见问题：
   - 缺少依赖项：更新 `requirements.txt`
   - 缺少文件：更新 `build.spec` 以包含它们
   - 导入错误：在 `build.spec` 的 `hiddenimports` 中添加缺少的模块

### 可执行文件无法运行

1. 首先使用构建脚本在本地测试
2. 检查所有数据文件（frontend 目录）是否包含在内
3. 验证隐藏导入是否在 `build.spec` 中列出

## 版本编号指南

使用语义化版本控制（主版本号.次版本号.修订号）：

- **主版本号**：破坏性更改
- **次版本号**：新功能，向后兼容
- **修订号**：错误修复，向后兼容

示例：
- `v1.0.0` - 初始发布
- `v1.0.1` - 错误修复
- `v1.1.0` - 新功能
- `v2.0.0` - 破坏性更改

## 快速开始

最简单的发布方式：

1. 在本地测试您的更改：
   ```bash
   python main.py
   ```

2. 提交并推送到主分支

3. 创建并推送标签：
   ```bash
   git tag -a v1.0.0 -m "初始发布"
   git push origin v1.0.0
   ```

4. 等待几分钟，GitHub Actions 将自动构建并创建发布

5. 在 GitHub 的 Releases 页面下载 `FASTVOLT-Windows.zip`

就这么简单！
