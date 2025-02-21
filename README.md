# pointcloud2pgm_slicer

## 概要
これは点群データ（.pcdまたは.ply形式）からPGM画像を生成するプログラムです。 \
点群データをユーザが指定する高さ（z軸方向）範囲で抽出し、XY平面に投影して二値化することでPGM画像を生成します。 \
加えて、画像に対応するパラメータ（解像度や原点、閾値など）を記述したYAMLファイルも生成します。

## デモ動画
[![](https://img.youtube.com/vi/gKtSeKtFF_E/0.jpg)](https://www.youtube.com/watch?v=gKtSeKtFF_E&ab_channel=caffeline)

## 依存ライブラリ
- Python 3.x
- [numpy](https://numpy.org/)
- [matplotlib](https://matplotlib.org/)
- [open3d](http://www.open3d.org/)
- [pyvista](https://docs.pyvista.org/)
- [PyQt5](https://pypi.org/project/PyQt5/)
- [pyvistaqt](https://pypi.org/project/pyvistaqt/)

## インストールと実行方法
このツールは、以下の2通りの方法で実行できます。

### 1. パッケージとしてインストールして実行する方法
1. 依存関係のインストール
```bash
pip install -r requirements.txt
```
2. パッケージのインストール
```bash
pip install -e .
```
3. 実行
```bash
python3 -m pointcloud2pgm_slicer.main <input_file.pcd> <output_directory>
```
### 2. 直接実行する方法
1. 依存関係のインストール
```bash
pip install -r requirements.txt
```
2. 実行
```bash
python3 pointcloud2pgm_slicer/main.py <input_file.pcd> <output_directory>
```

## **GUIの操作**
   プログラム起動後、ウィンドウが表示されます。
   - **Min Z / Max Z スライダーおよび数値入力**: 点群データ内のz軸の抽出範囲を設定します。
   - **Reset ボタン**: z軸の設定を全範囲にリセットします。
   - **Set Output File Name ボタン**: 出力PGMファイルのファイル名を変更します。
   - **Set Resolution ボタン**: 1ピクセルあたりの実空間距離（m/px）を設定します。
   - **Convert to PGM ボタン**: 現在の設定に基づき、点群データをPGM画像およびYAMLファイルに変換して出力します。

## 設定の変更
- **設定ファイル:** [pointcloud2pgm_slicer/config.py](pointcloud2pgm_slicer/config.py)

- VOXEL_SIZE
  - 描画用の点群のダウンサンプリングに使用するボクセルサイズ

- MIN_OCCUPIED_POINTS
  - PGM画像生成時に各ピクセル内の点群数を基準に占有判定を行うための閾値
  - 各ピクセルに含まれる点の数が MIN_OCCUPIED_POINTS 以上であれば、そのピクセルは占有と判定
    - 未満の場合は未占有

## ライセンス
[Apache License 2.0](LICENSE)
