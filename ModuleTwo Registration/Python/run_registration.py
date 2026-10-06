"""Command line entry point of the registration

Example:
    python run_registration.py --scan ../AsBuilt/scan.ply --bim ../AsPlanned/bim.ply --out ../outputs/d19
"""

import argparse
from pathlib import Path

from registration import RegistrationConfig, register
from registration.io import load_point_cloud, save_results
from registration.visualization import show_before_after

MODULE_DIR = Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    defaults = RegistrationConfig()
    parser = argparse.ArgumentParser(
        description="OBBP-ICP registration of an as-built scan onto the as-planned cloud"
    )
    parser.add_argument(
        "--scan", type=Path, required=True, help="as-built point cloud (.ply)"
    )
    parser.add_argument(
        "--bim",
        type=Path,
        required=True,
        help="as-planned synthetic point cloud (.ply)",
    )
    parser.add_argument(
        "--out", type=Path, default=MODULE_DIR / "outputs", help="output folder"
    )
    parser.add_argument(
        "--voxel", type=float, default=defaults.voxel_size, help="voxel size in metres"
    )
    parser.add_argument(
        "--level-z", action="store_true", help="estimate the Z-axis leveling"
    )
    parser.add_argument(
        "--point-to-plane", action="store_true", help="point-to-plane ICP"
    )
    parser.add_argument(
        "--estimate-scale", action="store_true", help="estimate a scale factor"
    )
    parser.add_argument(
        "--viz", action="store_true", help="show the clouds before and after"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = RegistrationConfig(
        voxel_size=args.voxel,
        level_z=args.level_z,
        point_to_plane=args.point_to_plane,
        estimate_scale=args.estimate_scale,
    )

    scan = load_point_cloud(args.scan)
    bim = load_point_cloud(args.bim)

    result = register(scan, bim, config)
    save_results(result, config, args.out)

    if args.viz:
        show_before_after(scan, result.scan_registered, bim)


if __name__ == "__main__":
    main()
