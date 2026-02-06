# 快速参考 / Quick Reference

## 创建发布的最简步骤 / Simplest Steps to Create a Release

### 中文版本

```bash
# 1. 创建并推送标签
git tag -a v1.0.0 -m "初始发布"
git push origin v1.0.0

# 2. 等待几分钟，GitHub Actions 会自动完成以下工作：
#    - 安装 Python 和依赖
#    - 运行 PyInstaller 构建 exe
#    - 创建 ZIP 文件
#    - 发布到 Releases 页面

# 3. 完成！访问以下链接查看：
#    https://github.com/PanCodeInventory/FASTVOLT/releases
```

### English Version

```bash
# 1. Create and push a tag
git tag -a v1.0.0 -m "Initial release"
git push origin v1.0.0

# 2. Wait a few minutes, GitHub Actions will automatically:
#    - Install Python and dependencies
#    - Run PyInstaller to build exe
#    - Create ZIP file
#    - Publish to Releases page

# 3. Done! Visit:
#    https://github.com/PanCodeInventory/FASTVOLT/releases
```

## 本地测试构建 / Test Build Locally

### Windows
```batch
build.bat
dist\FASTVOLT.exe
```

### Linux/macOS
```bash
./build.sh
./dist/FASTVOLT
```

## 版本号规则 / Version Number Rules

- `v1.0.0` - 初始版本 / Initial release
- `v1.0.1` - 小修复 / Bug fix
- `v1.1.0` - 新功能 / New feature
- `v2.0.0` - 重大变更 / Breaking change

## 常见问题 / FAQ

### Q: 如何查看构建进度？/ How to check build progress?
A: 访问仓库的 Actions 标签页 / Visit the Actions tab in your repository

### Q: 构建失败怎么办？/ What if build fails?
A: 查看 Actions 日志，常见原因：
   - 缺少依赖：更新 requirements.txt
   - 路径错误：检查 build.spec
   Check Actions logs, common causes:
   - Missing dependencies: update requirements.txt
   - Path errors: check build.spec

### Q: exe 文件在哪里？/ Where is the exe file?
A: 在 GitHub Releases 页面下载 FASTVOLT-Windows.zip
   Download FASTVOLT-Windows.zip from GitHub Releases page

### Q: 可以手动触发构建吗？/ Can I manually trigger a build?
A: 可以！在 Actions 标签页点击 "Build and Release EXE" → "Run workflow"
   Yes! In Actions tab, click "Build and Release EXE" → "Run workflow"

## 文件说明 / File Descriptions

| 文件 / File | 用途 / Purpose |
|------------|---------------|
| build.spec | PyInstaller 配置文件 / PyInstaller config |
| build.bat | Windows 构建脚本 / Windows build script |
| build.sh | Linux/macOS 构建脚本 / Linux/macOS build script |
| .github/workflows/release.yml | 自动发布工作流 / Auto-release workflow |
| RELEASE.md | 英文详细指南 / English detailed guide |
| RELEASE_CN.md | 中文详细指南 / Chinese detailed guide |
| IMPLEMENTATION_SUMMARY.md | 技术实现总结 / Technical summary |

## 更多帮助 / More Help

- 详细的英文指南：查看 RELEASE.md
- 详细的中文指南：查看 RELEASE_CN.md
- 技术细节：查看 IMPLEMENTATION_SUMMARY.md

- Detailed English guide: See RELEASE.md
- Detailed Chinese guide: See RELEASE_CN.md
- Technical details: See IMPLEMENTATION_SUMMARY.md
