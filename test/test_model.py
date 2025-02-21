import os
import numpy as np
import open3d as o3d
import pytest
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "pointcloud2pgm_slicer")))
from model import PointCloudModel


@pytest.fixture
def sample_point_cloud():
    # ダミーの点群データを生成する
    pcd = o3d.geometry.PointCloud()
    points = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0],
        [2.0, 2.0, 2.0],
        [3.0, 3.0, 3.0]
    ])
    pcd.points = o3d.utility.Vector3dVector(points)
    return pcd

def test_set_point_cloud_data(sample_point_cloud):
    model = PointCloudModel()
    model.set_point_cloud_data(sample_point_cloud)
    # overall_z_min, overall_z_max が正しく設定されるか
    assert model.overall_z_min == 0.0
    assert model.overall_z_max == 3.0
    # full_cloud に z 値が付与されているか
    assert "z" in model.display_cloud.array_names

def test_get_polydata(sample_point_cloud):
    model = PointCloudModel()
    model.set_point_cloud_data(sample_point_cloud)
    # 1.0～2.0の範囲に該当する点は [1,1,1] と [2,2,2] の2点
    polydata = model.get_polydata(1.0, 2.0)
    assert polydata is not None
    np_points = polydata.points
    assert np_points.shape[0] == 2

def test_convert_to_pgm(tmp_path, sample_point_cloud):
    model = PointCloudModel()
    model.set_point_cloud_data(sample_point_cloud)
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    output_filename = "test_map.pgm"
    pgm_path, yaml_path = model.convert_to_pgm(
        min_z=0.0,
        max_z=3.0,
        resolution=1.0,
        output_dir=str(output_dir),
        output_filename=output_filename,
        occupied_thresh=0.65,
        free_thresh=0.2,
        negate=0
    )
    # ファイルが出力されているか確認
    assert os.path.exists(pgm_path)
    assert os.path.exists(yaml_path)
    # PGMファイルの最初の行が "P2" となっているかチェック
    with open(pgm_path, "r") as f:
        header = f.readline().strip()
    assert header == "P2"
