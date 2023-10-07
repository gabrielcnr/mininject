from example.component import Database
from example.containers import ExampleContainer
from mininject import inject


class ExampleApplication:

    @inject(
        db=ExampleContainer.cache,
    )
    def __init__(self, name: str, db: Database):
        self.name = name
        self.db = db

    def set_points(self, player: str, points: int) -> None:
        self.db.set(player, points)

    def get_winner(self):
        all_players_points = self.db.get_all()
        return max(all_players_points.items(), key=lambda x: x[1])
