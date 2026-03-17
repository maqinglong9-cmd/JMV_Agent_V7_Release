"""
纯 Python Windows 截图工具（零外部依赖）
==========================================
使用 ctypes 调用 Win32 GDI API 截取屏幕，
保存为 PPM P6 格式（与 NativeEyeComponent 兼容）。

非 Windows 系统：返回降级提示，不崩溃。
"""
import os
import struct
import sys
import time

_WORKSPACE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'jmv_workspace'
)


def capture_screen_to_ppm(output_path: str | None = None, scale: float = 0.25) -> tuple[str, str]:
    """
    截取整个屏幕并保存为 PPM 文件。
    scale: 缩放比例（默认 0.25 即 1/4 分辨率，减小文件体积）

    返回 (file_path, status)：
      status = "SUCCESS" 或 "ERROR: ..."
    """
    if sys.platform != "win32":
        return "", "ERROR: 截图功能仅支持 Windows 平台"

    try:
        import ctypes
        import ctypes.wintypes as wt

        # GDI 常量
        SRCCOPY       = 0x00CC0020
        DIB_RGB_COLORS = 0
        BI_RGB         = 0

        gdi32  = ctypes.windll.gdi32
        user32 = ctypes.windll.user32

        # 获取屏幕尺寸
        screen_w = user32.GetSystemMetrics(0)  # SM_CXSCREEN
        screen_h = user32.GetSystemMetrics(1)  # SM_CYSCREEN

        out_w = max(1, int(screen_w * scale))
        out_h = max(1, int(screen_h * scale))

        # 创建设备上下文
        hdc_screen = user32.GetDC(None)
        hdc_mem    = gdi32.CreateCompatibleDC(hdc_screen)
        hbm        = gdi32.CreateCompatibleBitmap(hdc_screen, out_w, out_h)
        gdi32.SelectObject(hdc_mem, hbm)

        # 拉伸复制屏幕到缩放大小
        gdi32.StretchBlt(
            hdc_mem, 0, 0, out_w, out_h,
            hdc_screen, 0, 0, screen_w, screen_h,
            SRCCOPY
        )

        # 读取像素数据（BGR 格式，需转 RGB）
        class BITMAPINFOHEADER(ctypes.Structure):
            _fields_ = [
                ("biSize",          ctypes.c_uint32),
                ("biWidth",         ctypes.c_int32),
                ("biHeight",        ctypes.c_int32),
                ("biPlanes",        ctypes.c_uint16),
                ("biBitCount",      ctypes.c_uint16),
                ("biCompression",   ctypes.c_uint32),
                ("biSizeImage",     ctypes.c_uint32),
                ("biXPelsPerMeter", ctypes.c_int32),
                ("biYPelsPerMeter", ctypes.c_int32),
                ("biClrUsed",       ctypes.c_uint32),
                ("biClrImportant",  ctypes.c_uint32),
            ]

        bmi            = BITMAPINFOHEADER()
        bmi.biSize     = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.biWidth    = out_w
        bmi.biHeight   = -out_h  # 负值 = 自上而下扫描
        bmi.biPlanes   = 1
        bmi.biBitCount = 24  # BGR 24bpp
        bmi.biCompression = BI_RGB

        row_bytes  = ((out_w * 3 + 3) // 4) * 4  # 4字节对齐
        buf_size   = row_bytes * out_h
        buf        = (ctypes.c_byte * buf_size)()

        gdi32.GetDIBits(
            hdc_mem, hbm, 0, out_h,
            buf, ctypes.byref(bmi), DIB_RGB_COLORS
        )

        # 清理 GDI 资源
        gdi32.DeleteObject(hbm)
        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(None, hdc_screen)

        # 写入 PPM P6 格式（RGB）
        if output_path is None:
            os.makedirs(_WORKSPACE, exist_ok=True)
            output_path = os.path.join(_WORKSPACE, f"screenshot_{int(time.time())}.ppm")

        with open(output_path, 'wb') as f:
            f.write(f"P6\n{out_w} {out_h}\n255\n".encode('ascii'))
            raw = bytes(buf)
            for row in range(out_h):
                offset = row * row_bytes
                for col in range(out_w):
                    b = raw[offset + col * 3]
                    g = raw[offset + col * 3 + 1]
                    r = raw[offset + col * 3 + 2]
                    f.write(struct.pack('BBB', r, g, b))

        return output_path, "SUCCESS"

    except Exception as e:
        return "", f"ERROR: 截图失败 {e}"


def capture_and_analyze() -> tuple[str, str]:
    """
    截图并用 NativeEyeComponent 分析，返回 (描述文字, status)。
    description 可直接用作视觉刺激输入。
    """
    ppm_path, status = capture_screen_to_ppm()
    if "ERROR" in status:
        return f"截图失败: {status}", "ERROR"

    try:
        from agent.native_eye_component import NativeEyeComponent
        eye = NativeEyeComponent()
        eye.parsing_mode = "lenient"  # 容忍非标准 maxval
        description, eye_status = eye.scan_local_image(ppm_path)
        if "SUCCESS" in eye_status:
            return f"屏幕截图分析：{description}", "SUCCESS"
        return f"截图分析失败: {eye_status}", "ERROR"
    except Exception as e:
        return f"视觉分析异常: {e}", "ERROR"
