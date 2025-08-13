from hikkatl.types import Message  # Importing the Message type from hikkatl.types
from .. import loader, utils  # Importing loader and utils from the parent module

@loader.tds
class CounterModule(loader.Module):
    """A module that counts from a given number to another, sending each number as a separate message."""
    
    strings = {
        "name": "CounterModule",
        "counting": "Counting from {} to {}...",
        "done": "Counting completed!",
        "invalid_range": "Invalid range! The start number must be less than or equal to the end number.",
        "invalid_input": "Please provide two valid integers: .count <start> <end>."
    }

    @loader.command(
        ru_doc="Считать от первого числа до второго",
        es_doc="Contar desde el primer número hasta el segundo",
        de_doc="Zählen Sie von der ersten Zahl bis zur zweiten"
    )
    async def count(self, message: Message):
        """Count from the first number to the second number."""
        # Split the message to get the numbers
        args = message.text.split()
        
        # Check if we have exactly 3 arguments (command + two numbers)
        if len(args) != 3:
            await utils.answer(message, self.strings["invalid_input"])  # Notify user of invalid input
            return
        
        try:
            start = int(args[1])  # Convert the first argument to an integer
            end = int(args[2])    # Convert the second argument to an integer
        except ValueError:
            await utils.answer(message, self.strings["invalid_input"])  # Notify user of invalid input
            return
        
        # Check if the start number is less than or equal to the end number
        if start > end:
            await utils.answer(message, self.strings["invalid_range"])  # Notify user of invalid range
            return
        
        await utils.answer(message, self.strings["counting"].format(start, end))  # Notify the user that counting has started
        
        # Loop through the range and send each number as a separate message
        for number in range(start, end + 1):
            await utils.answer(message, str(number))  # Send the current number as a message
        
        await utils.answer(message, self.strings["done"])  # Notify the user that counting is completed