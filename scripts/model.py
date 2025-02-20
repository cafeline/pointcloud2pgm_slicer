# SPDX-FileCopyrightText: 2025 Ryo Funai
# SPDX-License-Identifier: Apache-2.0

"""
点群データの保持、処理、およびPGM/YAML変換を行う
"""
from abc import ABC, abstractmethod
import os
import numpy as np
import open3d as o3d
import pyvista as pv
from typing import Optional, Tuple
from config import MIN_OCCUPIED_POINTS, VOXEL_SIZE

class IPointCloudModel(ABC):
    @abstractmethod
    def set_point_cloud_data(self, pcd: o3d.geometry.PointCloud) -> None:
        """点群データの読み込み後の初期化"""
        pass

    @abstractmethod
    def get_polydata(self, min_z: float, max_z: float) -> Optional[pv.PolyData]:
        """指定Z範囲におけるフィルタ済みの描画用PolyDataを返す"""
        pass

    @abstractmethod
    def convert_to_pgm(
        self,
        min_z: float,
        max_z: float,
        resolution: float,
        output_dir: str,
        output_filename: str,
        occupied_thresh: float,
        free_thresh: float,
        negate: int,
    ) -> Tuple[str, str]:
        """PGM/YAML変換を行い、生成ファイルのパスを返す"""
        pass

class PointCloudModel(IPointCloudModel):
    def __init__(self) -> None:
        # 生データ（PGM変換用）
        self.raw_points: Optional[np.ndarray] = None
        self.raw_z: Optional[np.ndarray] = None
        # 描画用（ダウンサンプリング済み）
        self.display_cloud: Optional[pv.PolyData] = None

        self.overall_z_min: Optional[float] = None
        self.overall_z_max: Optional[float] = None
        self.current_min_z: Optional[float] = None
        self.current_max_z: Optional[float] = None

    def set_point_cloud_data(self, pcd: o3d.geometry.PointCloud) -> None:
        self.raw_points = np.asarray(pcd.points)
        if self.raw_points.size == 0:
            raise ValueError("生の点群が存在しません。")
        self.raw_z = self.raw_points[:, 2]
        self.overall_z_min = float(np.min(self.raw_z))
        self.overall_z_max = float(np.max(self.raw_z))
        self.current_min_z = self.overall_z_min
        self.current_max_z = self.overall_z_max

        # ダウンサンプリング
        pcd_down = pcd.voxel_down_sample(VOXEL_SIZE)
        down_points = np.asarray(pcd_down.points)
        if down_points.size == 0:
            self.display_cloud = None
        else:
            down_z = down_points[:, 2]
            self.display_cloud = pv.PolyData(down_points)
            self.display_cloud["z"] = down_z

    def get_polydata(self, min_z: float, max_z: float) -> Optional[pv.PolyData]:
        # 描画用のダウンサンプリング済みデータからフィルタ
        if self.display_cloud is None:
            return None
        points = self.display_cloud.points
        z = self.display_cloud["z"]
        mask = (z >= min_z) & (z <= max_z)
        filtered_points = points[mask]
        if filtered_points.size == 0:
            return None
        filtered_z = z[mask]
        polydata = pv.PolyData(filtered_points)
        polydata["z"] = filtered_z
        return polydata

    def convert_to_pgm(
        self,
        min_z: float,
        max_z: float,
        resolution: float,
        output_dir: str,
        output_filename: str,
        occupied_thresh: float = 0.65,
        free_thresh: float = 0.2,
        negate: int = 0,
    ) -> Tuple[str, str]:
        # 生データを用いてPGM/YAML変換を実施
        if self.raw_points is None or self.raw_z is None:
            raise ValueError("生の点群データが未初期化です。")
        mask = (self.raw_z >= min_z) & (self.raw_z <= max_z)
        filtered_points = self.raw_points[mask]
        if filtered_points.size == 0:
            raise ValueError("指定されたZ範囲内に生の点群が存在しません。")
        # XY平面への投影と範囲計算
        min_x = float(filtered_points[:, 0].min())
        max_x = float(filtered_points[:, 0].max())
        min_y = float(filtered_points[:, 1].min())
        max_y = float(filtered_points[:, 1].max())
        res_x = int(np.ceil((max_x - min_x) / resolution))
        res_y = int(np.ceil((max_y - min_y) / resolution))

        x_coords = filtered_points[:, 0]
        y_coords = filtered_points[:, 1]
        hist, _, _ = np.histogram2d(
            x_coords, y_coords, bins=[res_x, res_y], range=[[min_x, max_x], [min_y, max_y]]
        )
        accum = np.flipud(hist.T).astype(np.int32)
        image = np.where(accum >= MIN_OCCUPIED_POINTS, 0, 255).astype(np.uint8)

        # PGMファイルの生成
        output_pgm = os.path.join(output_dir, output_filename)
        self._save_pgm(output_pgm, image, res_x, res_y)
        # YAMLファイルの生成
        yaml_name = os.path.splitext(output_pgm)[0] + ".yaml"
        self._save_yaml(yaml_name, os.path.basename(output_pgm), min_x, min_y, resolution, occupied_thresh, free_thresh, negate)
        return output_pgm, yaml_name

    def _save_pgm(self, filename: str, image: np.ndarray, width: int, height: int) -> None:
        with open(filename, "w") as f:
            f.write("P2\n")
            f.write(f"{width} {height}\n")
            f.write("255\n")
            for row in image:
                f.write(" ".join(map(str, row)) + "\n")

    def _save_yaml(
        self,
        filename: str,
        pgm_file: str,
        min_x: float,
        min_y: float,
        resolution: float,
        occupied_thresh: float,
        free_thresh: float,
        negate: int,
    ) -> None:
        with open(filename, "w") as f:
            f.write(f"image: {pgm_file}\n")
            f.write(f"resolution: {resolution}\n")
            f.write(f"origin: [{min_x}, {min_y}, 0.0]\n")
            f.write(f"occupied_thresh: {occupied_thresh}\n")
            f.write(f"free_thresh: {free_thresh}\n")
            f.write(f"negate: {negate}\n")
