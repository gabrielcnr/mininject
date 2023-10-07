from example.app import ExampleApplication
from example.config import set_env
from example.containers import ExampleContainer

container = None


def initialize_containers():
    global container
    if container is None:
        print('Initializing containers...')
        container = ExampleContainer()
        container.initialize()
        print('Containers initialized.')


def main():
    app = ExampleApplication('my-app')
    app.set_points('player1', 100)
    app.set_points('player2', 500)
    app.set_points('player3', 300)
    print(app.get_winner())


if __name__ == '__main__':
    set_env('development')

    # Initialize containers always on the main entry point of the application, before main()
    initialize_containers()

    main()
