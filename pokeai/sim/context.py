from pokeai.sim.poke_db import PokeDB

initialized = False
db = None  # type: PokeDB


def init():
    global initialized
    global db
    if not initialized:
        db = PokeDB()
