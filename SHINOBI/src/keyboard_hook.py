import ctypes
import platform
import logging

logger = logging.getLogger("SHINOBI.Keyboard")

class KeyboardHook:
    """
    低レベルキーボードフック (WH_KEYBOARD_LL) を使用して
    Alt+Tab, Alt+F4 などをブロックする。
    """
    WH_KEYBOARD_LL = 13
    WM_KEYDOWN = 0x0100
    VK_TAB = 0x09
    VK_MENU = 0x12 # ALT
    VK_F4 = 0x73
    VK_LWIN = 0x5B
    VK_RWIN = 0x5C
    VK_ESCAPE = 0x1B

    def __init__(self):
        self.hook_id = None
        self.user32 = None
        if platform.system() == "Windows":
            self.user32 = ctypes.windll.user32
            self.kernel32 = ctypes.windll.kernel32

    def start(self):
        if platform.system() != "Windows":
            logger.info("[MOCK] Keyboard hook STARTED.")
            return

        def hook_proc(nCode, wParam, lParam):
            if nCode >= 0:
                # lParam は KBDLLHOOKSTRUCT へのポインタ
                vk_code = ctypes.cast(lParam, ctypes.POINTER(ctypes.c_ulong))[0]

                # ブロック対象の判定
                # Alt + Tab, Alt + F4, Win key
                is_alt = (self.user32.GetAsyncKeyState(self.VK_MENU) & 0x8000) != 0
                if (vk_code == self.VK_TAB and is_alt) or \
                   (vk_code == self.VK_F4 and is_alt) or \
                   (vk_code in [self.VK_LWIN, self.VK_RWIN]):
                    logger.info(f"Blocked key: {vk_code}")
                    return 1 # 1を返すとメッセージが破棄される

            return self.user32.CallNextHookEx(self.hook_id, nCode, wParam, lParam)

        # フックの登録
        HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int)
        self.callback = HOOKPROC(hook_proc)

        self.hook_id = self.user32.SetWindowsHookExA(
            self.WH_KEYBOARD_LL, self.callback,
            self.kernel32.GetModuleHandleW(None), 0
        )
        if not self.hook_id:
            logger.error("Failed to set keyboard hook.")
        else:
            logger.info("Keyboard hook successfully set.")

    def stop(self):
        if platform.system() != "Windows":
            logger.info("[MOCK] Keyboard hook STOPPED.")
            return

        if self.hook_id:
            self.user32.UnhookWindowsHookEx(self.hook_id)
            self.hook_id = None
            logger.info("Keyboard hook removed.")
