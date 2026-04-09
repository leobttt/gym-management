from database import inicializar
from power_gym_app.app import App


def main():
    inicializar()
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
