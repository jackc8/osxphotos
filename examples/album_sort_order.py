""" Example function for use with osxphotos export --post-function option showing how to record album sort order """

import os
import pathlib
from typing import Optional

from osxphotos import ExportResults, PhotoInfo
from osxphotos.albuminfo import AlbumInfo
from osxphotos.path_utils import sanitize_dirname
from osxphotos.phototemplate import RenderOptions


def album_sequence(photo: PhotoInfo, options: RenderOptions, **kwargs) -> str:
    """Call this with {function} template to get album sequence (sort order) when exporting with {folder_album} template

    For example, calling this template function like the following prepends sequence#_ to each exported file if the file is in an album:

    osxphotos export /path/to/export -V --directory "{folder_album}" --filename "{album?{function:examples/album_sort_order.py::album_sequence}_,}{original_name}"

    The sequence will start at 0.  To change the sequence to start at a different offset (e.g. 1), set the environment variable OSXPHOTOS_ALBUM_SEQUENCE_START=1 (or whatever offset you want)
    """
    dest_path = options.dest_path
    if not dest_path:
        return ""

    album_info = None
    for album in photo.album_info:
        # following code is how {folder_album} builds the folder path
        folder = "/".join(sanitize_dirname(f) for f in album.folder_names)
        folder += "/" + sanitize_dirname(album.title)
        if dest_path.endswith(folder):
            album_info = album
            break
    else:
        # didn't find the album, so skip this file
        return ""
    start_index = int(os.getenv("OSXPHOTOS_ALBUM_SEQUENCE_START", 0))
    return str(album_info.photo_index(photo) + start_index)


def album_sort_order(
    photo: PhotoInfo, results: ExportResults, verbose: callable, **kwargs
):
    """Call this with osxphotos export /path/to/export --post-function album_sort_order.py::album_sort_order
        This will get called immediately after the photo has been exported

    Args:
        photo: PhotoInfo instance for the photo that's just been exported
        results: ExportResults instance with information about the files associated with the exported photo
        verbose: A function to print verbose output if --verbose is set; if --verbose is not set, acts as a no-op (nothing gets printed)
        **kwargs: reserved for future use; recommend you include **kwargs so your function still works if additional arguments are added in future versions

    Notes:
        Use verbose(str) instead of print if you want your function to conditionally output text depending on --verbose flag
        Any string printed with verbose that contains "warning" or "error" (case-insensitive) will be printed with the appropriate warning or error color
        Will not be called if --dry-run flag is enabled
        Will be called immediately after export and before any --post-command commands are executed
    """

    # ExportResults has the following properties
    # fields with filenames contain the full path to the file
    # exported: list of all files exported
    # new: list of all new files exported (--update)
    # updated: list of all files updated (--update)
    # skipped: list of all files skipped (--update)
    # exif_updated: list of all files that were updated with --exiftool
    # touched: list of all files that had date updated with --touch-file
    # converted_to_jpeg: list of files converted to jpeg with --convert-to-jpeg
    # sidecar_json_written: list of all JSON sidecar files written
    # sidecar_json_skipped: list of all JSON sidecar files skipped (--update)
    # sidecar_exiftool_written: list of all exiftool sidecar files written
    # sidecar_exiftool_skipped: list of all exiftool sidecar files skipped (--update)
    # sidecar_xmp_written: list of all XMP sidecar files written
    # sidecar_xmp_skipped: list of all XMP sidecar files skipped (--update)
    # missing: list of all missing files
    # error: list tuples of (filename, error) for any errors generated during export
    # exiftool_warning: list of tuples of (filename, warning) for any warnings generated by exiftool with --exiftool
    # exiftool_error: list of tuples of (filename, error) for any errors generated by exiftool with --exiftool
    # xattr_written: list of files that had extended attributes written
    # xattr_skipped: list of files that where extended attributes were skipped (--update)
    # deleted_files: list of deleted files
    # deleted_directories: list of deleted directories
    # exported_album: list of tuples of (filename, album_name) for exported files added to album with --add-exported-to-album
    # skipped_album: list of tuples of (filename, album_name) for skipped files added to album with --add-skipped-to-album
    # missing_album: list of tuples of (filename, album_name) for missing files added to album with --add-missing-to-album

    for filepath in results.exported:
        # do your processing here
        filepath = pathlib.Path(filepath)
        album_dir = filepath.parent.name
        if album_dir not in photo.albums:
            return

        # get the first album that matches this name of which the photo is a member
        album_info = None
        for album in photo.album_info:
            if album.title == album_dir:
                album_info = album
                break
        else:
            # didn't find the album, so skip this file
            return

        try:
            sort_order = album_info.photo_index(photo)
        except ValueError:
            # photo not in album, so skip this file
            return

        verbose(f"Sort order for {filepath} in album {album_dir} is {sort_order}")
        with open(str(filepath) + "_sort_order.txt", "w") as f:
            f.write(str(sort_order))
