# 卸载指南 / Uninstallation Guide

## Windows 可执行文件卸载 / Windows Executable Uninstallation

### 中文说明

FASTVOLT Windows 可执行文件是一个**便携式应用程序**，这意味着：
- ✅ 不需要安装过程
- ✅ 不会修改 Windows 注册表
- ✅ 不会在系统目录中创建文件
- ✅ 所有文件都包含在您解压的文件夹中

因此，"卸载" FASTVOLT 非常简单！

#### 卸载步骤

1. **关闭 FASTVOLT**
   - 关闭浏览器中的应用程序标签页
   - 如果 FASTVOLT.exe 仍在运行，关闭控制台窗口或在任务管理器中结束进程

2. **删除应用程序文件夹**
   - 找到您解压 FASTVOLT-Windows.zip 的文件夹
   - 右键单击该文件夹并选择"删除"
   - 或者按 `Shift + Delete` 永久删除（跳过回收站）

3. **完成！**
   - 不需要其他步骤
   - 应用程序已完全从您的计算机中删除

#### 应用程序创建的文件

FASTVOLT 在运行时会创建一些临时文件：

| 文件类型 | 位置 | 清理方式 |
|---------|------|---------|
| 临时解压文件 | Windows TEMP 目录 (`%TEMP%`) | 应用关闭时自动清理 |
| 上传的 FCS 文件临时副本 | 系统临时目录 | 应用关闭时自动清理 |
| 导出的 PDF 文件 | 浏览器下载文件夹 | 需要手动删除（如果不需要） |

**注意**：如果您强制终止应用程序（例如，通过任务管理器），可能会在 `%TEMP%` 目录中留下一些临时文件。这些文件通常以 `_MEI` 开头，可以安全删除。

#### 清理临时文件（可选）

如果您强制关闭了应用程序，可以手动清理临时文件：

1. 按 `Win + R` 打开运行对话框
2. 输入 `%TEMP%` 并按回车
3. 查找以 `_MEI` 开头的文件夹（这些是 PyInstaller 的临时文件）
4. 删除这些文件夹

或者，使用 Windows 磁盘清理工具：
1. 打开"设置" > "系统" > "存储"
2. 点击"临时文件"
3. 选择要清理的项目并点击"删除文件"

---

### English Instructions

The FASTVOLT Windows executable is a **portable application**, which means:
- ✅ No installation process required
- ✅ No Windows registry modifications
- ✅ No files created in system directories
- ✅ All files are contained in the folder you extracted

Therefore, "uninstalling" FASTVOLT is very simple!

#### Uninstallation Steps

1. **Close FASTVOLT**
   - Close the application tab in your browser
   - If FASTVOLT.exe is still running, close the console window or end the process in Task Manager

2. **Delete the Application Folder**
   - Locate the folder where you extracted FASTVOLT-Windows.zip
   - Right-click the folder and select "Delete"
   - Or press `Shift + Delete` to permanently delete (skip Recycle Bin)

3. **Done!**
   - No additional steps required
   - The application is completely removed from your computer

#### Files Created by the Application

FASTVOLT creates some temporary files during operation:

| File Type | Location | Cleanup Method |
|-----------|----------|----------------|
| Temporary extraction files | Windows TEMP directory (`%TEMP%`) | Automatically cleaned when app closes |
| Temporary copies of uploaded FCS files | System temporary directory | Automatically cleaned when app closes |
| Exported PDF files | Browser downloads folder | Manual deletion (if not needed) |

**Note**: If you force-quit the application (e.g., via Task Manager), some temporary files may remain in the `%TEMP%` directory. These files typically start with `_MEI` and can be safely deleted.

#### Cleaning Temporary Files (Optional)

If you force-closed the application, you can manually clean temporary files:

1. Press `Win + R` to open the Run dialog
2. Type `%TEMP%` and press Enter
3. Look for folders starting with `_MEI` (these are PyInstaller temporary files)
4. Delete these folders

Alternatively, use Windows Disk Cleanup:
1. Open "Settings" > "System" > "Storage"
2. Click "Temporary files"
3. Select items to clean and click "Remove files"

---

## 从源代码安装的卸载 / Uninstalling Source Installation

### 中文说明

如果您从源代码安装了 FASTVOLT（使用 Python），卸载过程取决于您的安装方式：

#### 使用虚拟环境（推荐）

如果您在虚拟环境中安装了依赖：
```bash
# 删除虚拟环境文件夹
rm -rf venv  # 或 env, .venv, 等您使用的文件夹名称
```

#### 全局安装

如果您全局安装了依赖，可以卸载它们：
```bash
pip uninstall -y fastapi uvicorn python-multipart flowio matplotlib pandas reportlab pyinstaller
```

#### 删除仓库

删除克隆的仓库文件夹：
```bash
cd ..
rm -rf FASTVOLT
```

### English Instructions

If you installed FASTVOLT from source (using Python), the uninstallation process depends on how you installed it:

#### Using Virtual Environment (Recommended)

If you installed dependencies in a virtual environment:
```bash
# Delete the virtual environment folder
rm -rf venv  # or env, .venv, whatever folder name you used
```

#### Global Installation

If you installed dependencies globally, you can uninstall them:
```bash
pip uninstall -y fastapi uvicorn python-multipart flowio matplotlib pandas reportlab pyinstaller
```

#### Delete Repository

Delete the cloned repository folder:
```bash
cd ..
rm -rf FASTVOLT
```

---

## 常见问题 / FAQ

### Q: 卸载后会丢失我的数据吗？/ Will I lose my data after uninstalling?
**A (中文)**: FASTVOLT 不存储任何数据。所有导出的 PDF 文件都保存在您的浏览器下载文件夹中。只要不删除下载文件夹中的 PDF 文件，您的数据就不会丢失。

**A (English)**: FASTVOLT does not store any data. All exported PDF files are saved in your browser's downloads folder. As long as you don't delete the PDF files in your downloads folder, you won't lose your data.

### Q: 卸载 FASTVOLT 会影响我的 Python 安装吗？/ Will uninstalling FASTVOLT affect my Python installation?
**A (中文)**: 不会。Windows 可执行文件是独立的，不依赖于系统 Python。如果您从源代码安装，只有在全局安装依赖时才会影响 Python 包（建议使用虚拟环境避免此问题）。

**A (English)**: No. The Windows executable is standalone and doesn't depend on system Python. If you installed from source, it only affects Python packages if you installed dependencies globally (using a virtual environment avoids this issue).

### Q: 我可以保留应用程序但删除临时文件吗？/ Can I keep the app but delete temporary files?
**A (中文)**: 可以。只需关闭应用程序，然后清理 Windows TEMP 目录中的临时文件。应用程序本身不受影响。

**A (English)**: Yes. Just close the application, then clean temporary files in the Windows TEMP directory. The application itself is not affected.

### Q: 卸载后如何重新安装？/ How do I reinstall after uninstalling?
**A (中文)**: 只需从 [Releases 页面](https://github.com/PanCodeInventory/FASTVOLT/releases)重新下载 FASTVOLT-Windows.zip 并解压即可。

**A (English)**: Just re-download FASTVOLT-Windows.zip from the [Releases page](https://github.com/PanCodeInventory/FASTVOLT/releases) and extract it.

---

## 反馈 / Feedback

如果您在卸载过程中遇到任何问题，请在 [GitHub Issues](https://github.com/PanCodeInventory/FASTVOLT/issues) 中报告。

If you encounter any issues during uninstallation, please report them in [GitHub Issues](https://github.com/PanCodeInventory/FASTVOLT/issues).
