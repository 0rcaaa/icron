"""Tests for file tool workspace security validation."""

import tempfile
from pathlib import Path

import pytest

from icron.agent.tools.filesystem import (
    WorkspaceSecurityError,
    validate_workspace_path,
    ReadFileTool,
    WriteFileTool,
    RenameFileTool,
    MoveFileTool,
    CopyFileTool,
    CreateDirTool,
)


class TestValidateWorkspacePath:
    """Tests for validate_workspace_path function."""

    def test_valid_path_within_workspace(self, tmp_path: Path):
        """Test that valid paths within workspace are allowed."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Create test file
        test_file = workspace / "test.txt"
        test_file.write_text("test")

        result = validate_workspace_path("test.txt", workspace, restrict_to_workspace=True)
        assert result == test_file.resolve()

    def test_path_escape_via_dotdot(self, tmp_path: Path):
        """Test that .. escape attempts are blocked."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        with pytest.raises(WorkspaceSecurityError, match="outside the allowed workspace"):
            validate_workspace_path("../secret.txt", workspace, restrict_to_workspace=True)

    def test_path_escape_via_absolute(self, tmp_path: Path):
        """Test that absolute paths outside workspace are blocked."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        with pytest.raises(WorkspaceSecurityError, match="outside the allowed workspace"):
            validate_workspace_path("/etc/passwd", workspace, restrict_to_workspace=True)

    def test_empty_path_rejected(self, tmp_path: Path):
        """Test that empty paths are rejected."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        with pytest.raises(WorkspaceSecurityError, match="Empty path"):
            validate_workspace_path("", workspace, restrict_to_workspace=True)

        with pytest.raises(WorkspaceSecurityError, match="Empty path"):
            validate_workspace_path("   ", workspace, restrict_to_workspace=True)

    def test_null_byte_rejected(self, tmp_path: Path):
        """Test that null bytes in paths are rejected."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        with pytest.raises(WorkspaceSecurityError, match="Invalid characters"):
            validate_workspace_path("test\x00.txt", workspace, restrict_to_workspace=True)

    def test_restriction_disabled(self, tmp_path: Path):
        """Test that paths are allowed when restriction is disabled."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Even escape paths should work
        result = validate_workspace_path("/tmp/test.txt", workspace, restrict_to_workspace=False)
        assert result == Path("/tmp/test.txt").resolve()

    def test_no_workspace_configured(self):
        """Test error when workspace is None but restriction is enabled."""
        with pytest.raises(FileNotFoundError, match="Workspace not configured"):
            validate_workspace_path("test.txt", None, restrict_to_workspace=True)

    def test_home_expansion(self, tmp_path: Path, monkeypatch):
        """Test that ~ expansion doesn't escape workspace."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # ~ will expand to something outside workspace
        with pytest.raises(WorkspaceSecurityError, match="outside the allowed workspace"):
            validate_workspace_path("~/secret.txt", workspace, restrict_to_workspace=True)


class TestReadFileToolSecurity:
    """Security tests for ReadFileTool."""

    @pytest.mark.asyncio
    async def test_read_blocks_escape(self, tmp_path: Path):
        """Test that reading files outside workspace is blocked."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        tool = ReadFileTool(workspace=workspace, restrict_to_workspace=True)
        result = await tool.execute(path="../secret.txt")

        assert "Error:" in result or "denied" in result.lower()

    @pytest.mark.asyncio
    async def test_read_allows_workspace_files(self, tmp_path: Path):
        """Test that files within workspace can be read."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        test_file = workspace / "allowed.txt"
        test_file.write_text("secret content")

        tool = ReadFileTool(workspace=workspace, restrict_to_workspace=True)
        result = await tool.execute(path="allowed.txt")

        assert "secret content" in result


class TestWriteFileToolSecurity:
    """Security tests for WriteFileTool."""

    @pytest.mark.asyncio
    async def test_write_blocks_escape(self, tmp_path: Path):
        """Test that writing files outside workspace is blocked."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        tool = WriteFileTool(workspace=workspace, restrict_to_workspace=True)
        result = await tool.execute(path="../escape.txt", content="malicious")

        assert "Error:" in result or "denied" in result.lower()
        assert not (tmp_path / "escape.txt").exists()


class TestMoveFileToolSecurity:
    """Security tests for MoveFileTool."""

    @pytest.mark.asyncio
    async def test_move_blocks_source_escape(self, tmp_path: Path):
        """Test that moving with source outside workspace is blocked."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        tool = MoveFileTool(workspace=workspace, restrict_to_workspace=True)
        result = await tool.execute(source="../secret.txt", destination="stolen.txt")

        assert "Error:" in result or "denied" in result.lower()

    @pytest.mark.asyncio
    async def test_move_blocks_dest_escape(self, tmp_path: Path):
        """Test that moving with destination outside workspace is blocked."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Create source file
        source_file = workspace / "source.txt"
        source_file.write_text("content")

        tool = MoveFileTool(workspace=workspace, restrict_to_workspace=True)
        result = await tool.execute(source="source.txt", destination="../escaped.txt")

        assert "Error:" in result or "denied" in result.lower()
        assert source_file.exists()  # Source should still exist


class TestCopyFileToolSecurity:
    """Security tests for CopyFileTool."""

    @pytest.mark.asyncio
    async def test_copy_blocks_source_escape(self, tmp_path: Path):
        """Test that copying with source outside workspace is blocked."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        tool = CopyFileTool(workspace=workspace, restrict_to_workspace=True)
        result = await tool.execute(source="/etc/passwd", destination="stolen.txt")

        assert "Error:" in result or "denied" in result.lower()


class TestRenameFileToolSecurity:
    """Security tests for RenameFileTool."""

    @pytest.mark.asyncio
    async def test_rename_blocks_escape(self, tmp_path: Path):
        """Test that renaming to path outside workspace is blocked."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Create source file
        source_file = workspace / "source.txt"
        source_file.write_text("content")

        tool = RenameFileTool(workspace=workspace, restrict_to_workspace=True)
        result = await tool.execute(old_path="source.txt", new_name="../escaped.txt")

        assert "Error:" in result or "denied" in result.lower()
        assert source_file.exists()


class TestCreateDirToolSecurity:
    """Security tests for CreateDirTool."""

    @pytest.mark.asyncio
    async def test_create_dir_blocks_escape(self, tmp_path: Path):
        """Test that creating directories outside workspace is blocked."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        tool = CreateDirTool(workspace=workspace, restrict_to_workspace=True)
        result = await tool.execute(path="../escape_dir")

        assert "Error:" in result or "denied" in result.lower()
        assert not (tmp_path / "escape_dir").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
