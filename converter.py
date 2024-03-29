import os
import logging
import coloredlogs

from pathlib import Path
from shutil import copytree, ignore_patterns, copy2
from PIL import Image, UnidentifiedImageError

# logger setup
log = logging.getLogger(__name__)
coloredlogs.install(level="DEBUG", logger=log)


class AppLogic:
    def create_folder_tree(self, src_path, dst_path):
        """Create a folder tree in the destination path that mirrors the source path."""
        def ignore_files(folder, files):
            return [file for file in files if not os.path.isdir(os.path.join(folder, file))]

        try:
            copytree(
                src_path,
                os.path.join(dst_path, os.path.basename(os.path.normpath(src_path))),
                symlinks=False,
                ignore=ignore_files,
            )
        except FileExistsError:
            return False

    def convert(self, gui, selected_format):
        """Convert images in the source path to the selected format and save them in the destination path."""
        src_path = gui.fields[0].get().strip()
        dst_path = gui.fields[1].get().strip()
        quality = gui.quality_dropdown.get()
        if gui.check_params(src_path, dst_path):
            self.create_folder_tree(src_path, dst_path)

            file_list = list(Path(src_path).rglob("*.*"))
            file_list_length = len(file_list)
            last_iter_length = 0
            num_of_image_files = 0
            num_of_non_image_files = 0
            num_of_skipped_files = 0
            non_image_files = []
            are_you_sure = False

            for file in file_list:
                image = None
                new_dst_path = os.path.join(dst_path, os.path.basename(src_path), os.path.relpath(file, src_path))  # destination to original tree path

                print(
                    f"Converting {os.path.basename(new_dst_path)}...",
                    end=" " * (last_iter_length - len(os.path.basename(new_dst_path)))
                    + "\r",
                )
                last_iter_length = len(os.path.basename(new_dst_path))

                try:
                    image = Image.open(file)
                    num_of_image_files += 1
                except UnidentifiedImageError:
                    num_of_non_image_files += 1
                    non_image_files.append(file)

                if image:
                    if not gui.show_overwrite_dialogues(new_dst_path, are_you_sure, selected_format):
                        num_of_skipped_files += 1
                        image.close()
                        gui.update_progressbar(
                            num_of_image_files,
                            num_of_non_image_files,
                            num_of_skipped_files,
                            file_list_length,
                        )
                        continue  # continue if user chooses to skip overwriting this file.

                    if quality == "Lossless":
                        image.save(
                            new_dst_path[: new_dst_path.rfind(".")] + "." + selected_format,
                            format=selected_format,
                            lossless=True,
                            subsampling=0,
                        )
                    else:
                        image.save(
                            new_dst_path[: new_dst_path.rfind(".")] + "." + selected_format,
                            format=selected_format,
                            quality=int(quality),
                            subsampling=0,
                        )
                    image.close()
                    image = None

                gui.update_progressbar(
                    num_of_image_files,
                    num_of_non_image_files,
                    num_of_skipped_files,
                    file_list_length,
                )

            if gui.post_conversion_dialogue(
                num_of_image_files, num_of_non_image_files
            ):
                for file in non_image_files:
                    copy2(
                        file,
                        os.path.join(
                            dst_path,
                            os.path.basename(src_path),
                            os.path.relpath(file, src_path),
                        ),
                    )
            # Reset progress bar
            gui.progress.set("0%")
            gui.progressbar_percentage.set("0")

            gui.overwrite_all = False  # reset overwrite all flag

        else:
            log.warn("Invalid parameters. No changes have been made.")
        
        gui.start_button.configure(state="normal")
