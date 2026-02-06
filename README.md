# FASTVOLT

FASTVOLT is a lightweight local web application designed for researchers to quickly extract voltage and compensation data from Flow Cytometry Standard (FCS) files and generate professional, lab-ready A4 PDF reports.

## Features

- **Fast Parsing**: Extract metadata from FCS files in seconds using `flowio`.
- **Instrument Awareness**: Automatically detects instrument model and serial numbers (optimized for CytoFLEX).
- **A4 PDF Reports**: Generates professional PDF records with institutional headers and space for manual entry.
- **Batch Export**: Process multiple files at once and download them as a ZIP archive.
- **Intuitive UI**: Simple drag-and-drop web interface.

## Quick Start (Windows Executable)

**For Windows users**, you can download the standalone executable from the [Releases](https://github.com/PanCodeInventory/FASTVOLT/releases) page:

1. Download `FASTVOLT-Windows.zip` from the latest release
2. Extract the ZIP file
3. Double-click `FASTVOLT.exe` to run the application
4. Your browser will open automatically at `http://127.0.0.1:8000`

No Python installation required!

### Uninstalling (Windows Executable)

Since FASTVOLT is a portable application, uninstallation is simple:

1. **Close the application** - Close your browser and terminate FASTVOLT.exe if it's running
2. **Delete the folder** - Delete the folder containing FASTVOLT.exe
3. **Done!** - No registry entries or system files are created

The application only creates temporary files during operation, which are automatically cleaned up when you close it.

**For detailed uninstallation instructions, see [UNINSTALL.md](UNINSTALL.md)**

## Installation from Source

### Prerequisites

- Python 3.10 or higher
- Chrome, Edge, or Safari browser

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/PanCodeInventory/FASTVOLT.git
   cd FASTVOLT
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Usage

Run the application using the following command:

```bash
python main.py
```

The application will automatically open your default browser to `http://127.0.0.1:8000`.

1. **Upload**: Drag and drop your `.fcs` files into the blue drop zone.
2. **Review**: Check the extracted instrument info and data tables on the screen.
3. **Export**: 
   - Click **Export PDF** on a specific file card for an individual report.
   - Click **Export All (PDF ZIP)** at the top to download reports for all loaded files.

## Building Executable

To build your own executable from source:

### Windows
```batch
build.bat
```

### Linux/macOS
```bash
chmod +x build.sh
./build.sh
```

The executable will be created in the `dist/` directory.

## Tech Stack

- **Backend**: FastAPI (Python)
- **PDF Engine**: ReportLab
- **Parsing**: flowio
- **Frontend**: Vue.js (CDN), Tailwind CSS

## License

This project is developed for laboratory record enhancement.

---

# FASTVOLT（中文说明）

FASTVOLT 是一个轻量级本地 Web 应用程序，专为研究人员设计，用于快速从流式细胞仪标准 (FCS) 文件中提取电压和补偿数据，并生成专业的、实验室就绪的 A4 PDF 报告。

## 快速开始（Windows 可执行文件）

**对于 Windows 用户**，您可以从 [Releases](https://github.com/PanCodeInventory/FASTVOLT/releases) 页面下载独立的可执行文件：

1. 从最新版本下载 `FASTVOLT-Windows.zip`
2. 解压 ZIP 文件
3. 双击 `FASTVOLT.exe` 运行应用程序
4. 浏览器将自动打开 `http://127.0.0.1:8000`

无需安装 Python！

### 卸载（Windows 可执行文件）

由于 FASTVOLT 是便携式应用程序，卸载非常简单：

1. **关闭应用程序** - 关闭浏览器并终止正在运行的 FASTVOLT.exe
2. **删除文件夹** - 删除包含 FASTVOLT.exe 的文件夹
3. **完成！** - 不会创建注册表项或系统文件

应用程序仅在运行期间创建临时文件，这些文件会在您关闭应用程序时自动清理。

**详细的卸载说明，请参阅 [UNINSTALL.md](UNINSTALL.md)**

## 从源码安装

### 前置要求

- Python 3.10 或更高版本
- Chrome、Edge 或 Safari 浏览器

### 安装步骤

1. **克隆仓库**：
   ```bash
   git clone https://github.com/PanCodeInventory/FASTVOLT.git
   cd FASTVOLT
   ```

2. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

### 使用方法

使用以下命令运行应用程序：

```bash
python main.py
```

应用程序将自动在您的默认浏览器中打开 `http://127.0.0.1:8000`。

1. **上传**：将您的 `.fcs` 文件拖放到蓝色拖放区域。
2. **查看**：在屏幕上检查提取的仪器信息和数据表。
3. **导出**：
   - 点击特定文件卡片上的 **Export PDF**（导出 PDF）以获取单个报告。
   - 点击顶部的 **Export All (PDF ZIP)**（导出全部）以下载所有已加载文件的报告。

## 构建可执行文件

要从源码构建自己的可执行文件：

### Windows
```batch
build.bat
```

### Linux/macOS
```bash
chmod +x build.sh
./build.sh
```

可执行文件将在 `dist/` 目录中创建。

## 发布新版本

查看 [RELEASE_CN.md](RELEASE_CN.md) 了解如何创建新的发布版本。
