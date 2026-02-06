# Release Guide for FASTVOLT

This document explains how to create a new release with Windows executable.

## Creating a Release

The release process is automated through GitHub Actions. Follow these steps:

### 1. Prepare Your Release

1. Ensure all changes are committed and tested
2. Update version information if needed
3. Merge changes to the main branch

### 2. Create a Version Tag

Tags should follow semantic versioning (e.g., `v1.0.0`, `v1.1.0`, `v2.0.0`).

**Using Git Command Line:**

```bash
# Create and push a tag
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

**Using GitHub Web Interface:**

1. Go to your repository on GitHub
2. Click on "Releases" (right sidebar)
3. Click "Create a new release"
4. Click "Choose a tag"
5. Type your version tag (e.g., `v1.0.0`) and click "Create new tag"
6. Fill in the release title and description
7. Click "Publish release"

### 3. Automated Build Process

Once you push a tag starting with `v`, the GitHub Actions workflow will automatically:

1. Set up a Windows environment with Python 3.10
2. Install all dependencies from `requirements.txt`
3. Build the executable using PyInstaller
4. Create a ZIP archive (`FASTVOLT-Windows.zip`)
5. Upload the ZIP as a release asset
6. Generate release notes

### 4. Verify the Release

1. Go to the "Actions" tab in your repository
2. Check that the "Build and Release EXE" workflow completed successfully
3. Go to the "Releases" page
4. Verify that `FASTVOLT-Windows.zip` is attached to the release

## Manual Workflow Trigger

You can also manually trigger the build workflow without creating a release:

1. Go to the "Actions" tab
2. Select "Build and Release EXE" workflow
3. Click "Run workflow"
4. Choose the branch and click "Run workflow"

This will build the executable and upload it as an artifact (not as a release).

## Local Testing

Before creating a release, you can test the build locally:

### Windows
```batch
build.bat
```

### Linux/macOS
```bash
chmod +x build.sh
./build.sh
```

The executable will be in the `dist/` directory.

## Troubleshooting

### Build Fails in GitHub Actions

1. Check the workflow logs in the "Actions" tab
2. Common issues:
   - Missing dependencies: Update `requirements.txt`
   - Missing files: Update `build.spec` to include them
   - Import errors: Add missing modules to `hiddenimports` in `build.spec`

### Executable Doesn't Work

1. Test locally first using the build scripts
2. Check that all data files (frontend directory) are included
3. Verify hidden imports are listed in `build.spec`

## Version Numbering Guidelines

Use semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes
- **MINOR**: New features, backwards compatible
- **PATCH**: Bug fixes, backwards compatible

Examples:
- `v1.0.0` - Initial release
- `v1.0.1` - Bug fix
- `v1.1.0` - New feature
- `v2.0.0` - Breaking changes
