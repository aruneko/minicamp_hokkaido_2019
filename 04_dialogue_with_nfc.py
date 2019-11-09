from libs.type3_tag import Type3Tag, ServiceCode, BlockCode


def main() -> None:
    felica = Type3Tag.connect()
    # ここに処理を書く
    felica.disconnect()


if __name__ == '__main__':
    main()
