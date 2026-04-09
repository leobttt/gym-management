from database import inicializar, limpiar_recibos_antiguos
from power_gym_app.app import App


def main():
    inicializar()
    limpiar_recibos_antiguos()
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
