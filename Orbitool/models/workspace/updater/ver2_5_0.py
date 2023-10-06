from datetime import datetime
from sys import hash_info
from h5py import File, Group
import numpy as np


def update(f: File):
    """
    to 2.5.0
    """

    f_data = f["data"]

    DT_KWDS = {"compression": "gzip", "compression_opts": 1}

    def assure_bytes(array: np.ndarray):
        if array.dtype.char == "S":
            return array
        if len(array):
            return np.char.encode(array.astype(str), "utf-8")
        return np.empty_like(array, "S")

    def move_dict_index(group: Group):
        group.create_dataset(
            "_index",
            data=assure_bytes(group.attrs["indexes"]),
            **DT_KWDS
        )

    def move_group_2_dataset(group: Group, key: str, dtype):
        g = group[key]
        values = [g[k][()] for k, _ in dtype]
        attrs = dict(g.attrs.items())
        del group[key]
        ds = group.create_dataset(
            key,
            len(values[0]), dtype, **DT_KWDS)
        for (k, _), v in zip(dtype, values):
            ds[k] = v
        for key, attr in attrs.items():
            ds.attrs[key] = attr
        return ds

    def move_fitted_peak(group: Group, key: str):
        peaks = group[key][()]
        del group[key]

        ind = 0
        mz = []
        intensity = []
        start_index = []
        stop_index = []
        fitted_params = []
        peak_position = []
        peak_intensity = []
        area = []
        tags = []
        formulas = []
        for peak in peaks:
            mz.append(peak["mz"])
            intensity.append(peak["intensity"])
            length = len(peak["mz"])
            start_index.append(ind)
            stop_index.append(ind + length)
            fitted_params.append(peak["fitted_param"].tobytes())
            peak_position.append(peak["peak_position"])
            peak_intensity.append(peak["peak_intensity"])
            area.append(peak["area"])
            tags.append(peak["tags"])
            formulas.append(peak["formulas"])
            ind += length
        g = group.create_group(key)

        mz = np.concatenate(mz)
        intensity = np.concatenate(intensity)
        ds = g.create_dataset(
            "spectrum", len(mz), [("mz", float), ("intensity", float)], **DT_KWDS)
        ds["mz"] = mz
        ds["intensity"] = intensity

        fitted_params = np.array(fitted_params)
        tags = np.array(tags)
        formulas = np.array(formulas)

        ds = g.create_dataset(
            "peaks", len(start_index), dtype=
            [("start_index", np.int64), ("stop_index", np.int64),
                        ("fitted_param", fitted_params.dtype), ( "peak_position", float),
                        ("peak_intensity", float), ("area", float),
                        ("tags", tags.dtype), ("formulas", formulas.dtype)], **DT_KWDS)
        ds["start_index"] = start_index
        ds["stop_index"] = stop_index
        ds["fitted_param"] = fitted_params
        ds["peak_position"] = peak_position
        ds["peak_intensity"] = peak_intensity
        ds["tags"] = tags
        ds["formulas"] = formulas



    def move_peak(group: Group, key: str):
        peaks=group[key][()]
        del group[key]

        ind=0
        mz=[]
        intensity=[]
        new_peaks=[]
        for peak in peaks:
            mz.append(peak["mz"])
            intensity.append(peak["intensity"])
            length=len(peak["mz"])
            new_peaks.append((ind, ind + length))
            ind += length
        g=group.create_group(key)

        mz=np.concatenate(mz)
        intensity=np.concatenate(intensity)
        ds=g.create_dataset(
            "spectrum", len(mz), [("mz", float), ("intensity", float)], **DT_KWDS)
        ds["mz"]=mz
        ds["intensity"]=intensity

        new_peaks=np.array(
            new_peaks, [("start_index", np.int64), ("stop_index", np.int64)])

        g.create_dataset("peaks", data = new_peaks, **DT_KWDS)

    def move_ui_state(parent_group: Group):
        ui_states=parent_group["ui_state"].attrs
        keys=assure_bytes(np.array(list(ui_states.keys())))
        values=assure_bytes(np.array(list(ui_states.values())))

        del parent_group["ui_state"]
        if len(ui_states):
            ds=parent_group.create_dataset(
                "ui_state", shape = len(keys),
                dtype = [("key", keys.dtype), ("value", values.dtype)], **DT_KWDS)
            ds["key"]=keys
            ds["value"]=values

    def move_disklist(group: Group, dtype):
        keys=list(map(str, group.attrs["keys"]))
        group.attrs["keys"]=keys
        for key in keys:
            move_group_2_dataset(
                group, key, dtype)

    move_disklist(f_data["calibrated_spectra"], [
                  ("mz", float), ("intensity", float)])
    move_disklist(f_data["raw_spectra"], [("mz", float), ("intensity", float)])
    move_disklist(f_data["time_series"], [("times", np.int64),
                  ("positions", float), ("intensity", float)])
    for key in f_data["time_series"].attrs["keys"]:
        f_data["time_series"][key]["times"] *= 1000000

    f_info=f["info"]

    def move_calibration(group: Group):
        def mv_info(name):
            info=group[name]
            rows=[]
            for i in range(len(info)):
                seg=info[str(i)].attrs
                rows.append((
                    seg["end_point"], seg["intensity_filter"], seg["degree"], seg["n_ions"], seg["rtol"]
                ))
            del group[name]
            group.create_dataset(
                name,
                dtype = [("end_point", float), ("intensity_filter", int),
                       ("degree", int), ("n_ions", int), ("rtol", float)],
                data = rows)
        mv_info("calibrate_info_segments")
        mv_info("last_calibrate_info_segments")

        # convert time[s] to time[us]
        group["calibrated_spectrum_infos"]["start_time"] *= 1000000
        group["calibrated_spectrum_infos"]["end_time"] *= 1000000

        move_dict_index(group["calibrator_segments"])

        path_infos_group=group["path_ion_infos"]
        move_dict_index(path_infos_group)

        for i in map(str, range(len(path_infos_group["_index"]))):
            g=path_infos_group[i]
            move_dict_index(g)
            for j in map(str, range(len(g["_index"]))):
                move_group_2_dataset(
                    g, j, [("raw_position", float), ("raw_intensity", float)])

        g=group["path_times"]
        attrs=g.attrs
        index=assure_bytes(attrs["indexes"])
        dts=[datetime.fromisoformat(attrs[str(i)])
               for i in range(len(index))]
        dts = np.array(dts, "M8[us]").astype("int64")
        del group["path_times"]
        ds = group.create_dataset(
            "path_times",
            len(index),
            [("key", index.dtype), ("value", np.int64)], **DT_KWDS)
        ds["key"] = index
        ds["value"] = dts

        move_ui_state(group)

    move_calibration(f_info["calibration_tab"])

    def move_file_tab(group: Group):
        group.move("pathlist", "tmp")
        group.move("tmp/paths", "pathlist")
        pathlist = group["pathlist"]
        pathlist["createDatetime"] *= 1000000
        pathlist["startDatetime"] *= 1000000
        pathlist["endDatetime"] *= 1000000

        periods = group["periods"]
        periods["start_time"] *= 1000000
        periods["end_time"] *= 1000000

        spectrum_infos = group["spectrum_infos"]
        spectrum_infos["start_time"] *= 1000000
        spectrum_infos["end_time"] *= 1000000

        move_ui_state(group)

    move_file_tab(f_info["file_tab"])

    def move_formula(group: Group):
        def move_dict_2_row(group: Group, key: str, dtype):
            g = group[key]
            index = assure_bytes(g.attrs["indexes"])
            data = g[()]
            del group[key]
            ds = group.create_dataset(
                key, len(index),
                [("_key_index", index.dtype), *dtype],
                **DT_KWDS)
            ds["_key_index"] = index
            for key, _ in dtype:
                ds[key] = data[key]
        move_dict_2_row(
            group["calc_gen"], "element_states",
            [("DBE2", float), ("HMin", float), ("HMax", float), ("OMin", float), ("OMax", float)])

        move_dict_2_row(
            group["calc_gen"], "isotope_usable",
            [("e_num", np.int64), ("i_num", np.int64), ("min", np.int64), ("max", np.int64), ("global_limit", bool)])

        move_ui_state(group)
    move_formula(f_info["formula_docker"])

    def move_massdefect(group: Group):
        clr_x = group["clr_x"][()]
        clr_y = group["clr_y"][()]
        clr_size = group["clr_size"][()]
        clr_color = group["clr_color"][()]
        # omit label

        ds = group.create_dataset(
            "clr",
            len(clr_x),
            dtype=[("x", float), ("y", float), ("size", float), ("color", float)])
        ds["x"] = clr_x
        ds["y"] = clr_y
        ds["size"] = clr_size
        ds["color"] = clr_color

        gry_x = group["gry_x"][()]
        gry_y = group["gry_y"][()]
        gry_size = group["gry_size"][()]

        ds = group.create_dataset(
            "gry",
            len(gry_x),
            dtype=[("x", float), ("y", float), ("size", float)])
        ds["x"] = gry_x
        ds["y"] = gry_y
        ds["size"] = gry_size

        move_ui_state(group)

    move_massdefect(f_info["mass_defect_tab"])
    move_ui_state(f_info["masslist_docker"])

    def move_noise_tab(group: Group):
        move_group_2_dataset(
            group, "current_spectrum", [("mz", float), ("intensity", float)])

        denoised_info = group["denoised_spectrum_infos"]
        denoised_info["start_time"] *= 1000000
        denoised_info["end_time"] *= 1000000

        result = group["general_result"]

        noise = result["noise"][()]
        lod = result["LOD"][()]
        del result["noise"]
        ds = result.create_dataset(
            "noise", len(noise),
            [("noise", float), ("LOD", float)]
        )
        ds["noise"] = noise
        ds["LOD"] = lod

        mz = result["spectrum_mz"][()]
        intensity = result["spectrum_intensity"][()]
        ds = result.create_dataset(
            "spectrum_split", len(mz), [("mz", float), ("intensity", float)])
        ds["mz"] = mz
        ds["intensity"] = intensity

        mz = result["noise_mz"][()]
        intensity = result["noise_intensity"][()]
        ds = result.create_dataset(
            "noise_split", len(mz), [("mz", float), ("intensity", float)])
        ds["mz"] = mz
        ds["intensity"] = intensity

        move_ui_state(group)

    move_noise_tab(f_info["noise_tab"])

    def move_peakfit_tab(group: Group):
        move_fitted_peak(group, "peaks")
        move_peak(group, "raw_peaks")
        move_group_2_dataset(group, "spectrum", [
                             ("mz", float), ("intensity", float)])
        move_ui_state(group)

    move_peakfit_tab(f_info["peak_fit_tab"])

    def move_peakshape_tab(group: Group):
        move_fitted_peak(group["peaks_manager"], "peaks")
        move_group_2_dataset(group, "spectrum", [
                             ("mz", float), ("intensity", float)])
        move_ui_state(group)

    move_peakshape_tab(f_info["peak_shape_tab"])

    move_ui_state(f_info["spectra_list"])

    move_group_2_dataset(f_info["spectrum_docker"], "spectrum", [
                         ("mz", float), ("intensity", float)])
    move_ui_state(f_info["spectrum_docker"])

    def move_timeseries_tab(group: Group):
        infos = group["timeseries_infos"]
        infos["time_min"]*=1000000
        infos["time_max"]*=1000000
        move_ui_state(group)
    move_timeseries_tab(f_info["time_series_tab"])