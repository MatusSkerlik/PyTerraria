from src.application import Application
from src.scenes.default import DefaultScene


def run():
    application = Application()
    application.init()
    application.set_scene(DefaultScene())
    application.loop()
    application.quit()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    run()
