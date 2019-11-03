#!/usr/bin/env python3
import nfc

def on_connect(tag) -> None:
    # カード固有のID
    print(f"IDm: {tag.idm.hex()}")
    print(f"PMm: {tag.pmm.hex()}")
    try:
        # カード内のSystem Codeを全て取得する
        system_codes = tag.request_system_code()
        # 取得したSystem Codeを表示
        for system in system_codes:
            print(f"System Code: {hex(system)}")
    except:
        # System Code取得命令に対応していないカード用
        print(f"System Code: {hex(tag.sys)}")

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

main()
