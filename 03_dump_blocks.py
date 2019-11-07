# from logging import getLogger, basicConfig
import sys

import nfc

# logger = getLogger('nfc')
# logger.setLevel(0)
# basicConfig(level=0)


def on_connect(tag):
    # 第一引数はSystemCode
    system_code = int(sys.argv[1], 16)
    # 第二引数以降はServiceCode
    service_codes = [int(n, 16) for n in sys.argv[2:]]
    dump_times = 32

    # 調べたいシステムコードでデフォルトのシステムコードを上書き
    tag.sys = system_code

    for c in service_codes:
        print(f"Service Code: 0x{c:04x}")
        sc = nfc.tag.tt3.ServiceCode(c >> 6, c & 0x3f)

        for i in range(dump_times):
            bc = nfc.tag.tt3.BlockCode(i, service=0)
            try:
                data = tag.read_without_encryption([sc], [bc])
                print(data.hex())
            except Exception as e:
                # エラーは握りつぶす
                pass
        print("")


def main() -> None:
    # USBのNFCリーダーに接続
    with nfc.ContactlessFrontend('usb') as clf:
        options = {
            # FeliCaだけと通信
            'targets': ['212F'],
            # カードを検知したタイミングでon_connect関数を呼び出す
            'on-connect': on_connect
        }
        # 接続処理の呼び出し
        clf.connect(rdwr=options)


if __name__ == '__main__':
    main()
