#!/usr/bin/env python3
"""Mirror a selected Ethan workspace subtree into the Box outputs area.

Default destination:
All Files/Andres_Obsidian_Notes_Box/tamu_flow_loop/analyzing_operational_data
  / ethans runs

Critical rule:
- Never upload to the raw-data Box folder 246873664013.

Default source root:
- the local ethan_runs repo root

Default exclusions keep the Box mirror useful for local ParaView work without
shipping local control state and scratch-only directories.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_ROOT = REPO_ROOT
DEFAULT_BOX_FOLDER_ID = "385169164073"
DEFAULT_BOX_FOLDER_PATH = (
    "All Files/Andres_Obsidian_Notes_Box/tamu_flow_loop/analyzing_operational_data"
)
RAW_DATA_BOX_FOLDER_ID = "246873664013"
DEFAULT_REMOTE_SUBFOLDER = "ethans runs"
DEFAULT_AUTH_CACHE = Path.home() / ".box" / "oauth_token_cache.json"
DEFAULT_ENV_PATH = Path.home() / ".box" / "box_environments.json"
DEFAULT_SMALL_UPLOAD_MAX_BYTES = 50 * 1024 * 1024
AUTH_REFRESH_SKEW_SECONDS = 300
DEFAULT_EXCLUDE_DIRS = (
    ".git",
    ".agent",
    ".agents",
    ".codex",
    "cache",
    "figures",
    "figures_rendered",
    "tmp",
    "tmp_extract",
    "linked_cases",
    "__pycache__",
    ".pytest_cache",
)
DEFAULT_EXCLUDE_NAMES = (".DS_Store",)


@dataclass
class RemoteItem:
    item_id: str
    item_type: str
    name: str
    size: int | None = None
    etag: str | None = None


@dataclass
class UploadStats:
    files_considered: int = 0
    bytes_considered: int = 0
    folders_created: int = 0
    uploaded_new: int = 0
    uploaded_overwrite: int = 0
    skipped_same: int = 0
    skipped_changed: int = 0
    skipped_symlink: int = 0


class JsonTokenStorage:
    """Minimal token-storage adapter compatible with BoxOAuth."""

    def __init__(self, path: Path):
        self.path = path

    def store(self, token: Any) -> None:
        now_ms = int(time.time() * 1000)
        expires_in = int(getattr(token, "expires_in", 0) or 0)
        payload = {
            "accessToken": getattr(token, "access_token", None),
            "refreshToken": getattr(token, "refresh_token", None),
            "accessTokenTTLMS": expires_in * 1000,
            "acquiredAtMS": now_ms,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def get(self) -> Any | None:
        imports = box_imports()
        AccessToken = imports["AccessToken"]
        data = self._read_cache()
        if not data:
            return None
        expires_in = self.seconds_remaining()
        return AccessToken(
            access_token=data.get("accessToken"),
            refresh_token=data.get("refreshToken"),
            expires_in=max(0, expires_in if expires_in is not None else 0),
        )

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()

    def _read_cache(self) -> dict[str, Any] | None:
        if not self.path.exists():
            return None
        return json.loads(self.path.read_text(encoding="utf-8"))

    def seconds_remaining(self) -> int | None:
        data = self._read_cache()
        if not data:
            return None
        acquired_ms = int(data.get("acquiredAtMS") or 0)
        ttl_ms = int(data.get("accessTokenTTLMS") or 0)
        if acquired_ms <= 0 or ttl_ms <= 0:
            return None
        expires_at = (acquired_ms + ttl_ms) / 1000.0
        return int(expires_at - time.time())


def box_imports() -> dict[str, Any]:
    try:
        from box_sdk_gen.box.oauth import BoxOAuth, OAuthConfig
        from box_sdk_gen.client import BoxClient
        from box_sdk_gen.managers.folders import CreateFolderParent
        from box_sdk_gen.managers.uploads import (
            UploadFileAttributes,
            UploadFileAttributesParentField,
            UploadFileVersionAttributes,
        )
        from box_sdk_gen.schemas.access_token import AccessToken
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Box SDK is not installed in this Python environment. "
            "Install the `box-sdk-gen` package inside the job-local virtualenv first."
        ) from exc
    return {
        "BoxOAuth": BoxOAuth,
        "OAuthConfig": OAuthConfig,
        "BoxClient": BoxClient,
        "CreateFolderParent": CreateFolderParent,
        "UploadFileAttributes": UploadFileAttributes,
        "UploadFileAttributesParentField": UploadFileAttributesParentField,
        "UploadFileVersionAttributes": UploadFileVersionAttributes,
        "AccessToken": AccessToken,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-root",
        default=str(DEFAULT_SOURCE_ROOT),
        help=f"Local folder to mirror. Default: {DEFAULT_SOURCE_ROOT}",
    )
    parser.add_argument(
        "--box-folder-id",
        default=DEFAULT_BOX_FOLDER_ID,
        help=f"Destination Box folder ID. Default: {DEFAULT_BOX_FOLDER_ID}",
    )
    parser.add_argument(
        "--remote-subfolder",
        default=DEFAULT_REMOTE_SUBFOLDER,
        help=f"Subfolder to create under the Box destination root. Default: {DEFAULT_REMOTE_SUBFOLDER!r}",
    )
    parser.add_argument(
        "--auth-cache-path",
        default=str(DEFAULT_AUTH_CACHE),
        help=f"Path to the Box OAuth token cache JSON. Default: {DEFAULT_AUTH_CACHE}",
    )
    parser.add_argument(
        "--box-env-path",
        default=str(DEFAULT_ENV_PATH),
        help=f"Path to the Box environment config JSON. Default: {DEFAULT_ENV_PATH}",
    )
    parser.add_argument(
        "--client-id",
        default=None,
        help="Optional Box client ID override. Defaults to ~/.box/box_environments.json",
    )
    parser.add_argument(
        "--client-secret",
        default=None,
        help="Optional Box client secret override. Defaults to ~/.box/box_environments.json",
    )
    parser.add_argument(
        "--small-upload-max-bytes",
        type=int,
        default=DEFAULT_SMALL_UPLOAD_MAX_BYTES,
        help="Size threshold above which chunked upload is used. Default: 50 MiB",
    )
    parser.add_argument(
        "--exclude-dir",
        action="append",
        default=[],
        help="Additional directory basename to exclude. May be repeated.",
    )
    parser.add_argument(
        "--exclude-name",
        action="append",
        default=[],
        help="Additional filename basename to exclude. May be repeated.",
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include dotfiles and dot-directories. Default is to skip them.",
    )
    parser.add_argument(
        "--follow-symlinks",
        action="store_true",
        help="Follow symlinked directories/files. Default is to skip symlinks.",
    )
    parser.add_argument(
        "--overwrite-changed",
        action="store_true",
        help="Upload a new Box version when a same-name file exists with a different size.",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=None,
        help="Optional cap on the number of local files scanned, for smoke testing.",
    )
    parser.add_argument(
        "--manifest-path",
        default=None,
        help="Optional JSON path for the summary manifest.",
    )
    parser.add_argument(
        "--inventory-only",
        action="store_true",
        help="Scan local files and write the manifest without talking to Box.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Perform uploads and folder creation. Default is dry-run.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Explicitly request dry-run mode.",
    )
    return parser.parse_args()


def format_bytes(num_bytes: int) -> str:
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    value = float(num_bytes)
    for unit in units:
        if value < 1024.0 or unit == units[-1]:
            return f"{value:.1f}{unit}"
        value /= 1024.0
    return f"{num_bytes}B"


def log(message: str) -> None:
    print(message, flush=True)


def resolve_box_client_credentials(args: argparse.Namespace) -> tuple[str, str]:
    if args.client_id and args.client_secret:
        return args.client_id, args.client_secret
    env_path = Path(args.box_env_path).expanduser()
    if not env_path.exists():
        raise RuntimeError(
            f"Missing Box environment config: {env_path}. "
            "Pass --client-id and --client-secret or re-establish ~/.box first."
        )
    data = json.loads(env_path.read_text(encoding="utf-8"))
    default_name = data.get("default")
    environments = data.get("environments") or {}
    selected = environments.get(default_name or "", {})
    client_id = args.client_id or selected.get("clientId")
    client_secret = args.client_secret or selected.get("clientSecret")
    if not client_id or not client_secret:
        raise RuntimeError(
            f"Could not resolve Box client credentials from {env_path}. "
            "Pass --client-id and --client-secret explicitly."
        )
    return client_id, client_secret


def build_box_client(args: argparse.Namespace) -> tuple[Any, Any, JsonTokenStorage]:
    imports = box_imports()
    BoxOAuth = imports["BoxOAuth"]
    OAuthConfig = imports["OAuthConfig"]
    BoxClient = imports["BoxClient"]
    client_id, client_secret = resolve_box_client_credentials(args)
    storage = JsonTokenStorage(Path(args.auth_cache_path).expanduser())
    if not storage.path.exists():
        raise RuntimeError(
            f"Missing Box OAuth cache: {storage.path}. Re-authenticate Box on this machine first."
        )
    auth = BoxOAuth(
        OAuthConfig(client_id=client_id, client_secret=client_secret, token_storage=storage)
    )
    client = BoxClient(auth)
    return client, auth, storage


def maybe_refresh_auth(auth: Any, storage: JsonTokenStorage, *, execute: bool) -> None:
    seconds_left = storage.seconds_remaining()
    if seconds_left is None:
        log("[box-auth] token expiry unknown; trying cached token as-is")
        return
    if seconds_left > AUTH_REFRESH_SKEW_SECONDS:
        log(f"[box-auth] cached access token still valid for about {seconds_left}s")
        return
    log(f"[box-auth] cached access token expires in {seconds_left}s; attempting refresh")
    try:
        auth.refresh_token()
    except Exception as exc:
        raise RuntimeError(
            "Box OAuth refresh failed. Re-authenticate Box on this machine before "
            f"running {'--execute' if execute else 'dry-run with remote probe'}."
        ) from exc


def should_skip_dir_name(name: str, *, include_hidden: bool, excluded_dirs: set[str]) -> bool:
    if name in excluded_dirs:
        return True
    if not include_hidden and name.startswith("."):
        return True
    return False


def should_skip_file(
    path: Path,
    rel: Path,
    *,
    include_hidden: bool,
    follow_symlinks: bool,
    excluded_names: set[str],
) -> tuple[bool, str | None]:
    if path.name in excluded_names:
        return True, None
    if not include_hidden and any(part.startswith(".") for part in rel.parts):
        return True, None
    if path.is_symlink() and not follow_symlinks:
        return True, "symlink"
    return False, None


def iter_local_files(
    root: Path,
    *,
    include_hidden: bool,
    follow_symlinks: bool,
    excluded_dirs: set[str],
    excluded_names: set[str],
    max_files: int | None,
    stats: UploadStats,
) -> list[Path]:
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=follow_symlinks):
        current = Path(dirpath)
        dirnames[:] = sorted(
            name
            for name in dirnames
            if not should_skip_dir_name(
                name, include_hidden=include_hidden, excluded_dirs=excluded_dirs
            )
        )
        for filename in sorted(filenames):
            path = current / filename
            rel = path.relative_to(root)
            skip, reason = should_skip_file(
                path,
                rel,
                include_hidden=include_hidden,
                follow_symlinks=follow_symlinks,
                excluded_names=excluded_names,
            )
            if skip:
                if reason == "symlink":
                    stats.skipped_symlink += 1
                continue
            files.append(path)
            if max_files is not None and len(files) >= max_files:
                return files
    return files


def summarize_local_tree(root: Path, files: list[Path]) -> dict[str, dict[str, int]]:
    summary: dict[str, dict[str, int]] = {}
    for path in files:
        rel = path.relative_to(root)
        top = rel.parts[0] if rel.parts else "."
        entry = summary.setdefault(top, {"files": 0, "bytes": 0})
        entry["files"] += 1
        entry["bytes"] += path.stat().st_size
    return dict(sorted(summary.items()))


def list_folder_items(client: Any, folder_id: str) -> dict[str, RemoteItem]:
    items: dict[str, RemoteItem] = {}
    marker: str | None = None
    while True:
        page = client.folders.get_folder_items(
            folder_id,
            fields=["id", "type", "name", "size", "etag"],
            usemarker=True,
            marker=marker,
            limit=1000,
        )
        for entry in page.entries or []:
            entry_type = getattr(entry.type, "value", entry.type)
            items[str(entry.name)] = RemoteItem(
                item_id=str(entry.id),
                item_type=str(entry_type),
                name=str(entry.name),
                size=getattr(entry, "size", None),
                etag=getattr(entry, "etag", None),
            )
        marker = page.next_marker
        if not marker:
            break
    return items


def ensure_remote_folder(
    client: Any,
    parent_id: str,
    name: str,
    *,
    dry_run: bool,
    folder_cache: dict[str, dict[str, RemoteItem]],
    dry_run_folder_counter: list[int],
    stats: UploadStats,
) -> str:
    if parent_id not in folder_cache:
        folder_cache[parent_id] = list_folder_items(client, parent_id)
    items = folder_cache[parent_id]
    existing = items.get(name)
    if existing is not None:
        if existing.item_type != "folder":
            raise RuntimeError(
                f"Remote name conflict under folder {parent_id}: {name!r} exists as {existing.item_type}"
            )
        return existing.item_id
    if dry_run:
        dry_run_folder_counter[0] += 1
        synthetic_id = f"dryrun-folder-{dry_run_folder_counter[0]}"
        items[name] = RemoteItem(item_id=synthetic_id, item_type="folder", name=name)
        folder_cache[synthetic_id] = {}
        stats.folders_created += 1
        log(f"[dry-run] would create remote folder {name!r} under parent {parent_id}")
        return synthetic_id
    imports = box_imports()
    CreateFolderParent = imports["CreateFolderParent"]
    created = client.folders.create_folder(name, CreateFolderParent(parent_id))
    remote = RemoteItem(item_id=str(created.id), item_type="folder", name=str(created.name))
    items[name] = remote
    folder_cache[remote.item_id] = {}
    stats.folders_created += 1
    log(f"[upload] created remote folder {name!r} under parent {parent_id}")
    return remote.item_id


def ensure_remote_path(
    client: Any,
    root_folder_id: str,
    rel_parent: Path,
    *,
    dry_run: bool,
    folder_cache: dict[str, dict[str, RemoteItem]],
    dry_run_folder_counter: list[int],
    stats: UploadStats,
) -> str:
    current_id = root_folder_id
    if rel_parent == Path("."):
        return current_id
    for part in rel_parent.parts:
        current_id = ensure_remote_folder(
            client,
            current_id,
            part,
            dry_run=dry_run,
            folder_cache=folder_cache,
            dry_run_folder_counter=dry_run_folder_counter,
            stats=stats,
        )
    return current_id


def sha1_digest_base64(chunk: bytes) -> str:
    return base64.b64encode(hashlib.sha1(chunk).digest()).decode("ascii")


def upload_big_file_version(client: Any, file_id: str, path: Path, file_size: int) -> Any:
    upload_session = client.chunked_uploads.create_file_upload_session_for_existing_file(
        file_id, file_size, file_name=path.name
    )
    upload_part_url = upload_session.session_endpoints.upload_part
    commit_url = upload_session.session_endpoints.commit
    list_parts_url = upload_session.session_endpoints.list_parts
    part_size = int(upload_session.part_size)
    overall_hash = hashlib.sha1()
    offset = 0
    parts: list[Any] = []
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(part_size)
            if not chunk:
                break
            chunk_digest = f"sha={sha1_digest_base64(chunk)}"
            end_offset = offset + len(chunk) - 1
            content_range = f"bytes {offset}-{end_offset}/{file_size}"
            uploaded_part = client.chunked_uploads.upload_file_part_by_url(
                upload_part_url,
                chunk,
                chunk_digest,
                content_range,
            )
            parts.append(uploaded_part.part)
            overall_hash.update(chunk)
            offset += len(chunk)
    client.chunked_uploads.get_file_upload_session_parts_by_url(list_parts_url)
    commit_digest = f"sha={base64.b64encode(overall_hash.digest()).decode('ascii')}"
    committed = client.chunked_uploads.create_file_upload_session_commit_by_url(
        commit_url, parts, commit_digest
    )
    if committed is None or not committed.entries:
        raise RuntimeError(f"Chunked commit for existing file {file_id} returned no file entry")
    return committed.entries[0]


def upload_new_file(client: Any, path: Path, parent_id: str, small_upload_max_bytes: int) -> Any:
    imports = box_imports()
    UploadFileAttributes = imports["UploadFileAttributes"]
    UploadFileAttributesParentField = imports["UploadFileAttributesParentField"]
    file_size = path.stat().st_size
    if file_size > small_upload_max_bytes:
        with path.open("rb") as handle:
            return client.chunked_uploads.upload_big_file(handle, path.name, file_size, parent_id)
    with path.open("rb") as handle:
        uploaded = client.uploads.upload_file(
            UploadFileAttributes(path.name, UploadFileAttributesParentField(parent_id)),
            handle,
            file_file_name=path.name,
        )
    return uploaded.entries[0]


def upload_existing_file_version(
    client: Any, path: Path, file_id: str, small_upload_max_bytes: int
) -> Any:
    imports = box_imports()
    UploadFileVersionAttributes = imports["UploadFileVersionAttributes"]
    file_size = path.stat().st_size
    if file_size > small_upload_max_bytes:
        return upload_big_file_version(client, file_id, path, file_size)
    with path.open("rb") as handle:
        uploaded = client.uploads.upload_file_version(
            file_id,
            UploadFileVersionAttributes(path.name),
            handle,
            file_file_name=path.name,
        )
    return uploaded.entries[0]


def build_manifest(
    args: argparse.Namespace,
    source_root: Path,
    files: list[Path],
    stats: UploadStats,
    top_level_summary: dict[str, dict[str, int]],
) -> dict[str, Any]:
    return {
        "timestamp_epoch_s": int(time.time()),
        "mode": (
            "inventory-only"
            if args.inventory_only
            else ("execute" if args.execute else "dry-run")
        ),
        "source_root": str(source_root),
        "destination_box_folder_id": args.box_folder_id,
        "destination_box_folder_path": DEFAULT_BOX_FOLDER_PATH,
        "remote_subfolder": args.remote_subfolder,
        "excluded_dirs": sorted(set(DEFAULT_EXCLUDE_DIRS).union(args.exclude_dir)),
        "excluded_names": sorted(set(DEFAULT_EXCLUDE_NAMES).union(args.exclude_name)),
        "include_hidden": args.include_hidden,
        "follow_symlinks": args.follow_symlinks,
        "max_files": args.max_files,
        "stats": asdict(stats),
        "top_level_summary": top_level_summary,
        "sample_paths": [str(path.relative_to(source_root)) for path in files[:20]],
    }


def write_manifest(manifest_path: str | None, payload: dict[str, Any]) -> None:
    if not manifest_path:
        return
    path = Path(manifest_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    log(f"[manifest] wrote {path}")


def main() -> int:
    args = parse_args()
    if args.execute and args.dry_run:
        print("Use either --execute or --dry-run, not both.", file=sys.stderr)
        return 2
    if args.box_folder_id == RAW_DATA_BOX_FOLDER_ID:
        print(
            f"Refusing to upload to raw-data Box folder {RAW_DATA_BOX_FOLDER_ID}.",
            file=sys.stderr,
        )
        return 2

    source_root = Path(args.source_root).expanduser().resolve()
    if not source_root.exists() or not source_root.is_dir():
        print(f"Missing source root directory: {source_root}", file=sys.stderr)
        return 2

    excluded_dirs = set(DEFAULT_EXCLUDE_DIRS).union(args.exclude_dir)
    excluded_names = set(DEFAULT_EXCLUDE_NAMES).union(args.exclude_name)

    stats = UploadStats()
    local_files = iter_local_files(
        source_root,
        include_hidden=args.include_hidden,
        follow_symlinks=args.follow_symlinks,
        excluded_dirs=excluded_dirs,
        excluded_names=excluded_names,
        max_files=args.max_files,
        stats=stats,
    )
    for path in local_files:
        stats.files_considered += 1
        stats.bytes_considered += path.stat().st_size
    top_level_summary = summarize_local_tree(source_root, local_files)

    log(f"[local] source root: {source_root}")
    log(f"[local] eligible files: {stats.files_considered}")
    log(f"[local] eligible bytes: {format_bytes(stats.bytes_considered)}")
    for top_level, summary in top_level_summary.items():
        log(
            f"[local]   {top_level}: {summary['files']} files, {format_bytes(summary['bytes'])}"
        )

    if args.inventory_only:
        manifest = build_manifest(args, source_root, local_files, stats, top_level_summary)
        write_manifest(args.manifest_path, manifest)
        return 0

    client, auth, storage = build_box_client(args)
    maybe_refresh_auth(auth, storage, execute=args.execute)

    folder_cache: dict[str, dict[str, RemoteItem]] = {}
    dry_run_folder_counter = [0]
    dry_run = not args.execute

    remote_root_id = ensure_remote_folder(
        client,
        args.box_folder_id,
        args.remote_subfolder,
        dry_run=dry_run,
        folder_cache=folder_cache,
        dry_run_folder_counter=dry_run_folder_counter,
        stats=stats,
    )

    for index, path in enumerate(local_files, start=1):
        rel = path.relative_to(source_root)
        parent_id = ensure_remote_path(
            client,
            remote_root_id,
            rel.parent,
            dry_run=dry_run,
            folder_cache=folder_cache,
            dry_run_folder_counter=dry_run_folder_counter,
            stats=stats,
        )
        if parent_id not in folder_cache:
            folder_cache[parent_id] = list_folder_items(client, parent_id)
        items = folder_cache[parent_id]
        existing = items.get(path.name)
        size = path.stat().st_size
        if existing is None:
            if dry_run:
                stats.uploaded_new += 1
                log(f"[dry-run] would upload new file {rel} -> parent {parent_id}")
            else:
                uploaded = upload_new_file(
                    client, path, parent_id, args.small_upload_max_bytes
                )
                items[path.name] = RemoteItem(
                    item_id=str(uploaded.id),
                    item_type="file",
                    name=str(uploaded.name),
                    size=size,
                )
                stats.uploaded_new += 1
                log(f"[upload] uploaded new file {rel}")
        else:
            if existing.item_type != "file":
                raise RuntimeError(
                    f"Remote name conflict for {rel}: existing Box item is a {existing.item_type}"
                )
            if existing.size == size:
                stats.skipped_same += 1
            elif not args.overwrite_changed:
                stats.skipped_changed += 1
                log(
                    f"[skip] remote file differs by size and --overwrite-changed is off: {rel}"
                )
            else:
                if dry_run:
                    stats.uploaded_overwrite += 1
                    log(f"[dry-run] would upload new Box version for {rel}")
                else:
                    uploaded = upload_existing_file_version(
                        client, path, existing.item_id, args.small_upload_max_bytes
                    )
                    items[path.name] = RemoteItem(
                        item_id=str(uploaded.id),
                        item_type="file",
                        name=str(uploaded.name),
                        size=size,
                        etag=getattr(uploaded, "etag", None),
                    )
                    stats.uploaded_overwrite += 1
                    log(f"[upload] uploaded new Box version for {rel}")
        if index % 250 == 0 or index == stats.files_considered:
            log(
                f"[progress] {index}/{stats.files_considered} files scanned; "
                f"new={stats.uploaded_new} overwrite={stats.uploaded_overwrite} "
                f"same={stats.skipped_same} changed-skip={stats.skipped_changed}"
            )

    manifest = build_manifest(args, source_root, local_files, stats, top_level_summary)
    write_manifest(args.manifest_path, manifest)
    log(
        "[done] "
        f"mode={'execute' if args.execute else 'dry-run'} "
        f"folders_created={stats.folders_created} "
        f"uploaded_new={stats.uploaded_new} "
        f"uploaded_overwrite={stats.uploaded_overwrite} "
        f"skipped_same={stats.skipped_same} "
        f"skipped_changed={stats.skipped_changed}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
