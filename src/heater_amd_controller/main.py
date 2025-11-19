import sys

from heater_amd_controller.app import create_app


def main() -> None:
    app = create_app(sys.argv)
    sys.exit(app.run())


if __name__ == "__main__":
    main()
