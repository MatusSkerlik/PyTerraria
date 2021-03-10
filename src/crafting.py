from abc import ABC, abstractmethod
from typing import List, Dict

from src.tables import Tiles, Items


class Recipe(ABC):

    @abstractmethod
    def get_ingredients(self) -> Dict[int, int]:
        """ :return dictionary of item_type: amount pairs """
        pass

    @abstractmethod
    def get_type(self) -> int:
        """ :return new item type """

class GoldOreRecipe(Recipe):

    def get_type(self) -> int:
        return Tiles.GOLD

    def get_ingredients(self) -> Dict[int, int]:
        return {
            Tiles.COPPER: 20
        }

class DirtWallRecipe(Recipe):

    def get_type(self) -> int:
        return Tiles.B_DIRT

    def get_ingredients(self) -> Dict[int, int]:
        return {
            Tiles.DIRT: 1
        }


class CraftingStation:

    def __init__(self, recipes: List[Recipe]) -> None:
        self.recipes = set(recipes)

    def available_for(self, inventory) -> List[Recipe]:
        """ :return list of recipes which are available for crafting """
        contents = {}
        for i, slot in inventory:
            if contents.get(slot.type):
                contents[slot.type] += slot.amount
            else:
                contents[slot.type] = slot.amount

        recipes = []
        for recipe in self.recipes:
            ingredients = recipe.get_ingredients()
            creatable = True
            for item_type, amount in ingredients.items():
                i_amount = contents.get(item_type)
                if i_amount and i_amount >= amount:
                    continue
                else:
                    creatable = False
                    break
            if creatable:
                recipes.append(recipe)
        return recipes


class DefaultCraftingStation(CraftingStation):

    def __init__(self) -> None:
        recipes = [
            GoldOreRecipe(),
            DirtWallRecipe(),
        ]
        super().__init__(recipes)

    def extend(self, station: CraftingStation):
        """ Extend this station recipes by recipes of station passed """
        for recipe in station.recipes:
            self.recipes.add(recipe)

    def reduce(self, station: CraftingStation):
        """ Reduce this station recipes by recipes of station passed """
        for recipe in station.recipes:
            self.recipes.remove(recipe)
