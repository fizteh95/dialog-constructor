# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import asyncio

def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


class Test:
    def __init__(self):
        self.queue = []

    async def send(self, a):
        self.queue.append(a)

    async def _send(self):
        while True:
            if not self.queue:
                await asyncio.sleep(0.5)
                continue
            message = self.queue.pop(0)
            await asyncio.sleep(1)
            print(message)
            await asyncio.sleep(2)


async def main():
    t = Test()
    await t.send(2)
    await t.send(33)
    print("sended")
    await asyncio.sleep(10)
    await t.send(11)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    asyncio.run(main())

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
