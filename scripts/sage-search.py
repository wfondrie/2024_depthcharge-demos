#!/usr/bin/env python3
"""Assign PSMs with Sage"""

import json
import logging
import subprocess
import time

from pathlib import Path

import click
import ppx
import polars as pl

ROOT = Path(__file__).parent.parent
LOGGER = logging.getLogger(__name__)


def select_files(n_train, n_valid, n_test, seed):
    """Select files at random for the data splits from MassIVE-KB.

    Parameters
    ----------
    n_train : int
        The number of files in the training set.
    n_valid : int
        The number of files in the validation set.
    n_test : int
        The number of files in the test set.
    seed : int
        The random seed.

    Returns
    -------
    dict[str, tuple[str,str]]
        The split, MassIVE identifier, and file name for selected each file.
    """
    mskb_files = (
        pl.read_csv(
            ROOT / "data/manual/massivekb_v2.0.15-hcd-files.tsv",
            separator="\t",
        )
        .select(
            pl.col("spectrum_filename")
            .str.splitn("/", 2)
            .struct.rename_fields(["acc", "file"])
        )
        .unnest("spectrum_filename")
        .sample(fraction=1, seed=seed)
        .group_by("acc", maintain_order=True)
        .head(1)
        .sample(fraction=1, seed=seed)
        .rows()
    )

    splits = [
        mskb_files[:n_train],  # Train
        mskb_files[n_train : (n_train + n_valid)],  # Valid
        mskb_files[(n_train + n_valid) : (n_train + n_valid + n_test)],  # Test
    ]

    mzml_files = {}
    for label, split in zip(["train", "valid", "test"], splits):
        mzml_files[label] = []
        for acc, fname in split:
            mzml_files[label].append(download(acc, fname))

    return mzml_files


def download(massive_id, fname):
    """Download a file from MassIVE, if they don't already exist.

    Parameters
    ----------
    massive_id : str
        The MassIVE identifier.
    fname : str
        The file to download.

    Returns
    -------
    str
        The local path to the file.
    """
    proj = ppx.MassiveProject(massive_id)
    loc = proj.local_files(fname)
    if not loc:
        loc = proj.download(fname)

    return str(loc[0])


def search_files(mzml_files):
    """Search the mzML files for each split, if necessary.

    Parameters
    ----------
    mzml_files : dict[str, list[tuple[str, str]]]
        The mzML files for each split.
    """
    search_results = {}
    for split, split_files in mzml_files.items():
        search_results[split] = (
            ROOT / f"data/spectrum-quality/{split}/results.sage.parquet"
        )
        if not search_results[split].exists():
            # This is just a safety check to prevent someone from injecting malicious code.
            if split not in ["train", "valid", "test"]:
                raise ValueError("Unrecognized split.")

            LOGGER.info(
                "Searching %s split (see logs/sage-%s.log for progress)...",
                split,
                split,
            )
            split_files = [f"'{f}'" for f in split_files]
            cmd = [
                "bin/sage",
                "--parquet",
                "--output_directory",
                str(search_results[split].parent),
                "--fasta",
                str(ROOT / "data/fasta/human.fasta"),
                str(ROOT / "data/manual/sage.json"),
                *split_files,
                "2>",
                f"logs/sage-{split}.log",
                "1>",
                "/dev/null",
            ]
            subprocess.run(cmd, shell=True, check=True)
        else:
            LOGGER.info("Using previous search results for %s split.", split)

    return search_results


@click.command()
@click.option("-s", "--seed", help="The random seed.", default=42, type=int)
@click.argument("n_train", type=int)
@click.argument("n_valid", type=int)
@click.argument("n_test", type=int)
def main(n_train, n_valid, n_test, seed):
    """Create data splits from MassIVE-KB and search them with Sage."""
    start = time.time()
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    (ROOT / "data/mzml").mkdir(exist_ok=True, parents=True)
    (ROOT / "data/spectrum-quality").mkdir(exist_ok=True)
    ppx.set_data_dir(ROOT / "data/mzml")

    LOGGER.info("Downloading selected files...")
    mzml_files = select_files(n_train, n_valid, n_test, seed)

    LOGGER.info("Performing OMS searches with Sage...")
    search_files(mzml_files)

    with (ROOT / "data/spectrum-quality/splits.json").open("w+") as out:
        json.dump(mzml_files, out)

    LOGGER.info("Elapesed time: %f", (time.time() - start) / 60)
    LOGGER.info("DONE!")


if __name__ == "__main__":
    main()
