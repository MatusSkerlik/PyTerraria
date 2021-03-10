from src.crafting import DefaultCraftingStation


class Inventory:
    class Slot:
        def __init__(self, max_amount: int) -> None:
            self.type = None
            self.amount = 0
            self.max = max_amount

        def is_empty(self):
            return self.amount == 0 or self.type is None

        def accept(self, item_type: int):
            """ :return true if this slot accepts item type """
            return self.type == item_type

        def set_type(self, item_type: int):
            """ Will change type of underlying item type """
            self.type = item_type

        def clear(self):
            """ Will reset internal item counter """
            self.amount = 0
            self.type = None

        def add(self, amount: int):
            """ :return how much was added from amount"""
            if self.amount < self.max:
                self.amount += amount
                if self.amount > self.max:
                    exceed = self.amount - self.max
                    self.amount = self.max
                    return amount - exceed
                else:
                    return amount
            else:
                return 0

        def remove(self, amount: int):
            """ :return how much was removed """
            if amount <= self.amount:
                self.amount -= amount
                if self.amount == 0:
                    self.clear()
                return amount
            else:
                exceed = amount - self.amount
                self.clear()
                return exceed

    def __init__(self, capacity: int, stack_size: int) -> None:
        self.capacity = capacity
        self.stack_size = stack_size
        self.index = 0
        self.temp = Inventory.Slot(stack_size)
        self.slots = [Inventory.Slot(stack_size) for i in range(capacity)]
        self.crafting_station = DefaultCraftingStation()
        self.crafting = False

    def __iter__(self):
        if not self.crafting:
            if self.capacity >= 10:
                return zip(range(10), self.slots[0:10])
        return zip(range(len(self.slots)), self.slots)

    def get_recipes(self):
        return self.crafting_station.available_for(self)

    def get_free(self):
        """ :return first free slot or None if there is no empty slot """
        for slot in self.slots:
            if slot.is_empty():
                return slot
        return None

    def shift_left(self):
        self.index -= 1
        if self.index < 0:
            self.index = 0

    def shift_right(self):
        self.index += 1
        if self.capacity < 10:
            if self.index >= self.capacity:
                self.index = self.capacity - 1
        else:
            if self.index >= 10:
                self.index = 9

    def set_active(self, index: int):
        self.index = index

    def pop(self):
        """
        pops one item from active slot
        :return item category
        """

        slot = self.slots[self.index]
        if not slot.is_empty():
            t = slot.type
            slot.remove(1)
            return t
        else:
            return None

    def add(self, item_type: int, amount: int):
        """
        Will add item quantity to first slot
        with same type (if available) or
        initialize first empty to this item type

        Will raise AttributeError if there is no free space in process
        """

        for slot in self.slots:
            if slot.accept(item_type):
                added = slot.add(amount)
                if added == amount:
                    return
                else:
                    amount -= added

        while amount != 0:
            slot = self.get_free()
            if slot:
                slot.set_type(item_type)
                added = slot.add(amount)
                if added == amount:
                    break
            else:
                raise AttributeError("No space available.")

    def remove(self, slot_index: int, amount: int):
        """ :return how much was removed from slot """
        slot = self.slots[slot_index]
        return slot.remove(amount)

    def consume(self, item_type: int, amount: int):

        slots = []
        count = 0
        consumable = False
        for slot in self.slots:
            if slot.accept(item_type):
                slots.append(slot)
                count += slot.amount

            if count >= amount:
                consumable = True
                break

        if consumable:
            removed = 0
            for slot in slots:
                removed += slot.remove(amount)
                if removed == amount:
                    return True
        else:
            return False




