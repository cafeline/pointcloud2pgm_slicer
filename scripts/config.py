VOXEL_SIZE: float = 0.2       # 点群のダウンサンプリングに使用するボクセルサイズ[m] (描画の軽量化のみに使用し、pgmには影響しない)
MIN_OCCUPIED_POINTS: int = 1      # 各ピクセルの点数がこの値以上なら占有と判断