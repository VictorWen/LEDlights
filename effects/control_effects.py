from color_utils import *
from effects.effects import BaseEffect, DYNAMIC, STATIC

class DebugClone(BaseEffect):
    def __init__(self, id, send, effect=None, depth=0):
        super().__init__(STATIC if effect is None else effect.type)
        self.id = id
        self.send = send
        self.depth = depth
        self.effect = effect
    
    def tick(self, pixels, time_delta):
        if self.effect is not None:
            self.effect.tick(pixels, time_delta)
    
    def clone(self):
        self.send(f"{self.id} cloned {self.depth + 1} time(s)")
        effect = None
        if self.effect is not None:
            effect = self.effect.clone()
        return DebugClone(self.id, self.send, effect, self.depth + 1)
        

class ShareEffect(BaseEffect):
    def __init__(self, effect, reclones=0):
        super().__init__(effect.type)
        self.box = [effect] # a pointer to effect
        self.reclones = reclones

    def tick(self, pixels, time_delta):
        self.box[0].tick(pixels, time_delta)
    
    def clone(self):
        reclones = self.reclones
        if reclones != 0:
            self.box[0] = self.box[0].clone()
            reclones -= 1
        copy = ShareEffect(None, reclones)
        copy.box = self.box
        return copy
    
    
class Parent(BaseEffect):
    def __init__(self, effect):
        super().__init__(effect.type)
        self.effect = effect
        self.last_clone = self
        
    def tick(self, pixels, time_delta):
        self.effect.tick(pixels, time_delta)
        
    def clone(self):
        copy = Parent(self.effect.clone())
        self.last_clone = copy
        return copy


class Child(BaseEffect):
    def __init__(self, parent):
        super().__init__(parent.effect.type)
        self.parent = parent
        self.effect = parent.effect.clone()
        
    def tick(self, pixels, time_delta):
        self.effect.tick(pixels, time_delta)
        
    def clone(self):
        return Child(self.parent.last_clone)