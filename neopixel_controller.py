import asyncio
from asyncio.tasks import wait
from audioop import add
from pickle import NONE
from effects import STATIC, DYNAMIC, BaseEffect
import datetime
from color_utils import *


def merge_layers(layers, merge_behavior="OVERWRITE"):
    result = [(0, 0, 0) for i in range(len(layers[0]))]
    for i in range(len(layers)):
        layer = layers[i]
        for j in range(len(layer)):
            if layer[j] == (-1, -1, -1):
                continue
            elif merge_behavior == "OVERWRITE":
                result[j] = layer[j]
            elif merge_behavior == "ADD":
                result[j] = add_colors(result[j], layer[j])
            elif merge_behavior == "BLEND":
                result[j] = blend_colors(result[j], layer[j])
    return result


class NeoPixelController:
    def __init__(self, pixels, tps=20):
        self.delay = 1/tps
        self.paused = False
        self.pixels = pixels
        
        self.running = False

        self.N = len(pixels)

        self.layers=[clone_pixels(pixels)]
        self.layer_index = 0

        self.effects = [None]
        self.merge_behavior = "OVERWRITE"

    def set_effect(self, effect: BaseEffect):
        self.effects[self.layer_index] = effect

    def resume(self):
        if (self.effect.type == DYNAMIC):
            self.paused = False

    def pause(self):
        if (self.effect.type == DYNAMIC):
            self.paused = True

    def stop(self):
        self.pixels.deinit()
        self.layers = [[(-1, -1, -1) for i in range(self.N)]]
        self.effects = [None]
        self.running = False
        self.paused = False

    def add_layer(self):
        self.layers.insert(self.layer_index + 1, [(-1, -1, -1) for i in range(self.N)])
        self.effects.insert(self.layer_index + 1, None)
        self.layer_index = self.layer_index + 1

    def num_layers(self):
        return len(self.layers)
    
    def current_layer(self):
        return self.layer_index

    def delete_layer(self):
        self.layers.pop(self.layer_index)
        self.effects.pop(self.layer_index)
        self.layer_index -= 1

        if self.num_layers() == 0:
            self.add_layer()
        if self.layer_index < 0:
            self.layer_index = 0

    def clear_layer(self):
        self.layers[self.layer_index] = [(-1, -1, -1) for i in range(self.N)]
        self.effects[self.layer_index] = None
    
    def reset_layers(self):
        self.layers = [[(-1, -1, -1) for i in range(self.N)]]
        self.effects = [None]
        self.layer_index = 0

    def set_layer(self, layer_index):
        self.layer_index = layer_index
        if self.layer_index >= len(self.layers):
            self.layer_index = len(self.layers) - 1
        elif self.layer_index < 0:
            self.layer_index = 0

    def change_merge_behavior(self, behavior):
        acceptable = ["OVERWRITE", "ADD", "BLEND"]
        if behavior not in acceptable:
            return False
        else:
            self.merge_behavior = behavior
            return True

    async def run(self):
        timer = datetime.datetime.now()
        self.running = True
        while self.running:
            if (self.paused):
                timer = datetime.datetime.now()
                continue
            
            prev_timer = timer
            timer = datetime.datetime.now()
            for i in range(self.num_layers()):
                layer = self.layers[i]
                effect = self.effects[i]
                
                if (effect is None):
                    continue
                
                elif (effect.type == STATIC):
                    effect.tick(layer, 0)
                    self.effects[i] = None
                
                elif (effect.type == DYNAMIC):
                    time_delta = datetime.datetime.now() - prev_timer
                    effect.tick(layer, time_delta.total_seconds())

            colors = merge_layers(self.layers, self.merge_behavior)
            for i in range(self.N):
                self.pixels[i] = colors[i]
            self.pixels.show()

            await asyncio.sleep(self.delay)
           