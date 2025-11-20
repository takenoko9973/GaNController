import os
import sys

from heater_amd_controller.app import create_app


def main() -> None:
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_SCALE_FACTOR"] = "1"

    app = create_app(sys.argv)
    sys.exit(app.run())


if __name__ == "__main__":
    main()
