#!/usr/bin/env python3
# from logging import getLogger, basicConfig
import sys

import nfc

# logger = getLogger('nfc')
# logger.setLevel(0)
# basicConfig(level=0)


def dump_services(tag, start, n=32) -> list:
    # request_serviceコマンドは複数のServiceCodeを受け取れるので
    # 効率化のためにひとまず32個ずつリクエストしておく
    service_codes = [
        # ServiceCodeは10bit+6bitの2bytes
        # bit演算で必要な分だけ切り出す
        nfc.tag.tt3.ServiceCode(i >> 6, i & 0x3f)
        for i in range(start, start + n)
    ]
    # Request Serviceコマンドで鍵バージョンを取得
    key_versions = tag.request_service(service_codes)
    # サービスの一覧を表示
    raw_services = zip(service_codes, key_versions)
    # 無効なServiceはkey_versionが0xFFFFになるのでそれを除外
    return [service for service, key_version in raw_services if key_version != 0xFFFF]


def on_connect(tag) -> None:
    # 調べたいシステムコードをリストに入れる
    system_code = int(sys.argv[1], 16)

    # tag構造体のシステムコードを上書き
    tag.sys = system_code
    # サービスリストを出力
    for i in range(0, 0x10000, 32):
        services = dump_services(tag, i)
        for service in services:
            print(service)


def main() -> None:
    # USBのNFCリーダーに接続
    with nfc.ContactlessFrontend('usb') as clf:
        options = {
            # FeliCaだけと通信
            'targets': ['212F', '424F'],
            # カードを検知したタイミングでon_connect関数を呼び出す
            'on-connect': on_connect
        }
        # 接続処理の呼び出し
        clf.connect(rdwr=options)


if __name__ == '__main__':
    main()
