import asyncio
from asyncio.tasks import wait
from effects import STATIC, DYNAMIC, BaseEffect
import datetime

class NeoPixelController:
    
    def __init__(self, pixels, tps=20):
        self.delay = 1/tps
        self.wait_event = asyncio.Event()
        self.effect = None
        self.pixels = pixels
        self.running = False

    def set_effect(self, effect: BaseEffect):
        self.effect = effect
        if (not self.wait_event.is_set()):
            self.wait_event.set()

    def resume(self):
        if (self.effect.type == DYNAMIC):
            self.wait_event.set()

    def pause(self):
        if (self.effect.type == DYNAMIC):
            self.wait_event.clear()

    def stop(self):
        self.pixels.deinit()
        self.effect = None
        self.running = False
        self.wait_event.set()

    async def run(self):
        timer = datetime.datetime.now()
        self.running = True
        while self.running:
            if (not self.wait_event.is_set()):
                await self.wait_event.wait()
                timer = datetime.datetime.now()

            if (self.effect is None):
                return
            
            elif (self.effect.type == STATIC):
                self.effect.tick(self.pixels, 0)
                await self.wait_event.wait()
                self.wait_event.clear()
            
            elif (self.effect.type == DYNAMIC):
                time_delta = datetime.datetime.now() - timer
                timer = datetime.datetime.now()
                self.effect.tick(self.pixels, time_delta.total_seconds())
                await asyncio.sleep(self.delay)