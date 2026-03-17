"""纯原生 PPM (P6) 图像解析器，不依赖 PIL/OpenCV"""
import os


class NativeEyeComponent:
    def __init__(self):
        self.status = "ONLINE"
        self.parsing_mode = "strict"  # 故障初始态

    def scan_local_image(self, file_path):
        if not os.path.exists(file_path):
            return None, "ERROR: FILE_NOT_FOUND"

        try:
            with open(file_path, 'rb') as f:
                header = f.readline().decode('ascii').strip()
                if header != 'P6':
                    return None, f"ERROR: INVALID_HEADER_{header}"

                line = f.readline().decode('ascii').strip()
                while line.startswith('#'):
                    line = f.readline().decode('ascii').strip()
                width, height = map(int, line.split())

                maxval = int(f.readline().decode('ascii').strip())

                if self.parsing_mode == "strict" and maxval != 255:
                    raise ValueError(f"Strict mode error: maxval not 255, got {maxval}")

                pixel_data = f.read()

                total_brightness = 0
                sample_step = 3 * 10
                samples = 0
                for i in range(0, len(pixel_data), sample_step):
                    if i + 2 < len(pixel_data):
                        r, g, b = pixel_data[i], pixel_data[i + 1], pixel_data[i + 2]
                        total_brightness += (r + g + b) / 3
                        samples += 1

                avg_brightness = total_brightness / samples if samples > 0 else 0
                semantic = "明亮的画面" if avg_brightness > 128 else "暗淡的画面"

                return (
                    f"已解析 {width}x{height} 本地图像，特征：{semantic} (均值: {int(avg_brightness)})",
                    "SUCCESS"
                )

        except Exception as e:
            return None, f"ERROR: EXCEPTION_DURING_PARSE_{str(e)}"
