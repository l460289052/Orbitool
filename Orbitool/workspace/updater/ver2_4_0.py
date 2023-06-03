import h5py
from .utils import move_to, create_group, delete


def update(path: str):
    """
    update to 2.4.0
    """
    parts = [
        "calibration tab", "file tab", "formula docker", "mass detect tab", "masslist docker", "noise tab",
        "peak fit tab", "peaklist docker", "peak shape tab", "spectra list", "spectrum docker", "time series tab"]

    lists = {
        "noise tab/raw_spectra": "data/raw_spectra",
        "calibration tab/calibrated_spectra": "data/calibrated_spectra",
    }

    with h5py.File(path, 'r+') as f:
        for part in parts:
            source = f"{part}/info"
            target = f"info/{part.replace(' ', '_')}"
            move_to(f, source, target)
            create_group(f, target, 'a')

            source = f"{part}/ui_state"
            target = f"info/{part.replace(' ', '_')}/ui_state"
            move_to(f, source, target)
            create_group(f, target, 'a')

        for source, target in lists.items():
            move_to(f, source, target)
            group = create_group(f, target, 'a')
            group.attrs["keys"] = sorted(list(map(int, group.keys())))

        for part in parts:
            delete(f, part)
